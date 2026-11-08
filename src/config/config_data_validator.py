from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict
from dataclasses import dataclass, field

@dataclass
class LoggingConfigData:
    """Dataclass for validating logging configuration."""
    CONSOLE_LEVEL: str
    FILE_LEVEL: str
    LOG_TO_FILE: bool
    LOG_TO_CONSOLE: bool
    MAX_LOG_FILES: int
    LOG_FILE_MAX_SIZE_MB: int
    USE_SINGLE_LOG_FILE: bool
    SINGLE_LOG_FILE_NAME: str
    CONSOLE_FORMAT: str
    LOG_FORMAT: str
    DATE_FORMAT: str

    def __post_init__(self) -> None:
        errors = []
        
        # Validate log levels
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.CONSOLE_LEVEL not in valid_levels:
            errors.append(f"CONSOLE_LEVEL must be one of {valid_levels}")
        if self.FILE_LEVEL not in valid_levels:
            errors.append(f"FILE_LEVEL must be one of {valid_levels}")
        
        # Validate boolean flags
        if not isinstance(self.LOG_TO_FILE, bool):
            errors.append("LOG_TO_FILE must be boolean")
        if not isinstance(self.LOG_TO_CONSOLE, bool):
            errors.append("LOG_TO_CONSOLE must be boolean")
        if not isinstance(self.USE_SINGLE_LOG_FILE, bool):
            errors.append("USE_SINGLE_LOG_FILE must be boolean")
        
        # Validate numeric limits
        if not isinstance(self.MAX_LOG_FILES, int) or self.MAX_LOG_FILES < 1:
            errors.append("MAX_LOG_FILES must be a positive integer")
        if not isinstance(self.LOG_FILE_MAX_SIZE_MB, int) or self.LOG_FILE_MAX_SIZE_MB < 1:
            errors.append("LOG_FILE_MAX_SIZE_MB must be a positive integer")
        
        # Validate format strings
        if not isinstance(self.CONSOLE_FORMAT, str) or not self.CONSOLE_FORMAT:
            errors.append("CONSOLE_FORMAT must be a non-empty string")
        if not isinstance(self.LOG_FORMAT, str) or not self.LOG_FORMAT:
            errors.append("LOG_FORMAT must be a non-empty string")
        if not isinstance(self.DATE_FORMAT, str) or not self.DATE_FORMAT:
            errors.append("DATE_FORMAT must be a non-empty string")
        if not isinstance(self.SINGLE_LOG_FILE_NAME, str) or not self.SINGLE_LOG_FILE_NAME:
            errors.append("SINGLE_LOG_FILE_NAME must be a non-empty string")

        if errors:
            raise ValueError("Logging config validation errors:\n" + "\n".join(errors))

@dataclass
class FileConfigData:
    """Dataclass for validating file and folder configuration."""
    ESSENTIAL_DIRS: Dict[str, str]
    SUPPORTED_TEXT_EXTENSIONS: list
    SUPPORTED_DOCUMENT_EXTENSIONS: list
    DEFAULT_ENCODING: str
    CREATE_DIRS_IF_MISSING: bool
    MAX_FILENAME_LENGTH: int
    OUTPUT_SUFFIX_SEPARATOR: str
    OUTPUT_TIMESTAMP_FORMAT: str
    DEFAULT_OUTPUT_FILENAME: str

    def __post_init__(self) -> None:
        errors = []
        
        # Validate essential directories
        if not isinstance(self.ESSENTIAL_DIRS, dict):
            errors.append("ESSENTIAL_DIRS must be a dictionary")
        else:
            for dir_name, dir_path in self.ESSENTIAL_DIRS.items():
                if not isinstance(dir_path, str) or not dir_path:
                    errors.append(f"Essential directory '{dir_name}' must be a non-empty string")
        
        # Validate file extensions lists
        if not isinstance(self.SUPPORTED_TEXT_EXTENSIONS, list):
            errors.append("SUPPORTED_TEXT_EXTENSIONS must be a list")
        elif len(self.SUPPORTED_TEXT_EXTENSIONS) == 0:
            errors.append("SUPPORTED_TEXT_EXTENSIONS must contain at least one extension")
        else:
            for ext in self.SUPPORTED_TEXT_EXTENSIONS:
                if not isinstance(ext, str) or not ext:
                    errors.append("SUPPORTED_TEXT_EXTENSIONS must contain non-empty strings")
                    break
                if not ext.startswith('.'):
                    errors.append(f"Extension '{ext}' in SUPPORTED_TEXT_EXTENSIONS must start with '.'")
                    break
        
        if not isinstance(self.SUPPORTED_DOCUMENT_EXTENSIONS, list):
            errors.append("SUPPORTED_DOCUMENT_EXTENSIONS must be a list")
        else:
            for ext in self.SUPPORTED_DOCUMENT_EXTENSIONS:
                if not isinstance(ext, str) or not ext:
                    errors.append("SUPPORTED_DOCUMENT_EXTENSIONS must contain non-empty strings")
                    break
                if not ext.startswith('.'):
                    errors.append(f"Extension '{ext}' in SUPPORTED_DOCUMENT_EXTENSIONS must start with '.'")
                    break
        
        # Validate encoding
        if not isinstance(self.DEFAULT_ENCODING, str) or not self.DEFAULT_ENCODING:
            errors.append("DEFAULT_ENCODING must be a non-empty string")
        
        # Validate boolean flags
        if not isinstance(self.CREATE_DIRS_IF_MISSING, bool):
            errors.append("CREATE_DIRS_IF_MISSING must be boolean")
        
        # Validate numeric limits
        if not isinstance(self.MAX_FILENAME_LENGTH, int) or self.MAX_FILENAME_LENGTH < 1:
            errors.append("MAX_FILENAME_LENGTH must be a positive integer")
        
        # Validate output naming settings
        if not isinstance(self.OUTPUT_SUFFIX_SEPARATOR, str) or not self.OUTPUT_SUFFIX_SEPARATOR:
            errors.append("OUTPUT_SUFFIX_SEPARATOR must be a non-empty string")
        if not isinstance(self.OUTPUT_TIMESTAMP_FORMAT, str) or not self.OUTPUT_TIMESTAMP_FORMAT:
            errors.append("OUTPUT_TIMESTAMP_FORMAT must be a non-empty string")
        elif not datetime.now().strftime(self.OUTPUT_TIMESTAMP_FORMAT).strip():
            errors.append("OUTPUT_TIMESTAMP_FORMAT must produce a non-empty timestamp")
        if not isinstance(self.DEFAULT_OUTPUT_FILENAME, str) or not Path(self.DEFAULT_OUTPUT_FILENAME).stem:
            errors.append("DEFAULT_OUTPUT_FILENAME must be a file name with a base name (e.g. 'output.txt')")
        
        if errors:
            raise ValueError("File config validation errors:\n" + "\n".join(errors))

