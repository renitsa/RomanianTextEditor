"""
Text Processing Application - Main orchestrator

Coordinates all components to process text through various tasks.
"""

import sys
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Tuple

if TYPE_CHECKING:
    from src.config.app_config import AppConfig
    from src.utils.app_logger import AppLogger

from src.text_processor import TextChunker, ProcessingWorkflow, TextProcessor
from src.text_processor.text_io import TextReader, TextWriter
from src.text_processor.chunker import get_chunker_strategy
from src.config.app_config import get_app_config
from src.utils.app_logger import get_logger
from src.utils.dict_utils import DotDict
from src.app.exceptions import UserCancelled
from src.app.path_manager import PathManager
from src.app.processor_factory import ProcessorFactory
from src.app.parameter_collection.param_orchestrator import ParameterCollectionOrchestrator


class TextProcessingApplication:
    """Main application class that orchestrates text processing."""
    
    def __init__(self, app_config: Optional["AppConfig"] = None,
                logger: Optional["AppLogger"] = None):
        """Initialize the application with config and logger.
        
        Args:
            app_config: Optional AppConfig instance. If not provided, will get singleton.
            logger: Optional AppLogger instance. If not provided, will create one.
        """
        # Use dependency injection or get default config and logger
        self.config = app_config if app_config is not None else get_app_config()
        self.logger = logger if logger is not None else get_logger("RomanianTextEditor.App")
    
        # Initialize components with dependencies
        self.path_manager = PathManager(app_config=self.config, logger=self.logger)

        self._validate_processor_factory()
        
        # Parameter collection orchestrator (interface-based parameter collection)
        self.param_orchestrator = ParameterCollectionOrchestrator(
            path_manager=self.path_manager,
            logger=self.logger
        )
        
        self.logger.debug("TextProcessingApplication initialized")
    
    def _validate_processor_factory(self) -> None:
        """Validate ProcessorFactory configuration consistency.
        
        Checks that all registered tasks have corresponding config entries
        and that all config entries have registered processors.
        
        Raises:
            RuntimeError: If critical validation errors are found
        """
        errors, warnings = ProcessorFactory.validate_config(self.config.actions_config)
        
        if errors:
            self.logger.error("ProcessorFactory configuration validation failed:")
            for error in errors:
                self.logger.error(f"  - {error}")
                print(f"ERROR: {error}", file=sys.stderr)
            raise RuntimeError("ProcessorFactory configuration validation failed - see errors above")
        
        if warnings:
            self.logger.warning("ProcessorFactory configuration validation warnings:")
            for warning in warnings:
                self.logger.warning(f"  - {warning}")
    
    def _create_chunker_for_task(self, task_config: Any, task_name: str, 
                                 language: str, 
                                 chunkers: Optional[List[str]] = None) -> Optional[TextChunker]:
        """Create chunker configured for specific task based on config or CLI.
        
        Args:
            task_config: The task configuration object (must have CHUNKERS and INPUT_LANGUAGE fields)
            task_name: The task name (for error messages)
            language: Language code for the chunker (from task config)
            chunkers: Optional CLI chunkers. If provided, overrides config.
                     None = use config defaults
                     [] = no chunking (explicit)
                     ['strategy'] = use these strategies
            
        Returns:
            Configured TextChunker instance with strategies, or None if no chunking requested
            
        Raises:
            RuntimeError: If CHUNKERS field is missing from config
        """
        if not hasattr(task_config, 'CHUNKERS'):
            raise RuntimeError(f"Task '{task_name}' config missing CHUNKERS field")
        
        # Determine which chunkers to use:
        # - If CLI provided chunkers, use those (could be [] for no chunking)
        # - Otherwise, use config defaults

        if chunkers is not None:
            selected_chunkers = chunkers
            self.logger.debug(f"Using CLI-specified chunkers: {selected_chunkers}")
        else:
            selected_chunkers = task_config.CHUNKERS
            self.logger.debug(f"Using config chunkers for task '{task_name}': {selected_chunkers}")
        
        # Empty list means no chunking
        if not selected_chunkers:
            self.logger.info(f"No chunking configured for task '{task_name}' - processing as single text")
            return None
        
        # Create chunker with specified strategies
        chunker = TextChunker(language=language)
        for chunker_name in selected_chunkers:
            # All strategies now accept language parameter (uniform interface)
            strategy = get_chunker_strategy(chunker_name, language=language)
            chunker.add_strategy(strategy)
        
        return chunker
    
    def process_text(self, params: Dict[str, Any]) -> bool:
        """Execute the text processing workflow.
        
        Args:
            params: Dictionary with runtime processing parameters (task, model, input, output, etc.)
            
        Returns:
            True if processing succeeded, False otherwise
        """
        # Convert to DotDict for consistent access pattern (matching config.xxx.yyy style)
        params = DotDict(params)
        
        self.logger.debug(f"Starting text processing: task={params.task}, model={params.model_name}")
        print(f"\nStarting processing...")
        
        try:
            # Load task configuration
            task_config = self._load_task_config(params.task)
            if not task_config:
                return False
            
            # Create processing components
            processor, chunker = self._create_processing_components(params, task_config)
            if not processor:
                return False
            
            # Setup I/O components
            text_reader = self._create_text_reader(params)
            if not text_reader:
                return False
            
            text_writer = self._create_text_writer(params)
            
            # Execute workflow
            success = self._execute_workflow(
                processor, chunker, text_reader, text_writer, params
            )
            
            return success
            
        except Exception as e:
            error_msg = f"Error during setup: {e}"
            print(error_msg)
            self.logger.error(error_msg, exc_info=True)
            return False
    
    def _load_task_config(self, task: str) -> Optional[DotDict]:
        """Load and validate task configuration.
        
        Args:
            task: The task name to load config for
            
        Returns:
            Task configuration object (DotDict with PROMPT, INPUT_LANGUAGE, etc.) or None if not found/invalid
        """
        self.logger.debug(f"Loading task configuration for: {task}")
        task_config = ProcessorFactory.get_task_config(self.config.actions_config, task)
        
        if not task_config:
            error_msg = f"No configuration found for task '{task}'"
            print(error_msg)
            self.logger.error(error_msg)
            return None
        
        # Validate required fields
        if not hasattr(task_config, 'INPUT_LANGUAGE'):
            error_msg = f"Task '{task}' config missing INPUT_LANGUAGE field"
            print(error_msg)
            self.logger.error(error_msg)
            return None
        
        return task_config
    
    def _create_processing_components(self, params: DotDict, task_config: DotDict) -> Tuple[Optional[TextProcessor], Optional[TextChunker]]:
        """Create processor and chunker components.
        
        Args:
            params: Processing parameters (DotDict with task, model_name, etc.)
            task_config: Task configuration object (DotDict with INPUT_LANGUAGE, CHUNKERS, etc.)
            
        Returns:
            Tuple of (processor, chunker) or (None, None) on error
        """
        self.logger.debug("Creating processor and chunker")
        
        try:
            processor = ProcessorFactory.create_processor(params.task, params.model_name, config=self.config)
            
            # Handle chunkers from CLI (None = use config, [] = no chunking, ['x'] = override)
            cli_chunkers = params.get('chunkers')
            chunker = self._create_chunker_for_task(
                task_config, params.task, language=task_config.INPUT_LANGUAGE, 
                chunkers=cli_chunkers
            )
            
            return processor, chunker
            
        except Exception as e:
            error_msg = f"Failed to create processing components: {e}"
            print(error_msg)
            self.logger.error(error_msg)
            return None, None
    
    def _create_text_reader(self, params: DotDict) -> Optional[TextReader]:
        """Create and configure text reader with input source.
        
        Args:
            params: Processing parameters (DotDict with input_text or input_path)
            
        Returns:
            Configured TextReader instance or None if no valid input
        """
        text_reader = TextReader()
        
        if params.get('input_text'):
            # Set direct text input
            text_reader.set_text(params.input_text)
            self.logger.debug(f"Using direct text input ({len(params.input_text)} characters)")
        elif params.get('input_path'):
            # Read from file
            text_reader.read_by_format(params.input_path)
            self.logger.debug(f"Read text from file: {params.input_path}")
        else:
            error_msg = "Error: No input provided"
            print(error_msg)
            self.logger.error(error_msg)
            return None
        
        return text_reader
    
    def _create_text_writer(self, params: DotDict) -> TextWriter:
        """Create text writer with output destination.
        
        Args:
            params: Processing parameters (DotDict with output_path)
            
        Returns:
            Configured TextWriter instance
        """
        return TextWriter(output_path=params.output_path)
    
    def _execute_workflow(self, processor: TextProcessor, chunker: Optional[TextChunker],
                         text_reader: TextReader, text_writer: TextWriter,
                         params: DotDict) -> bool:
        """Execute the processing workflow and display results.
        
        Args:
            processor: Text processor instance for the task
            chunker: Text chunker instance or None
            text_reader: Configured text reader
            text_writer: Configured text writer
            params: Processing parameters (DotDict with task, verbose, etc.)
            
        Returns:
            True if processing succeeded, False otherwise
        """
        # Create workflow orchestrator
        self.logger.debug("Creating processing workflow")
        workflow = ProcessingWorkflow(
            processor=processor,
            chunker=chunker,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=params.verbose
        )
        
        # Execute processing (the processor reads its prompt from the task config)
        self.logger.debug("Executing workflow")
        success = workflow.process()
        
        # Display results
        self._display_workflow_results(success, params, workflow)
        
        return success
    
    def _display_workflow_results(self, success: bool, params: DotDict, workflow: ProcessingWorkflow) -> None:
        """Display workflow execution results and statistics.
        
        Args:
            success: Whether workflow execution succeeded
            params: Processing parameters (DotDict with output_path, verbose)
            workflow: Workflow instance with statistics
        """
        if success:
            if params.output_path:
                print(f"\nOutput saved to: {params.output_path}")
                self.logger.debug(f"Processing completed successfully. Output: {params.output_path}")
            else:
                self.logger.debug("Processing completed successfully. Output to console.")
            
            # Display workflow statistics if verbose
            if params.verbose:
                stats = workflow.get_stats()
                if stats:
                    print(f"\nWorkflow Statistics:")
                    print(f"- Processing time: {stats.get('processing_time', 0):.2f} seconds")
                    print(f"- Chunks processed: {stats.get('chunks_processed', 0)}/{stats.get('total_chunks', 0)}")
                    print(f"- Success rate: {stats.get('success_rate', 0):.1f}%")
                    if stats.get('failed_chunks', 0) > 0:
                        print(f"- Failed chunks: {stats['failed_chunks']}")
                    self.logger.debug(f"App: Workflow stats: {stats}")
        else:
            error_msg = "Processing failed. Please check the error messages above."
            print(f"\n{error_msg}")
            self.logger.error(f"App: {error_msg}")
    
    def run(self, startup_context: Dict[str, Any]) -> None:
        """
        Main application entry point.
        
        Args:
            startup_context: Context from startup manager containing environment status
        """
        # Display banner
        self._display_banner()
        
        # Display Ollama status after banner
        if startup_context.get("ollama_running"):
            print("✓ Ollama service is running\n")
        
        # Collect parameters using the orchestrator (with automatic fallback)
        self.logger.debug("Collecting parameters via orchestrator")
        try:
            params = self.param_orchestrator.collect_parameters()
        except UserCancelled:
            print("Exiting application...")
            self.logger.debug("App: User cancelled during parameter collection")
            return
        
        # Validate runtime requirements (fast-fail: Ollama service, model existence, files, etc.)
        self.logger.debug("Validating runtime requirements")
        runtime_validation = self.param_orchestrator.validate_runtime(params)
        if not runtime_validation.is_valid:
            self.param_orchestrator.handle_runtime_validation_errors(runtime_validation)
        
        # Process the text
        success = self.process_text(params.to_dict())
        
        if not success:
            self.logger.error("Application failed")
            sys.exit(1)
        
        self.logger.debug("Application completed successfully")
    
    def _display_banner(self) -> None:
        """Display application banner."""
        print("""
╔═════════════════════════════════════╗
║                                     ║
║       Romanian Text Processor       ║
║                                     ║
╚═════════════════════════════════════╝
        """)
