"""
Data models for parameter collection.
Defines the structure of parameters used throughout the application.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class OutputMode(Enum):
    """Output destination modes."""
    FILE = "file"
    CONSOLE = "console"


@dataclass
class ProcessingParameters:
    """
    Complete set of parameters needed for text processing.
    
    This is the contract that all collectors must fulfill.
    """
    # Required parameters
    task: Optional[str] = None
    model_name: Optional[str] = None
    input_path: Optional[str] = None
    input_text: Optional[str] = None
    output_path: Optional[str] = None
    
    # Optional parameters with defaults
    verbose: bool = False
    chunkers: Optional[List[str]] = None  # Chunking strategies from CLI (overrides config)
    
    # Internal tracking
    _source: Dict[str, str] = field(default_factory=dict)  # Track where each param came from
    
    def is_complete(self) -> bool:
        """Check if all required parameters are collected."""
        has_task = self.task is not None
        has_model = self.model_name is not None
        has_input = self.input_path is not None or self.input_text is not None
        # Output can be None (console) or auto-generated, so it doesn't affect completeness
        
        return has_task and has_model and has_input
    
    def get_missing_required(self) -> List[str]:
        """Get list of missing required parameters."""
        missing = []
        if self.task is None:
            missing.append("task")
        if self.model_name is None:
            missing.append("model")
        if self.input_path is None and self.input_text is None:
            missing.append("input")
        return missing
    
    def get_input_source(self) -> Optional[str]:
        """Get the actual input source (text or path)."""
        return self.input_text if self.input_text else self.input_path
    
    def get_output_mode(self) -> OutputMode:
        """Determine output mode."""
        return OutputMode.CONSOLE if self.output_path is None else OutputMode.FILE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format (convenience method)."""
        return {
            "task": self.task,
            "model_name": self.model_name,
            "input_path": self.input_path,
            "input_text": self.input_text,
            "output_path": self.output_path,
            "verbose": self.verbose,
            "chunkers": self.chunkers
        }
    
    def mark_source(self, param_name: str, source: str) -> None:
        """Mark where a parameter came from (for debugging/logging)."""
        self._source[param_name] = source


@dataclass
class ValidationResult:
    """Result of parameter validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.is_valid = False
        self.errors.append(message)
    
    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
    
    def get_error_message(self) -> str:
        """Get formatted error message."""
        if not self.errors:
            return ""
        return "\n".join([f"❌ {error}" for error in self.errors])