@dataclass
class TextProcessingConfigData:
    """Dataclass for validating text processing configuration."""
    SENTENCE_TERMINATORS: List[str]
    SECONDARY_TERMINATORS: List[str]
    FALLBACK_SEPARATORS: List[str]
    SPACE_SEPARATORS: List[str]
    FALLBACK_CHUNK_SEPARATOR: str
    STRINGSPLIT_MIN_SIZE: int
    STRINGSPLIT_MAX_SIZE: int
    SENTENCESPLIT_MIN_SIZE: int
    SENTENCESPLIT_MAX_SIZE: int
    SIZEOPTIMIZING_MIN_SIZE: int
    SIZEOPTIMIZING_MAX_SIZE: int
    COMMON_ENG_ABBREVIATIONS: Set[str] = field(default_factory=set)
    COMMON_RO_ABBREVIATIONS: Set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        errors = []

        # Type validation
        if not all(isinstance(term, str) for term in self.SENTENCE_TERMINATORS):
            errors.append("SENTENCE_TERMINATORS must contain strings")
        if not all(isinstance(term, str) for term in self.SECONDARY_TERMINATORS):
            errors.append("SECONDARY_TERMINATORS must contain strings")
        if not all(isinstance(sep, str) for sep in self.FALLBACK_SEPARATORS):
            errors.append("FALLBACK_SEPARATORS must contain strings")
        if not all(isinstance(sep, str) for sep in self.SPACE_SEPARATORS):
            errors.append("SPACE_SEPARATORS must contain strings")
        if not isinstance(self.FALLBACK_CHUNK_SEPARATOR, str):
            errors.append("FALLBACK_CHUNK_SEPARATOR must be a string")

        # Range validation for size parameters
        size_params = [
            ("STRINGSPLIT_MIN_SIZE", self.STRINGSPLIT_MIN_SIZE, self.STRINGSPLIT_MAX_SIZE),
            ("SENTENCESPLIT_MIN_SIZE", self.SENTENCESPLIT_MIN_SIZE, self.SENTENCESPLIT_MAX_SIZE),
            ("SIZEOPTIMIZING_MIN_SIZE", self.SIZEOPTIMIZING_MIN_SIZE, self.SIZEOPTIMIZING_MAX_SIZE)
        ]
        
        for param_name, min_val, max_val in size_params:
            if not isinstance(min_val, int):
                errors.append(f"{param_name} must be an integer")
            elif not isinstance(max_val, int):
                errors.append(f"{param_name.replace('MIN', 'MAX')} must be an integer")
            elif min_val > max_val:
                errors.append(f"{param_name} must be <= {param_name.replace('MIN', 'MAX')}")
            elif min_val < 5:
                errors.append(f"{param_name} must be at least 5")

        # Abbreviation validation
        if not isinstance(self.COMMON_ENG_ABBREVIATIONS, set):
            errors.append("COMMON_ENG_ABBREVIATIONS must be a set")
        elif not all(isinstance(abbr, str) for abbr in self.COMMON_ENG_ABBREVIATIONS):
            errors.append("COMMON_ENG_ABBREVIATIONS must contain strings")

        if not isinstance(self.COMMON_RO_ABBREVIATIONS, set):
            errors.append("COMMON_RO_ABBREVIATIONS must be a set")
        elif not all(isinstance(abbr, str) for abbr in self.COMMON_RO_ABBREVIATIONS):
            errors.append("COMMON_RO_ABBREVIATIONS must contain strings")

        if errors:
            raise ValueError("Config validation errors:\n" + "\n".join(errors))

