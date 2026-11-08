"""
Parameter collection orchestrator.
Coordinates multiple collectors with fallback logic.
"""

from typing import Optional, TYPE_CHECKING
import sys

if TYPE_CHECKING:
    from src.utils.app_logger import AppLogger
    from src.app.path_manager import PathManager
    from src.app.parameter_collection.param_models import ProcessingParameters, ValidationResult

from src.app.parameter_collection.param_models import ProcessingParameters
from src.app.parameter_collection.param_validator import ParameterValidator
from src.app.parameter_collection.cli_collector import CLIParameterCollector
from src.app.parameter_collection.interactive_collector import InteractiveParameterCollector
from src.utils.app_logger import get_logger


class ParameterCollectionOrchestrator:
    """
    Orchestrates parameter collection from multiple sources with fallback logic.
    
    Flow:
    1. Try CLI collector first (if it has any args)
    2. For any missing parameters, fall back to interactive collector
    3. Validate parameter format after collection (task name is correct, etc.)
    4. Return complete, validated parameters
    """
    
    def __init__(self, path_manager: "PathManager", logger: Optional["AppLogger"] = None):
        """
        Initialize orchestrator.
        
        Args:
            path_manager: PathManager for file operations
            logger: Optional logger for debugging
        """
        self.path_manager = path_manager
        self.logger = logger if logger is not None else get_logger("RomanianTextEditor.App")
        self.validator = ParameterValidator(logger=self.logger)
        
        # Initialize collectors
        self.cli_collector = CLIParameterCollector(path_manager=path_manager, logger=self.logger)
        self.interactive_collector = InteractiveParameterCollector(path_manager=path_manager, logger=self.logger)
        
        self.logger.debug("Orchestrator: Initialized")
    
    def collect_parameters(self) -> "ProcessingParameters":
        """
        Collect complete set of parameters using fallback strategy.
        
        Returns:
            ProcessingParameters: Complete, syntax-validated parameters
            
        Raises:
            SystemExit: If non-interactive parameters are incomplete or syntax validation fails.
            UserCancelled: If the user exits or interrupts interactive parameter collection.
        """
        self.logger.debug("Orchestrator: Starting parameter collection")
        
        params = ProcessingParameters()
        
        # Check if --non-interactive flag was specified
        non_interactive = self.cli_collector.is_non_interactive()
        
        if non_interactive:
            # Non-interactive mode - no user prompts, fail if incomplete
            self.logger.debug("Orchestrator: --non-interactive specified - no user prompts allowed")
            params = self.cli_collector.collect_all()
            
            # Check completeness immediately
            if not params.is_complete():
                missing = params.get_missing_required()
                error_msg = (
                    f"ERROR: Required parameters missing: {', '.join(missing)}\n"
                    f"--non-interactive mode requires all parameters to be specified.\n"
                    f"Either provide all required parameters or remove --non-interactive flag for interactive prompts."
                )
                print(f"\n{error_msg}")
                self.logger.error(f"Orchestrator: {error_msg}")
                sys.exit(1)
        else:
            # Default mode: parameter-by-parameter fallback
            self.logger.debug("Orchestrator: Using parameter collection with interactive fallback")
            params = self._collect_with_fallback()
        
        # Validate parameter format
        validation_result = self.validator.validate_syntax(params)
        if not validation_result.is_valid:
            self._handle_validation_errors(validation_result, from_cli=non_interactive)
        
        # Log collected parameters
        self.logger.debug("Orchestrator: Parameter collection complete")
        self.logger.debug(f"Orchestrator: Collected parameters: {params.to_dict()}")
        
        return params
    
    def _collect_with_fallback(self) -> "ProcessingParameters":
        """
        Collect parameters with parameter-by-parameter fallback.
        
        Strategy:
        - Pure interactive mode (no processing args): Prompt for all parameters
        - CLI mode with fallback: Ask only for missing required params, use defaults for optional ones
        
        Note: Utility args (like --verbose) don't affect the interaction mode.
        """
        params = ProcessingParameters()
        
        # Determine if we're in pure interactive mode (no processing-related CLI args)
        is_pure_interactive = not self.cli_collector.has_processing_args()
        
        self.logger.debug(f"Orchestrator: Pure interactive mode: {is_pure_interactive}")
        
        # Task (required)
        params.task = self.cli_collector.collect_task()
        if params.task is None:
            self.logger.debug("Task not specified in CLI - switching to interactive mode")
            params.task = self.interactive_collector.collect_task()
            params.mark_source('task', 'interactive (fallback)')
        else:
            params.mark_source('task', 'cli')
        
        # Model (required)
        params.model_name = self.cli_collector.collect_model_name()
        if params.model_name is None:
            self.logger.debug("Model not specified in CLI - switching to interactive mode")
            params.model_name = self.interactive_collector.collect_model_name()
            params.mark_source('model_name', 'interactive (fallback)')
        else:
            params.mark_source('model_name', 'cli')
        
        # Input
        params.input_path, params.input_text = self.cli_collector.collect_input()
        if params.input_path is None and params.input_text is None:
            self.logger.debug("Input not specified in CLI - switching to interactive mode")
            params.input_path, params.input_text = self.interactive_collector.collect_input()
            params.mark_source('input', 'interactive (fallback)')
        else:
            params.mark_source('input', 'cli')
        
        # Output (non-essential) - only prompt in pure interactive mode
        # Pass the appropriate identifier based on input type
        if params.input_text:
            input_identifier = "cli_text"
        elif params.input_path:
            input_identifier = params.input_path
        else:
            input_identifier = "text_input"
        
        task = params.task or "unknown"
        
        if is_pure_interactive:
            # Pure interactive mode - ask for output preference
            params.output_path = self.interactive_collector.collect_output(input_identifier, task)
            params.mark_source('output_path', 'interactive')
        else:
            # CLI mode - use CLI value or auto-generated default
            params.output_path = self.cli_collector.collect_output(input_identifier, task)
            params.mark_source('output_path', 'cli or auto-generated')
        
        # Verbose (non-essential) - respect CLI value if set, otherwise prompt in pure interactive
        if is_pure_interactive:
            # Check if verbose was explicitly set via CLI (utility arg)
            cli_verbose = self.cli_collector.collect_verbose()
            if cli_verbose:
                # User explicitly set --verbose, respect it
                params.verbose = cli_verbose
                params.mark_source('verbose', 'cli (utility arg)')
            else:
                # Not set via CLI, prompt interactively
                params.verbose = self.interactive_collector.collect_verbose()
                params.mark_source('verbose', 'interactive')
        else:
            # CLI mode - use CLI value or default (False)
            params.verbose = self.cli_collector.collect_verbose()
            if not params.verbose:
                params.mark_source('verbose', 'cli (default: False)')
            else:
                params.mark_source('verbose', 'cli')
        
        # Chunkers (non-essential, CLI-only - interactive always returns None)
        params.chunkers = self.cli_collector.collect_chunkers()
        if params.chunkers is not None:
            params.mark_source('chunkers', 'cli')
        
        return params
    
    def _handle_validation_errors(self, validation_result: "ValidationResult", from_cli: bool) -> None:
        """
        Handle validation errors with helpful messages.
        
        Args:
            validation_result: Validation result with errors
            from_cli: Whether errors came from CLI mode
        """
        print("\n" + "="*60)
        print("❌ PARAMETER VALIDATION FAILED")
        print("="*60)
        print(validation_result.get_error_message())
        
        if from_cli:
            print("\n💡 Tip: Run without arguments for interactive mode:")
            print("   python run.py")
        
        print("="*60)
        
        self.logger.error(f"Orchestrator: Parameter validation failed: {len(validation_result.errors)} errors")
        for error in validation_result.errors:
            self.logger.error(f"Orchestrator:   - {error}")
        
        sys.exit(1)
    
    def validate_runtime(self, params: "ProcessingParameters") -> "ValidationResult":
        """
        Validate runtime requirements (services, files, etc.).
        
        This should be called just before processing begins.
        
        Args:
            params: Parameters to validate
            
        Returns:
            ValidationResult: Validation result with any errors
        """
        self.logger.debug("Orchestrator: Starting runtime validation")
        
        return self.validator.validate_runtime(params)
    
    def handle_runtime_validation_errors(self, validation_result: "ValidationResult") -> None:
        """
        Handle runtime validation errors.
        
        Args:
            validation_result: Validation result with errors
        """
        print("\n" + "="*60)
        print("❌ RUNTIME VALIDATION FAILED")
        print("="*60)
        print(validation_result.get_error_message())
        
        if validation_result.warnings:
            print("\n⚠️  Warnings:")
            for warning in validation_result.warnings:
                print(f"   {warning}")
        
        print("="*60)
        
        self.logger.error(f"Runtime validation failed: {len(validation_result.errors)} errors")
        for error in validation_result.errors:
            self.logger.error(f"  - {error}")
        
        sys.exit(1)
