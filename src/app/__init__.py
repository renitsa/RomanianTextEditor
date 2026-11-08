"""
Application layer for the Romanian Text Processor.
Contains the main application classes and interfaces.
"""

from .processor_factory import ProcessorFactory
from .path_manager import PathManager
from .text_processing_app import TextProcessingApplication
from .startup_manager import StartupManager, initialize_application
from .parameter_collection.param_models import ProcessingParameters, ValidationResult, OutputMode
from .parameter_collection.base_collector import BaseParameterCollector
from .parameter_collection.cli_collector import CLIParameterCollector
from .parameter_collection.interactive_collector import InteractiveParameterCollector
from .parameter_collection.param_validator import ParameterValidator
from .parameter_collection.param_orchestrator import ParameterCollectionOrchestrator

__all__ = [
    'ProcessorFactory',
    'PathManager', 
    'TextProcessingApplication',
    'StartupManager',
    'initialize_application',
    'ProcessingParameters',
    'ValidationResult',
    'OutputMode',
    'BaseParameterCollector',
    'CLIParameterCollector',
    'InteractiveParameterCollector',
    'ParameterValidator',
    'ParameterCollectionOrchestrator'
]