@dataclass
class OllamaServiceConfig:
    """Dataclass for validating individual Ollama service configuration."""
    url: str
    generate_timeout: int
    check_timeout: int
    
    def __post_init__(self) -> None:
        errors = []
        
        # Validate URL
        if not isinstance(self.url, str) or not self.url:
            errors.append("url must be a non-empty string")
        elif not self.url.startswith("http"):
            errors.append("url must be a valid HTTP/HTTPS URL")
        
        # Validate timeouts
        if not isinstance(self.generate_timeout, int) or self.generate_timeout < 1:
            errors.append("generate_timeout must be a positive integer")
        if not isinstance(self.check_timeout, int) or self.check_timeout < 1:
            errors.append("check_timeout must be a positive integer")
        
        if errors:
            raise ValueError("Ollama service config validation errors:\n" + "\n".join(errors))


@dataclass
class LLMServicesConfigData:
    """Dataclass for validating LLM services configuration."""
    OLLAMA: Dict
    
    def __post_init__(self) -> None:
        errors = []
        
        # Validate OLLAMA service config
        try:
            if not isinstance(self.OLLAMA, dict):
                errors.append("OLLAMA must be a dictionary")
            else:
                OllamaServiceConfig(**self.OLLAMA)
        except (TypeError, ValueError) as e:
            errors.append(f"OLLAMA validation failed: {e}")
        
        if errors:
            raise ValueError("LLM services config validation errors:\n" + "\n".join(errors))


@dataclass
class ActionConfig:
    """Dataclass for validating individual action configuration (DIACRITICS, SUMMARIZE, etc.)."""
    DESC: str
    PROMPT: str
    CHUNKERS: List[str]
    INPUT_LANGUAGE: str
    
    def __post_init__(self) -> None:
        errors = []
        
        # Validate description
        if not isinstance(self.DESC, str) or not self.DESC:
            errors.append("DESC must be a non-empty string")
        
        # Validate prompt
        if not isinstance(self.PROMPT, str) or not self.PROMPT:
            errors.append("PROMPT must be a non-empty string")
        
        # Validate chunkers list (empty list is valid and means no chunking)
        if not isinstance(self.CHUNKERS, list):
            errors.append("CHUNKERS must be a list")
        else:
            # Empty list is valid (no chunking), but if not empty, all items must be non-empty strings
            for chunker in self.CHUNKERS:
                if not isinstance(chunker, str) or not chunker:
                    errors.append("CHUNKERS must contain only non-empty strings")
                    break
        
        # Validate INPUT_LANGUAGE (must be non-empty string)
        if not isinstance(self.INPUT_LANGUAGE, str) or not self.INPUT_LANGUAGE:
            errors.append("INPUT_LANGUAGE must be a non-empty string")
        
        if errors:
            raise ValueError("Action config validation errors:\n" + "\n".join(errors))


class TextActionsConfigData:
    """Validator for text action configurations - dynamically validates any task from JSON.
    
    This class validates that each task in the config has the required structure:
    - DESC: non-empty string
    - PROMPT: non-empty string  
    - CHUNKERS: list of strings
    - INPUT_LANGUAGE: non-empty string (e.g., 'ro', 'en')
    
    Tasks are discovered dynamically from the JSON file. No need to update this class
    when adding new tasks - just add to text_actions_config.json.
    
    Note: Validation against chunker registry and processor factory happens during
    startup, not during config loading.
    """
    
    def __init__(self, **kwargs) -> None:
        """Initialize and validate task configurations from JSON.
        
        Args:
            **kwargs: Task configurations (e.g., DIACRITICS={...}, CUSTOM={...})
        """
        errors = []
        self._tasks = {}  # Store tasks in dict for easy conversion to DotDict
        
        # Validate each task in the config
        for task_name, task_data in kwargs.items():
            try:
                # Check it's a dictionary
                if not isinstance(task_data, dict):
                    errors.append(f"{task_name} must be a dictionary")
                else:
                    # Validate structure using ActionConfig
                    ActionConfig(**task_data)
                    # Store in _tasks dict
                    self._tasks[task_name] = task_data
                    
            except (TypeError, ValueError) as e:
                errors.append(f"{task_name} validation failed: {e}")
        
        if errors:
            raise ValueError("Text actions config validation errors:\n" + "\n".join(errors))