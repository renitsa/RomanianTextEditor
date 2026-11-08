"""
app_config.py - Unified config with module-level singleton storage
"""

from pathlib import Path
from dataclasses import asdict
from typing import Dict, Any, Optional

from src.config.config_data_validator import (
    LoggingConfigData, FileConfigData,
    TextProcessingConfigData, LLMServicesConfigData, TextActionsConfigData
)

from src.utils.file_utils import read_json
from src.utils.dict_utils import DotDict


class AppLoaderConfig:
    """Configuration paths and file validation for the application."""
    BASE_DIR = Path(__file__).parent.parent.parent
    CONFIG_DIR = BASE_DIR / "config"
    TEXT_CONFIG_FILE_PATH = CONFIG_DIR / "text_processing_config.json"
    LLM_SERVICES_CONFIG_FILE_PATH = CONFIG_DIR / "llm_services_config.json"
    TEXT_ACTIONS_CONFIG_FILE_PATH = CONFIG_DIR / "text_actions_config.json"
    LOGGING_CONFIG_FILE_PATH = CONFIG_DIR / "logging_config.json"
    FILE_CONFIG_FILE_PATH = CONFIG_DIR / "file_config.json"

    @classmethod
    def validate_all_files_exist(cls, startup_logger=None) -> bool:
        """Check that all configuration files exist.
        
        Args:
            startup_logger: Optional StartupLogger instance for logging validation results
        
        Returns:
            bool: True if all files exist, False otherwise
        """
        if not cls.CONFIG_DIR.exists() or not cls.CONFIG_DIR.is_dir():
            msg = f"Config directory does not exist: {cls.CONFIG_DIR}"
            if startup_logger:
                startup_logger.error(msg)
            else:
                print(f"ERROR: {msg}")
            return False
        
        all_files = [
            cls.LOGGING_CONFIG_FILE_PATH,
            cls.FILE_CONFIG_FILE_PATH,
            cls.TEXT_CONFIG_FILE_PATH,
            cls.LLM_SERVICES_CONFIG_FILE_PATH,
            cls.TEXT_ACTIONS_CONFIG_FILE_PATH
        ]
        
        for path in all_files:
            if not path.exists() or not path.is_file():
                msg = f"Missing config file: {path}"
                if startup_logger:
                    startup_logger.error(msg)
                else:
                    print(f"ERROR: {msg}")
                return False
        
        if startup_logger:
            startup_logger.debug("All required config files found")
        
        return True


