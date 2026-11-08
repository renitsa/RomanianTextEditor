"""
Parameter validation logic.
Handles both syntax validation (during collection) and runtime validation (before processing).
"""

from difflib import get_close_matches
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Tuple

from src.app.parameter_collection.param_models import ValidationResult
from src.app.processor_factory import ProcessorFactory
from src.config.app_config import get_app_config
from src.text_processor.chunker import VALID_CHUNKER_NAMES
from src.utils.app_logger import get_logger

if TYPE_CHECKING:
    from src.utils.app_logger import AppLogger
    from src.config.app_config import AppConfig
    from src.app.parameter_collection.param_models import ProcessingParameters


class ParameterValidator:
    """
    Validates parameters at different stages.
    
    Validation Levels:
    1. Syntax validation (during collection) - basic format checks
    2. Runtime validation (before processing) - service/resource availability
    """

    def __init__(self, logger: Optional["AppLogger"] = None, config: Optional["AppConfig"] = None):
        """Initialize validator with optional logger and config (both default to the app ones)."""
        self.logger = logger if logger is not None else get_logger("RomanianTextEditor.App")
        self.config = config if config is not None else get_app_config()
    
    def validate_syntax(self, params: "ProcessingParameters") -> ValidationResult:
        """
        Validate parameter syntax and format.
        
        This is called during parameter collection to catch obvious errors early.
        Does NOT check runtime availability (services, files, etc.).
        """
        result = ValidationResult(is_valid=True)
        
        # Validate task
        if params.task:
            if not ProcessorFactory.is_valid_task(params.task):
                valid_tasks = ', '.join(ProcessorFactory.get_available_tasks())
                result.add_error(
                    f"Invalid task: '{params.task}'\n"
                    f"   Valid options: {valid_tasks}\n"
                    f"   Tip: Run without arguments for interactive mode"
                )
        
        # Validate input exclusivity
        if params.input_path and params.input_text:
            result.add_error("Cannot specify both input file and input text")
        
        # Validate chunker names (empty list means "no chunking")
        unknown_chunkers = [name for name in (params.chunkers or []) if name not in VALID_CHUNKER_NAMES]
        if unknown_chunkers:
            result.add_error(
                f"Unknown chunker(s): {', '.join(unknown_chunkers)}\n"
                f"   Valid options: {', '.join(sorted(VALID_CHUNKER_NAMES))}, or 'none' to disable chunking"
            )
        
        if not result.is_valid:
            self.logger.warning(f"Validator: Syntax validation failed: {len(result.errors)} errors")
        
        return result
    
    def validate_runtime(self, params: "ProcessingParameters") -> ValidationResult:
        """
        Validate runtime requirements before processing.
        
        This checks that services are running and resources exist.
        Called just before processing begins (fast-fail).
        """
        result = ValidationResult(is_valid=True)
        
        self.logger.debug("Validator: Starting runtime validation (pre-processing)")
        
        # 1. FIRST: Validate Ollama service (fastest check)
        ollama_available, ollama_error = self._check_ollama_service()
        if not ollama_available and ollama_error:
            result.add_error(ollama_error)
            # Fast-fail: no point checking model if service isn't running
            return result
        
        # 2. Validate model availability (fast)
        if params.model_name:
            model_available, model_error = self._check_model_exists(params.model_name)
            if not model_available and model_error:
                result.add_error(model_error)
        
        # 3. Validate input file existence (if file path provided)
        if params.input_path:
            file_exists, file_error = self._check_input_file(params.input_path)
            if not file_exists and file_error:
                result.add_error(file_error)
        
        # 4. Validate output path is writable (if file output)
        if params.output_path:
            writable, write_error = self._check_output_writable(params.output_path)
            if not writable and write_error:
                result.add_warning(write_error)
        
        if result.is_valid:
            self.logger.debug("Validator: Runtime validation passed")
        else:
            self.logger.error(f"Validator: Runtime validation failed: {len(result.errors)} errors")
        
        return result
    
    def _check_ollama_service(self) -> Tuple[bool, Optional[str]]:
        """Check if Ollama service is running."""
        try:
            from src.services import get_ollama_service
            service = get_ollama_service()
            
            if service.is_ollama_running():
                self.logger.debug("✓ Ollama runtime validation passed")
                return True, None
            else:
                error = (
                    "CRITICAL: Ollama service is not running.\n"
                    "   All text processing tasks require Ollama.\n"
                    "   Please start Ollama and try again:\n"
                    "   - Windows: Start 'Ollama' application\n"
                    "   - Linux/Mac: Run 'ollama serve' in terminal"
                )
                return False, error
        except Exception as e:
            error = f"Failed to check Ollama service: {e}"
            self.logger.error(f"Validator: {error}")
            return False, error
    
    def _check_model_exists(self, model_name: str) -> Tuple[bool, Optional[str]]:
        """"Check if specified model is available."""
        try:
            from src.services import get_ollama_service
            service = get_ollama_service()
            
            available_models = service.get_model_names()
            
            if model_name in available_models:
                self.logger.debug(f"Validator: ✓ Model '{model_name}' is available")
                return True, None
            else:
                # Provide helpful error with available models
                models_list = ', '.join(available_models[:5])
                if len(available_models) > 5:
                    models_list += f" (and {len(available_models) - 5} more)"
                
                error = (
                    f"Model '{model_name}' not found.\n"
                    f"   Available models: {models_list}\n"
                    f"   Download with: ollama pull {model_name}\n"
                    f"   Or run: ollama list (to see all installed models)"
                )
                return False, error
        except Exception as e:
            error = f"Failed to check model availability: {e}"
            self.logger.error(f"Validator: {error}")
            return False, error
    
    def _check_input_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """"Check if input file exists, is readable and has a readable format."""
        try:
            path = Path(file_path)
            if not path.exists():
                error = f"Input file not found: '{file_path}'"
                return False, error
            
            if not path.is_file():
                error = f"Input path is not a file: '{file_path}'"
                return False, error
            
            if path.suffix.lower() in self.config.file_config.SUPPORTED_DOCUMENT_EXTENSIONS:
                error = (
                    f"Cannot read '{path.name}': '{path.suffix}' files are not supported yet.\n"
                    f"   Readers for these formats need extra libraries, which this project avoids.\n"
                    f"   Convert the file to {', '.join(self.config.file_config.SUPPORTED_TEXT_EXTENSIONS)}"
                )
                return False, error
            
            # Reading a small sample checks permissions and the configured encoding
            # without loading the whole file
            encoding = self.config.file_config.DEFAULT_ENCODING
            try:
                with path.open('r', encoding=encoding) as f:
                    f.read(1024)
                self.logger.debug(f"Validator: ✓ Input file accessible: {file_path}")
                return True, None
            except PermissionError:
                error = f"No permission to read file: '{file_path}'"
                return False, error
            except UnicodeDecodeError:
                error = (
                    f"Cannot read '{path.name}' as {encoding} text.\n"
                    f"   Save the file with {encoding} encoding (or change DEFAULT_ENCODING in file_config.json)"
                )
                return False, error
        except Exception as e:
            error = f"Error checking input file: {e}"
            return False, error
    
    def _check_output_writable(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """"Check if output path is writable."""
        try:
            path = Path(file_path)
            
            # Check parent directory exists and is writable
            parent = path.parent
            if not parent.exists():
                # Try to create it
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                    self.logger.debug(f"Validator: Created output directory: {parent}")
                except Exception as e:
                    error = f"Cannot create output directory: {e}"
                    return False, error
            
            self.logger.debug(f"Validator: ✓ Output path is writable: {file_path}")
            return True, None
        except Exception as e:
            warning = f"Warning: Could not verify output path writability: {e}"
            return False, warning
    
    @staticmethod
    def suggest_fix(param_name: str, invalid_value: str) -> str:
        """Suggest a fix for an invalid parameter."""
        if param_name == "task":
            # Find close matches using difflib
            matches = get_close_matches(
                invalid_value, 
                ProcessorFactory.get_available_tasks(), 
                n=1, 
                cutoff=0.6
            )
            if matches:
                return f"Did you mean '{matches[0]}'?"
        return ""