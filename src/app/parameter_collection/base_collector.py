"""
Base interface for parameter collectors.
All collectors must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, TYPE_CHECKING

from src.app.parameter_collection.param_models import ProcessingParameters
from src.utils.app_logger import get_logger

if TYPE_CHECKING:
    from src.utils.app_logger import AppLogger


class BaseParameterCollector(ABC):
    """
    Abstract base class for parameter collection.
    
    Each collector is responsible for gathering parameters from a specific source
    (CLI args, interactive prompts, GUI forms, web requests, etc.).
    """
    
    def __init__(self, logger: Optional["AppLogger"] = None):
        """Initialize collector with an optional logger (defaults to the app logger)."""
        self.logger = logger if logger is not None else get_logger("RomanianTextEditor.App")
        self._collector_name = self.__class__.__name__
    
    @abstractmethod
    def collect_task(self) -> Optional[str]:
        """Collect the processing task parameter."""
        pass
    
    @abstractmethod
    def collect_model_name(self) -> Optional[str]:
        """Collect the model name parameter."""
        pass
    
    @abstractmethod
    def collect_input(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Collect input source.
        
        Returns:
            tuple: (input_path, input_text) - one will be None
        """
        pass
    
    @abstractmethod
    def collect_output(self, input_source: str, task: str) -> Optional[str]:
        """
        Collect output destination.
        
        Args:
            input_source: Input file/text (used for default generation)
            task: Processing task (used for default generation)
        
        Returns:
            Optional[str]: Output path, or None for console output
        """
        pass
    
    @abstractmethod
    def collect_verbose(self) -> bool:
        """Collect verbose flag."""
        pass
    
    @abstractmethod
    def collect_chunkers(self) -> Optional[List[str]]:
        """Collect chunking strategies.
        
        Returns:
            Optional list of chunker names, or None if not specified.
            Empty list means explicit 'no chunking'.
        """
        pass
    
    def collect_all(self) -> ProcessingParameters:
        """
        Collect all available parameters from this source.
        
        This method orchestrates all collection methods.
        Subclasses can override if they need custom logic.
        """
        params = ProcessingParameters()
        
        self.logger.debug(f"{self._collector_name}: Collecting parameters")
        
        params.task = self.collect_task()
        params.model_name = self.collect_model_name()
        params.input_path, params.input_text = self.collect_input()
        
        # Output needs input context
        # Pass the appropriate identifier based on input type
        if params.input_text:
            input_identifier = "cli_text"
        elif params.input_path:
            input_identifier = params.input_path
        else:
            input_identifier = "text_input"
        
        task = params.task if params.task is not None else "unknown"
        params.output_path = self.collect_output(input_identifier, task)
        
        params.verbose = self.collect_verbose()
        params.chunkers = self.collect_chunkers()
        
        collected = [k for k, v in params.to_dict().items() if v is not None]
        self.logger.debug(f"{self._collector_name}: Collected {len(collected)} parameters")
        
        return params
    
    def _log_collection(self, param_name: str, value, source: Optional[str] = None):
        """Helper to log parameter collection."""
        source_info = f" from {source}" if source else ""
        self.logger.debug(f"{self._collector_name}: Collected {param_name}={value}{source_info}")