class AppConfig:
    """ 
    Application configuration - loads all config files in the proper order.
    """
    
    @staticmethod
    def _process_text_abbreviations(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert abbreviation lists to sets for efficient lookup.
        
        Args:
            data: Raw configuration dictionary
            
        Returns:
            Modified dictionary with abbreviations as sets
        """
        data["COMMON_ENG_ABBREVIATIONS"] = set(data.get("COMMON_ENG_ABBREVIATIONS", []))
        data["COMMON_RO_ABBREVIATIONS"] = set(data.get("COMMON_RO_ABBREVIATIONS", []))
        return data
    
    def __init__(self, logger=None) -> None:
        """Initialize and load all configuration.
        
        Args:
            logger: Optional logger instance for logging during config load.
                   If not provided, will use print statements.
        """
        self.loadercfg = AppLoaderConfig()
        self._logger = logger
        self._load_success = False
        
        # Configuration attributes
        self.logging_config = None
        self.file_config = None
        self.text_config = None
        self.llm_services_config = None
        self.actions_config = None
        
        # Configuration loading specifications
        # Format: attribute_name -> (file_path, dataclass_type, pre_process_fn)
        self.__config_specs = {
            'logging_config': (
                self.loadercfg.LOGGING_CONFIG_FILE_PATH,
                LoggingConfigData,
                None  # pre-process function
            ),
            'file_config': (
                self.loadercfg.FILE_CONFIG_FILE_PATH,
                FileConfigData,
                None
            ),
            'text_config': (
                self.loadercfg.TEXT_CONFIG_FILE_PATH,
                TextProcessingConfigData,
                AppConfig._process_text_abbreviations  # pre-process: convert lists to sets
            ),
            'llm_services_config': (
                self.loadercfg.LLM_SERVICES_CONFIG_FILE_PATH,
                LLMServicesConfigData,
                None
            ),
            'actions_config': (
                self.loadercfg.TEXT_ACTIONS_CONFIG_FILE_PATH,
                TextActionsConfigData,
                None
            )
        }
        
        # Load all configurations
        self.load()
    
    def _log_message(self, level: str, message: str) -> None:
        """Helper to log messages to startup logger or print."""
        if self._logger:
            getattr(self._logger, level.lower())(message)
        else:
            print(f"{level.upper()}: {message}")
    
    def _load_config_file(self, file_path: Path, dataclass_type, post_process=None)->DotDict:
        """Load and validate a single configuration file.
        
        Args:
            file_path: Path to the JSON config file
            dataclass_type: Dataclass type to instantiate (e.g., LoggingConfigData)
            post_process: Optional function to process data before dataclass instantiation
            
        Returns:
            DotDict instance with validated configuration data
        """
        # Derive human-readable config name from file path
        if '_config' in file_path.stem:
            config_name = file_path.stem.replace('_config', '')
        else:
            config_name = file_path.stem
        
        self._log_message("debug", f"Loading {config_name} config from: {file_path}")
        
        # Read JSON file
        data = read_json(file_path)
        if data is None:
            raise RuntimeError(f"No data loaded from {file_path}")
        
        # Apply post-processing if provided
        if post_process:
            data = post_process(data)
        
        # Instantiate and validate dataclass
        try:
            config_instance = dataclass_type(**data)
        except TypeError as e:
            raise RuntimeError(
                f"Invalid {config_name} config structure in {file_path}: {e}"
            ) from e
        
        # Convert to DotDict for flexible access
        # Check if instance has _tasks attribute (for dynamic config classes)
        if hasattr(config_instance, '_tasks'):
            config_dict = DotDict(config_instance._tasks)
        else:
            # Standard dataclass - use asdict()
            config_dict = DotDict(asdict(config_instance))
        
        self._log_message("debug", f"Successfully loaded {config_name} configuration")
        return config_dict
    
    def load(self) -> None:
        """Load all application configuration files using preset configuration."""
        self._log_message("debug", "Loading application configuration")
        
        # Validate all config files exist
        if not self.loadercfg.validate_all_files_exist(startup_logger=self._logger):
            error_msg = "Required config files missing - check config directory"
            self._log_message("critical", error_msg)
            if self._logger and hasattr(self._logger.__class__, 'dump_to_file'):
                self._logger.__class__.dump_to_file(error_msg)
            raise RuntimeError(error_msg)
        
        try:
            # Load all configurations using the specifications
            for attr_name, (file_path, dataclass_type, pre_process) in self.__config_specs.items():
                config_data = self._load_config_file(
                    file_path,
                    dataclass_type,
                    post_process=pre_process  # pre_process happens before dataclass validation
                )
                setattr(self, attr_name, config_data)
                
                # Special case: file_config needs directory setup after loading
                if attr_name == 'file_config' and config_data.ESSENTIAL_DIRS:
                    self._setup_directories(config_data.ESSENTIAL_DIRS)
            
            self._load_success = True
            self._log_message("debug", "All application configuration loaded successfully")
                
        except Exception as e:
            self._load_success = False
            self._log_message("critical", f"Configuration load failed: {e}")
            raise
    
    def _setup_directories(self, directories: Dict[str, str], create_missing: bool = True) -> None:
        """Create necessary directories based on configuration."""
        base_path = self.loadercfg.BASE_DIR
        
        for _, dir_path in directories.items():
            full_path = base_path / dir_path
            
            if not full_path.exists():
                if create_missing:
                    try:
                        full_path.mkdir(parents=True, exist_ok=True)
                        self._log_message("debug", f"Created directory: {full_path}")
                    except Exception as e:
                        self._log_message("error", f"Failed to create directory {full_path}: {e}")
                else:
                    self._log_message("debug", f"Directory does not exist: {full_path}")
            elif not full_path.is_dir():
                self._log_message("warning", f"Path exists but is not a directory: {full_path}")
    
    
    @property
    def load_success(self) -> bool:
        """Check if configuration was loaded successfully."""
        return self._load_success


# --- Module-level singleton storage ---
_app_config: Optional[AppConfig] = None


# --- Module-level functions ---
def get_app_config(logger: Optional[Any] = None) -> AppConfig:
    """Get the AppConfig instance, creating it if necessary.
    
    Args:
        logger: Optional logger instance to use during config loading.
                Can be any logger (StartupLogger, AppLogger, etc.).
                If not provided, AppConfig will use print statements for logging.
    
    Returns:
        AppConfig instance
    """
    global _app_config
    if _app_config is None:
        _app_config = AppConfig(logger=logger)
    return _app_config


def is_app_config_loaded() -> bool:
    """Check if AppConfig has been loaded."""
    return _app_config is not None


def reset_app_config() -> None:
    """Reset the AppConfig singleton for testing purposes.
    
    Properly cleans up the logger if it has a close() method
    (e.g., AppLogger instances).
    """
    global _app_config
    if _app_config and hasattr(_app_config, '_logger') and _app_config._logger:
        # Only close if the logger has a close() method
        if hasattr(_app_config._logger, 'close'):
            _app_config._logger.close()
    _app_config = None


def get_config_summary() -> Dict[str, Any]:
    """Get a summary of loaded configurations for debugging."""
    return {
        "app_config_loaded": _app_config is not None,
        "app_config_id": id(_app_config) if _app_config else None,
        "app_config_load_success": _app_config.load_success if _app_config else False,
    }


if __name__ == "__main__":
    print("Tests have been migrated to tests/unit/test_app_config.py")
    print("Run: python -m unittest tests.unit.test_app_config")
    print("Or: python -m unittest discover tests")
