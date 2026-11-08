"""
Parameter Collection Module

This module contains the complete parameter collection system using the Strategy pattern.
It provides:
- Data Models: ProcessingParameters, ValidationResult, OutputMode
- Validators: ParameterValidator for syntax and runtime validation
- Collectors: Different strategies for collecting user input parameters
  - BaseParameterCollector: Abstract interface defining the collection contract
  - CLIParameterCollector: Collects parameters from command-line arguments
  - InteractiveParameterCollector: Collects parameters through interactive prompts
- Orchestrator: ParameterCollectionOrchestrator coordinates collection with fallback logic
"""

from src.app.parameter_collection.param_models import ProcessingParameters, ValidationResult, OutputMode
from src.app.parameter_collection.param_validator import ParameterValidator
from src.app.parameter_collection.base_collector import BaseParameterCollector
from src.app.parameter_collection.cli_collector import CLIParameterCollector
from src.app.parameter_collection.interactive_collector import InteractiveParameterCollector
from src.app.parameter_collection.param_orchestrator import ParameterCollectionOrchestrator

__all__ = [
    'ProcessingParameters',
    'ValidationResult',
    'OutputMode',
    'ParameterValidator',
    'BaseParameterCollector',
    'CLIParameterCollector', 
    'InteractiveParameterCollector',
    'ParameterCollectionOrchestrator'
]
