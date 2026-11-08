"""
app_logger.py - Unified logger classes with module-level singleton storage
Startup Logger: Independent, no config dependencies, hardcoded defaults
App Logger: Depends on AppConfig for full configuration
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.config.app_config import AppLoaderConfig

# --- Custom Log Level ---
VERBOSE_LEVEL = 15
logging.addLevelName(VERBOSE_LEVEL, "VERBOSE")

# --- StartupBufferHandler ---
class StartupBufferHandler(logging.Handler):
    """Handler that buffers messages and shows INFO+ on console."""
    
    def __init__(self, buffer: List[logging.LogRecord], buffer_limit: int) -> None:
        super().__init__()
        self.buffer = buffer
        self.buffer_limit = buffer_limit
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - STARTUP - %(levelname)s - %(message)s')
        self.console_handler.setFormatter(formatter)
    
    def emit(self, record: logging.LogRecord) -> None:
        if len(self.buffer) < self.buffer_limit:
            self.buffer.append(record)
        if record.levelno >= logging.INFO:
            self.console_handler.emit(record)


# --- StartupLogger: Completely independent, no config dependencies ---
class StartupLogger:
    """Lightweight logger for startup phase with hardcoded defaults.
    
    Features:
    - Buffers all messages for later replay to AppLogger
    - Shows INFO+ messages on console
    - Can dump buffer to emergency file if startup fails
    - NO configuration dependencies - completely standalone
    """
    _buffer: List[logging.LogRecord] = []
    _buffer_limit = 50
    _file_prefix = 'startup_errors'
    
    def __init__(self) -> None:
        """Initialize with hardcoded defaults - no config needed."""
        self.logger = logging.getLogger('startup')
        self.logger.setLevel(logging.DEBUG)
        # Clear any existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        # Add buffer handler (also shows INFO+ on console)
        buffer_handler = StartupBufferHandler(self.__class__._buffer, self.__class__._buffer_limit)
        self.logger.addHandler(buffer_handler)
    
    def debug(self, message: str) -> None:
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        self.logger.info(message)
   
    def warning(self, message: str) -> None:
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        self.logger.critical(message)
    
    @classmethod
    def get_buffered_records(cls) -> List[logging.LogRecord]:
        return cls._buffer.copy()
    
    @classmethod
    def clear_buffer(cls) -> None:
        cls._buffer.clear()
    
    @classmethod
    def dump_to_file(cls, error_msg: str) -> None:
        if cls._buffer:
            now = datetime.now().strftime('%Y%m%d_%H%M%S')
            dump_path = AppLoaderConfig.BASE_DIR / f"{cls._file_prefix}_{now}.log"
            try:
                with dump_path.open('w', encoding='utf-8') as f:
                    f.write(f"Startup Error: {error_msg}\n\nLog contents:\n")
                    formatter = logging.Formatter('%(asctime)s - STARTUP - %(levelname)s - %(message)s')
                    for record in cls._buffer:
                        f.write(f"{formatter.format(record)}\n")
                print(f"Emergency log dump created at: {dump_path.absolute()}")
                cls.clear_buffer()
            except Exception as e:
                print(f"Failed to create emergency log dump: {str(e)}")

# --- AppLogger: Depends on AppConfig for full configuration ---
class AppLogger:
    """Full-featured logger that uses AppConfig for configuration.
    
    Features:
    - Loads config from AppConfig (passed as parameter)
    - Console and file handlers with rotation
    - Transfers startup buffer messages on first initialization
    - Processes emergency startup dumps
    - Supports verbose mode: shows VERBOSE-level logs in console, DEBUG only in file
    """
    _startup_logs_transferred = False
    
    def __init__(self, name: str = "TextProcessor", config=None, verbose_mode: bool = False) -> None:
        """Initialize AppLogger with config from AppConfig.
        
        Args:
            name: Logger name for identification
            config: AppConfig instance (optional, will try to load if not provided)
            verbose_mode: Enable verbose mode (shows VERBOSE-level logs in console)
        """
        self.name = name
        self.verbose_mode = verbose_mode
        self.logging_config = None
        self.file_config = None
        self.log_dir = 'logs'
        
        # Get config from parameter or try to load it
        if config is not None:
            self._load_from_config(config)
        else:
            self._try_load_config()
        
        self.logger = self._setup_logger()
        self._transfer_all_startup_logs()
    
    def _load_from_config(self, config) -> None:
        """Load configuration from AppConfig instance."""
        try:
            self.logging_config = config.logging_config
            self.file_config = config.file_config
            if config.file_config and hasattr(config.file_config, 'ESSENTIAL_DIRS') and config.file_config.ESSENTIAL_DIRS:
                self.log_dir = config.file_config.ESSENTIAL_DIRS.get('LOGS_DIR', 'logs')
        except Exception as e:
            # Fallback to defaults if config is invalid
            print(f"Warning: Failed to load config: {e}")
    
    def _try_load_config(self) -> None:
        """Try to load config from AppConfig module (backward compatibility)."""
        try:
            from src.config.app_config import get_app_config
            config = get_app_config()
            self._load_from_config(config)
        except Exception as e:
            # Fallback to defaults if config loading fails
            print(f"Warning: Could not load AppConfig, using defaults: {e}")
   
    def _setup_logger(self) -> logging.Logger:
        """Set up logger with console and file handlers based on config."""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)
        
        # Prevent propagation to parent loggers to avoid duplicate logs
        # when using hierarchical logger names (e.g., RomanianTextEditor.App)
        logger.propagate = False
        
        # Clear any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # If no config available, use basic fallback
        if self.logging_config is None or self.file_config is None:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            return logger
        
        # Console handler
        if self.logging_config.LOG_TO_CONSOLE:
            console_handler = logging.StreamHandler(sys.stdout)
            
            # Set console level based on verbose mode
            if self.verbose_mode:
                # Verbose mode: show VERBOSE and above (but not DEBUG)
                console_level = VERBOSE_LEVEL
            else:
                # Normal mode: show INFO and above
                console_level = getattr(logging, self.logging_config.CONSOLE_LEVEL.upper(), logging.INFO)
            
            console_handler.setLevel(console_level)
            console_formatter = logging.Formatter(
                self.logging_config.CONSOLE_FORMAT,
                datefmt=self.logging_config.DATE_FORMAT
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # File handler
        if self.logging_config.LOG_TO_FILE:
            log_file = self._get_log_file_path()
            log_file.parent.mkdir(exist_ok=True, parents=True)
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.logging_config.LOG_FILE_MAX_SIZE_MB * 1024 * 1024,
                backupCount=self.logging_config.MAX_LOG_FILES,
                encoding=self.file_config.DEFAULT_ENCODING
            )
            file_level = getattr(logging, self.logging_config.FILE_LEVEL.upper(), logging.DEBUG)
            file_handler.setLevel(file_level)
            file_formatter = logging.Formatter(
                self.logging_config.LOG_FORMAT,
                datefmt=self.logging_config.DATE_FORMAT
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _get_log_file_path(self) -> Path:
        """Get the log file path using BASE_DIR from AppLoaderConfig.
        
        Uses either a single shared log file or separate files per logger,
        depending on the USE_SINGLE_LOG_FILE configuration setting.
        """
        if Path(self.log_dir).is_absolute():
            logs_dir = Path(self.log_dir)
        else:
            logs_dir = AppLoaderConfig.BASE_DIR / self.log_dir
        
        # Check if using single file or separate files per logger
        if (self.logging_config and 
            hasattr(self.logging_config, 'USE_SINGLE_LOG_FILE') and 
            self.logging_config.USE_SINGLE_LOG_FILE):
            # Use single shared log file for all loggers
            log_filename = getattr(self.logging_config, 'SINGLE_LOG_FILE_NAME', 'application.log')
        else:
            # Use separate log file per logger (legacy behavior)
            log_filename = f"{self.name.lower()}.log"
        
        return logs_dir / log_filename
    
    def _process_emergency_dumps(self) -> None:
        """Process emergency startup log dumps from the project root directory."""
        emergency_logs = sorted(
            AppLoaderConfig.BASE_DIR.glob(f'{StartupLogger._file_prefix}_*.log'),
            key=lambda x: x.stat().st_mtime
        )
        if emergency_logs:
            self.logger.info(f"Found {len(emergency_logs)} startup emergency log dumps to process")
            for log_file in emergency_logs:
                try:
                    content = log_file.read_text(encoding='utf-8')
                    self.logger.info(f"=== Emergency Startup Log: {log_file.name} ===")
                    for line in content.splitlines():
                        if line.strip():
                            self.logger.info(f"STARTUP-DUMP | {line}")
                    self.logger.info("=== End of Emergency Startup Log ===")
                    log_file.unlink()
                    self.logger.debug(f"Successfully processed and removed startup dump: {log_file.name}")
                except Exception as e:
                    self.logger.error(f"Failed to process startup emergency log {log_file}: {e}")
    
    def _transfer_all_startup_logs(self) -> None:
        if self.__class__._startup_logs_transferred:
            return
        self._process_emergency_dumps()
        startup_records = StartupLogger.get_buffered_records()
        if startup_records:
            self.logger.debug(f"=== Transferring Current Startup Buffer ({len(startup_records)} records) ===")
            for record in startup_records:
                self.logger.handle(record)
            self.logger.debug("=== End of Current Startup Buffer Transfer ===")
            StartupLogger.clear_buffer()
        else:
            self.logger.debug("No startup buffer records to transfer")
        self.__class__._startup_logs_transferred = True
    
    def debug(self, message: str, **kwargs) -> None:
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def verbose(self, message: str, **kwargs) -> None:
        """Log user-facing operational message.
        
        These messages are shown in console when verbose_mode=True,
        and always logged to file. Use for progress updates and
        user-relevant information.
        """
        self._log_with_context(VERBOSE_LEVEL, message, **kwargs)
    
    def set_verbose_mode(self, verbose_mode: bool) -> None:
        """Dynamically update verbose mode by adjusting console handler level.
        
        Args:
            verbose_mode: True to show VERBOSE messages in console, False to hide them
        """
        self.verbose_mode = verbose_mode
        
        # Update console handler level if it exists
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                if verbose_mode:
                    handler.setLevel(VERBOSE_LEVEL)
                    if self.logger:
                        self.logger.debug(f"Console handler level set to VERBOSE for verbose mode")
                else:
                    # Reset to INFO level from config or default
                    if self.logging_config:
                        console_level = getattr(logging, self.logging_config.CONSOLE_LEVEL.upper(), logging.INFO)
                    else:
                        console_level = logging.INFO
                    handler.setLevel(console_level)
                    if self.logger:
                        self.logger.debug(f"Console handler level reset to {logging.getLevelName(console_level)}")
                break
   
    def info(self, message: str, **kwargs) -> None:
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def _log_with_context(self, level: int, message: str, **kwargs) -> None:
        if kwargs:
            message = f"{message} | Context: {kwargs}"
        self.logger.log(level, message)
    
    def exception(self, message: str, exc_info: bool = True, **kwargs) -> None:
        self._log_with_context(logging.ERROR, message, **kwargs)
        if exc_info:
            self.logger.exception(message)
   
    def close(self) -> None:
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

# --- Module-level singleton storage ---
_startup_logger: Optional[StartupLogger] = None
_app_loggers: Dict[str, AppLogger] = {}


# --- Module-level functions ---

def get_startup_logger() -> StartupLogger:
    """Get the StartupLogger instance, creating it if necessary.
    
    This logger is completely independent with no config dependencies.
    Use this during application startup before AppConfig is loaded.
    """
    global _startup_logger
    if _startup_logger is None:
        _startup_logger = StartupLogger()
    return _startup_logger


def get_logger(name: str = "TextProcessor", config=None, verbose_mode: bool = False) -> AppLogger:
    """Get an AppLogger instance, creating it if necessary.
    
    Args:
        name: Logger name for identification
        config: Optional AppConfig instance. If not provided, will try to load it.
                For better control, pass the config explicitly.
        verbose_mode: Enable verbose mode (shows VERBOSE-level logs in console)
    
    Returns:
        AppLogger instance
    """
    if name not in _app_loggers:
        _app_loggers[name] = AppLogger(name=name, config=config, verbose_mode=verbose_mode)
    else:
        # Logger already exists - update verbose mode if different
        existing_logger = _app_loggers[name]
        if existing_logger.verbose_mode != verbose_mode:
            existing_logger.set_verbose_mode(verbose_mode)
    
    return _app_loggers[name]


def get_logger_summary() -> Dict[str, Any]:
    """Get a summary of loaded logger instances for debugging."""
    return {
        "startup_logger_loaded": _startup_logger is not None,
        "num_app_loggers": len(_app_loggers),
        "app_logger_names": list(_app_loggers.keys())
    }


def reset_startup_logger() -> None:
    """Reset the StartupLogger instance for testing."""
    global _startup_logger
    if _startup_logger and hasattr(_startup_logger, 'logger'):
        for handler in list(_startup_logger.logger.handlers):
            try:
                handler.close()
                _startup_logger.logger.removeHandler(handler)
            except Exception:
                pass
    _startup_logger = None


def reset_app_loggers() -> None:
    """Reset all AppLogger instances for testing."""
    for logger in _app_loggers.values():
        if hasattr(logger, 'logger'):
            for handler in list(logger.logger.handlers):
                try:
                    handler.close()
                    logger.logger.removeHandler(handler)
                except Exception:
                    pass
    _app_loggers.clear()


def reset_all_loggers() -> None:
    """Reset all logger instances for testing."""
    reset_startup_logger()
    reset_app_loggers()

if __name__ == "__main__":
    print("Tests have been migrated to tests/unit/test_app_logger.py")
    print("Run: python -m unittest tests.unit.test_app_logger")
    print("Or: python -m unittest discover tests")