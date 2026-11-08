"""
Interactive parameter collector.
Collects parameters through user prompts.
"""

import sys
from typing import Optional, List, Dict, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.utils.app_logger import AppLogger
    from src.app.path_manager import PathManager

from src.app.exceptions import UserCancelled
from src.app.parameter_collection.base_collector import BaseParameterCollector
from src.app.processor_factory import ProcessorFactory

class InteractiveParameterCollector(BaseParameterCollector):
    """
    Collects parameters through interactive user prompts.
    
    This collector always prompts the user for input.
    It's used as a fallback when CLI args are insufficient.
    
    Task options are generated dynamically from ProcessorFactory to ensure
    consistency with CLI mode and automatic inclusion of new tasks.
    """
    
    def __init__(self, path_manager: "PathManager", logger: Optional["AppLogger"] = None):
        """
        Initialize interactive collector.
        
        Args:
            path_manager: PathManager for file operations
            logger: Optional logger for debugging
        """
        super().__init__(logger)
        self.path_manager = path_manager
    
    def _get_task_options(self) -> Dict[int, Tuple[str, str]]:
        """Generate task options dynamically from ProcessorFactory.
        
        Returns:
            Dictionary mapping choice numbers to (task_name, description) tuples
        """
        
        # Get tasks and descriptions using same methods as CLI
        available_tasks = ProcessorFactory.get_available_tasks()
        task_descriptions = ProcessorFactory.get_task_descriptions()
        
        # Build numbered options dictionary
        task_options = {}
        for idx, task in enumerate(available_tasks, start=1):
            description = task_descriptions.get(task, "Process text")
            task_options[idx] = (task, description)
        
        self.logger.debug(f"InteractiveCollector: Generated {len(task_options)} task options from ProcessorFactory")
        
        return task_options
    
    def _read_input(self, prompt: str = "") -> str:
        """Read a line from the user, turning Ctrl+C into UserCancelled."""
        try:
            return input(prompt)
        except KeyboardInterrupt:
            self.logger.debug("InteractiveCollector: User interrupted (Ctrl+C)")
            raise UserCancelled() from None
    
    def _prompt_menu_choice(self, prompt: str, max_choice: int) -> int:
        """Ask for a number from 1 to max_choice until a valid one is entered.
        
        Args:
            prompt: Text shown when asking for the choice
            max_choice: Highest valid choice
            
        Returns:
            The chosen number (1 to max_choice)
            
        Raises:
            UserCancelled: If the user enters 0 or presses Ctrl+C
        """
        while True:
            try:
                choice = int(self._read_input(prompt))
            except ValueError:
                print("Please enter a valid number.")
                continue
            
            if choice == 0:
                self.logger.debug("InteractiveCollector: User chose to exit")
                raise UserCancelled()
            if 1 <= choice <= max_choice:
                return choice
            print(f"Invalid selection. Please choose 0-{max_choice}.")
    
    def collect_task(self) -> Optional[str]:
        """Prompt user to select a task.
        
        Task list is generated dynamically to match CLI behavior and ensure
        all registered tasks are available in interactive mode.
        """
        self.logger.debug("InteractiveCollector: Prompting user for task selection")
        
        # Generate task options dynamically
        task_options = self._get_task_options()
        max_choice = len(task_options)
        
        print("\nSelect a processing task:")
        for key, (task, description) in task_options.items():
            print(f"{key}. {description}")
        print("0. Exit")
        
        choice = self._prompt_menu_choice(f"\nEnter your choice (0-{max_choice}): ", max_choice)
        selected_task = task_options[choice][0]
        self.logger.debug(f"InteractiveCollector: User selected task: {selected_task}")
        self._log_collection("task", selected_task, "interactive")
        return selected_task
    
    def collect_model_name(self) -> Optional[str]:
        """Prompt user to select a model."""
        self.logger.debug("InteractiveCollector: Prompting user for model selection")
        
        from src.services import get_ollama_service
        ollama_service = get_ollama_service()
        
        # Check if Ollama is running
        if not ollama_service.is_ollama_running():
            error_msg = "Ollama service is not running. Please start it manually."
            print(f"\n❌ {error_msg}")
            self.logger.error(f"InteractiveCollector: {error_msg}")
            sys.exit(1)
        
        # Get available models
        ollama_models = ollama_service.get_model_names()
        self.logger.debug(f"InteractiveCollector: Found {len(ollama_models)} Ollama models")
        
        if not ollama_models:
            error_msg = "No models found. Check Ollama service and downloaded models."
            print(f"\n❌ {error_msg}")
            self.logger.error(f"InteractiveCollector: {error_msg}")
            sys.exit(1)
        
        print("\nAvailable models:")
        for i, model in enumerate(ollama_models, 1):
            print(f"{i}. {model}")
        print("0. Exit")
        
        choice = self._prompt_menu_choice("\nSelect model (enter number): ", len(ollama_models))
        selected_model = ollama_models[choice - 1]
        print(f"Selected model: {selected_model}")
        self.logger.debug(f"InteractiveCollector: User selected model: {selected_model}")
        self._log_collection("model_name", selected_model, "interactive")
        return selected_model
    
    def collect_input(self) -> Tuple[Optional[str], Optional[str]]:
        """Prompt user to select input source."""
        self.logger.debug("InteractiveCollector: Prompting user for input selection")
        
        print("\nSelect input option:")
        print("0. Exit")
        print("1. Enter text directly (CLI)")
        
        # Get available files
        input_files = self.path_manager.get_input_files()
        
        if input_files:
            print("\nAvailable input files:")
            for i, file_path in enumerate(input_files, 2):
                file_size = self.path_manager.get_file_size_str(file_path)
                print(f"{i}. {file_path.name} {file_size}")
        else:
            print("\nNo input files found in the input directory.")
            print("You can:")
            print("- Choose option 1 to enter text directly")
            print("- Add files to the input directory and restart")
            self.logger.warning("InteractiveCollector: No input files found in input directory")
        
        max_choice = len(input_files) + 1
        
        while True:
            choice = self._prompt_menu_choice(f"\nEnter your choice (0-{max_choice}): ", max_choice)
            
            if choice == 1:
                self.logger.debug("InteractiveCollector: User chose CLI text input")
                text_content = self._read_text_input()
                if text_content is not None:
                    self._log_collection("input_text", f"<{len(text_content)} chars>", "interactive")
                    return None, text_content
                continue
            
            selected_file = str(input_files[choice - 2])
            self.logger.debug(f"InteractiveCollector: User selected file: {selected_file}")
            self._log_collection("input_path", selected_file, "interactive")
            return selected_file, None
    
    def _read_text_input(self) -> Optional[str]:
        """Read multi-line text typed by the user.
        
        Returns:
            The text, or None if the user cancelled or entered nothing
        """
        print("\nEnter your text (press Ctrl+Z then Enter on Windows or Ctrl+D on Unix when done):")
        print("(Or type 'exit' on a new line to cancel)")
        
        text_lines: List[str] = []
        try:
            while True:
                line = self._read_input()
                if line.lower().strip() == 'exit':
                    print("Text input cancelled.")
                    self.logger.debug("InteractiveCollector: User cancelled text input")
                    return None
                text_lines.append(line)
        except EOFError:
            pass
        
        text_content = '\n'.join(text_lines)
        if not text_content.strip():
            print("No text entered. Please try again.")
            self.logger.warning("InteractiveCollector: User entered empty text")
            return None
        
        self.logger.debug(f"InteractiveCollector: User entered {len(text_content)} characters of text")
        return text_content
    
    def collect_output(self, input_source: str, task: str) -> Optional[str]:
        """Prompt user to select output destination."""
        self.logger.debug("InteractiveCollector: Prompting user for output selection")
        
        default_output = self.path_manager.generate_output_path(input_source, task)
        
        print("\nSelect output destination:")
        print("1. Save to file")
        print("2. Display in console (no file saved)")
        print("0. Exit")
        
        choice = self._read_input("\nEnter your choice (0-2): ").strip()
        
        if choice == '0' or choice.lower() == 'exit':
            self.logger.debug("User chose to exit during output selection")
            raise UserCancelled()
            
        elif choice == '2':
            # Console output
            self.logger.debug("User selected console output")
            print("Output will be displayed in console.")
            self._log_collection("output_path", "None (console)", "interactive")
            return None
            
        elif choice == '1':
            # File output
            custom_output = self._read_input(
                f"\nOutput will be saved as: {default_output}\n"
                f"Enter custom output path (or press Enter to accept, 'exit' to quit): "
            )
            
            if custom_output.lower().strip() == 'exit':
                self.logger.debug("User chose to exit during file path selection")
                raise UserCancelled()
            
            result = custom_output if custom_output else str(default_output)
            self.logger.debug(f"Output file selected: {result}")
            self._log_collection("output_path", result, "interactive")
            return result
        
        print("Invalid choice. Defaulting to file output.")
        self.logger.warning(f"Invalid output choice '{choice}', defaulting to file")
        result = str(default_output)
        self._log_collection("output_path", result, "interactive (default)")
        return result
    
    def collect_verbose(self) -> bool:
        """Prompt user for verbose mode preference."""
        self.logger.debug("Prompting user for verbose preference")
        
        response = self._read_input("\nShow detailed progress? (y/n/exit): ").lower().strip()
        if response == 'exit':
            self.logger.debug("User chose to exit during verbose confirmation")
            raise UserCancelled()
        
        verbose = response == 'y'
        self.logger.debug(f"Verbose mode: {verbose}")
        self._log_collection("verbose", verbose, "interactive")
        return verbose
    
    def collect_chunkers(self) -> Optional[List[str]]:
        """Chunking strategies cannot be configured in interactive mode.
        
        Always returns None, which means "use config defaults".
        Chunking is configured per-task in text_actions_config.json.
        CLI users can override with --chunkers flag.
        """
        return None
