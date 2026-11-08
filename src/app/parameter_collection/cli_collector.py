"""
CLI parameter collector.
Collects parameters from command-line arguments.
"""

import argparse
from typing import Optional, List, Tuple, TYPE_CHECKING

from src.app.parameter_collection.base_collector import BaseParameterCollector
from src.app.processor_factory import ProcessorFactory

if TYPE_CHECKING:
    from src.utils.app_logger import AppLogger
    from src.app.path_manager import PathManager


class CLIParameterCollector(BaseParameterCollector):
    """
    Collects parameters from command-line arguments.
    
    This collector parses command-line arguments and extracts parameters.
    It does NOT prompt the user - it only reads what was provided.
    
    Arguments are categorized into three groups:
    - REQUIRED_ARGS: Must have values for processing to occur
    - BEHAVIORAL_ARGS: Define how/where processing happens
    - UTILITY_ARGS: Meta/runtime control, orthogonal to processing logic
    """
    
    # Argument categorization
    REQUIRED_ARGS = {'task', 'model', 'input', 'text'}
    BEHAVIORAL_ARGS = {'output', 'console', 'chunkers'}
    UTILITY_ARGS = {'verbose'}
    
    def __init__(self, path_manager: "PathManager", logger: Optional["AppLogger"] = None):
        """
        Initialize CLI collector.
        
        Args:
            path_manager: PathManager for output path generation
            logger: Optional logger for debugging
        """
        super().__init__(logger)
        self.path_manager = path_manager
        self._args: Optional[argparse.Namespace] = None
        # Lazy parsing: arguments are parsed only when first accessed
    
    def _ensure_args_parsed(self):
        """Parse command-line arguments lazily on first access.
        
        This allows the class to be instantiated without immediately parsing sys.argv,
        which is important for testing and when the CLI collector is created but not used.
        
        After calling this method, self._args is guaranteed to be non-None, even though
        PyLance might not be able to infer that.
        """
        if self._args is None:
            self._parse_arguments()
    
    def _build_help_epilog(self) -> str:
        """Build dynamic help epilog with available tasks from ProcessorFactory.
        
        Returns:
            Formatted help epilog string
        """
        # Get tasks and descriptions dynamically
        available_tasks = ProcessorFactory.get_available_tasks()
        task_descriptions = ProcessorFactory.get_task_descriptions()
        
        # Build task list
        task_lines = []
        for task in available_tasks:
            desc = task_descriptions.get(task, "Process text")
            task_lines.append(f"  {task:<18} {desc}")
        
        tasks_section = "\n".join(task_lines)
        
        # Build complete epilog
        epilog = f"""
Available Tasks:
{tasks_section}

Usage Modes:
  Interactive Mode:
    python run.py
    (Prompts you for all required parameters)
  
  Command-Line Mode:
    python run.py --task TASK --input FILE [OPTIONS]
    (Uses CLI parameters and default values where available, prompts only for missing ones)
  
  Non-Interactive Mode:
    python run.py --task TASK --input FILE --non-interactive
    (Fails immediately if required parameters are missing)

Examples:
  # Add diacritics to a file
  python run.py --task diacritics --input file.txt

  # Summarize text and display in console
  python run.py --task summarize --input document.txt --console

  # Process direct text input
  python run.py --task diacritics --text "Diacriticele trebuie adaugate in acest text" --console

  # Use custom task with specific model
  python run.py --task custom --input file.txt --model jobautomation/OpenEuroLLM-Romanian:latest --output result.txt

  # Non-interactive mode for automation
  python run.py --task edit --input file.txt --output edited.txt --non-interactive

Notes:
  - Currently only supports running models locally through Ollama, so Ollama service must be running
  - Output typically defaults to ./output/ directory with auto-generated filename. Can be changed in file_config.json.
  - Use --console to display results instead of saving to file
"""
        return epilog
    
    def _parse_arguments(self):
        """Parse command-line arguments."""
        # Get available tasks dynamically
        available_tasks = ProcessorFactory.get_available_tasks()
        task_list = ", ".join(available_tasks)
        
        # Build dynamic help
        epilog = self._build_help_epilog()
        
        parser = argparse.ArgumentParser(
            description="Romanian Text Processing Application - Local LLM-powered text processing",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=epilog
        )
        
        parser.add_argument('--task', type=str, 
                          help=f'Processing task: {task_list}')
        parser.add_argument('--input', '-i', type=str, help='Input file path')
        parser.add_argument('--text', '-t', type=str, help='Direct text input in the console (alternative to --input)')
        parser.add_argument('--output', '-o', type=str, help='Output file path')
        parser.add_argument('--console', '-c', action='store_true', 
                          help='Display output in console instead of saving to file')
        parser.add_argument('--model', '-m', type=str, help='Model name to use')
        parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
        parser.add_argument('--chunkers', nargs='*', metavar='CHUNKER',
                          help='Override chunking strategies (space-separated). Use "none" to disable chunking. Omit flag to use config defaults. Examples: --chunkers sentence_split size_optimizing, --chunkers none')
        parser.add_argument('--non-interactive', action='store_true',
                          help='Non-interactive mode: no user prompts. Fails if required parameters are missing.')
        
        self._args = parser.parse_args()
        
        # Validate mutually exclusive options
        if self._args.input and self._args.text:
            parser.error("--input and --text are mutually exclusive. Use one or the other.")
        
        if self._args.output and self._args.console:
            parser.error("--output and --console are mutually exclusive. Use one or the other.")
        
        provided_args = [k for k, v in vars(self._args).items() if v is not None and v is not False]
        self.logger.debug(f"CLICollector: Parsed CLI arguments: {len(provided_args)} parameters provided")
    
    def is_non_interactive(self) -> bool:
        """
        Check if non-interactive mode is enabled.
        
        Returns:
            True if --non-interactive was specified, False otherwise
        """
        self._ensure_args_parsed()
        self._log_collection("non_interactive", self._args.non_interactive, "CLI")
        return self._args.non_interactive
    
    def has_processing_args(self) -> bool:
        """
        Check if any processing-related arguments were provided.
        
        Processing arguments include both required args (task, model, input) and
        behavioral args (output, console, chunkers) that define what/how/where to process.
        Utility args like --verbose do not trigger CLI mode as they're orthogonal to
        the processing workflow.
        
        Returns:
            True if any required or behavioral argument is present, False for pure interactive mode
        """
        self._ensure_args_parsed()
        
        # Combine required and behavioral args for processing check
        processing_args = self.REQUIRED_ARGS | self.BEHAVIORAL_ARGS
        
        # Check if any processing argument is present
        has_args = any(
            getattr(self._args, arg, None)
            for arg in processing_args
        )
        
        self.logger.debug(f"CLICollector: has_processing_args={has_args}")
        
        return has_args
    
    def collect_task(self) -> Optional[str]:
        """Collect task from CLI args."""
        self._ensure_args_parsed()
        task = self._args.task
        if task:
            self._log_collection("task", task, "CLI")
        return task
    
    def collect_model_name(self) -> Optional[str]:
        """Collect model name from CLI args."""
        self._ensure_args_parsed()
        model = self._args.model
        if model:
            self._log_collection("model_name", model, "CLI")
        return model
    
    def collect_input(self) -> Tuple[Optional[str], Optional[str]]:
        """Collect input from CLI args."""
        self._ensure_args_parsed()
        
        input_path = self._args.input
        input_text = self._args.text
        
        if input_path:
            self._log_collection("input_path", input_path, "CLI")
        if input_text:
            self._log_collection("input_text", f"<{len(input_text)} chars>", "CLI")
        
        return input_path, input_text
    
    def collect_chunkers(self) -> Optional[List[str]]:
        """Collect chunking strategies from CLI args.
        
        Returns:
            - None: --chunkers flag not provided (use config defaults)
            - []: --chunkers none (explicit no chunking)
            - ['strategy1', 'strategy2']: Specific strategies (override config)
        """
        self._ensure_args_parsed()
        
        chunkers = self._args.chunkers
        
        # Flag not provided at all
        if chunkers is None:
            return None
        
        # Flag provided with 'none' keyword
        if len(chunkers) == 1 and chunkers[0].lower() == 'none':
            self._log_collection("chunkers", "[] (no chunking)", "CLI")
            return []
        
        # Flag provided with strategy names
        if chunkers is not None:
            self._log_collection("chunkers", chunkers, "CLI")
        return chunkers
    
    def collect_output(self, input_source: str, task: str) -> Optional[str]:
        """Collect output destination from CLI args.
        
        Args:
            input_source: Input identifier ("cli_text" for text input, file path for file input)
            task: The processing task
        """
        self._ensure_args_parsed()
        
        # If input is CLI text, default to console output (unless explicit output file provided)
        if input_source == "cli_text":
            if self._args.output:
                # Explicit output file overrides default
                self._log_collection("output_path", self._args.output, "CLI")
                return self._args.output
            else:
                # Default to console for CLI text input
                self._log_collection("output_path", "None (console)", "default for CLI text")
                return None
        
        # For file input, check console flag or output file
        if self._args.console:
            # Console output explicitly requested
            self._log_collection("output_path", "None (console)", "CLI")
            return None
        elif self._args.output:
            # Explicit output file
            self._log_collection("output_path", self._args.output, "CLI")
            return self._args.output
        else:
            # Auto-generate default output path
            default_path = str(self.path_manager.generate_output_path(input_source, task))
            self._log_collection("output_path", default_path, "auto-generated")
            return default_path
    
    def collect_verbose(self) -> bool:
        """Collect verbose flag from CLI args."""
        self._ensure_args_parsed()
        verbose = self._args.verbose
        if verbose:
            self._log_collection("verbose", verbose, "CLI")
        return verbose
