"""
Startup Manager for Romanian Text Editor
Handles phased application initialization following Python startup conventions
"""

from __future__ import annotations

from typing import Dict, Any, Optional, TYPE_CHECKING, NoReturn
from enum import Enum
import sys
from pathlib import Path

if TYPE_CHECKING:
    from src.config.app_config import AppConfig
    from src.utils.app_logger import StartupLogger, AppLogger

# Import logger and appconfig getter functions
from src.config.app_config import get_app_config
from src.utils.app_logger import StartupLogger, get_startup_logger, get_logger


class StartupPhase(Enum):
    """Enum for tracking startup phases to prevent typos and improve type safety."""
    BOOTSTRAP_VALIDATED = "bootstrap_validated"
    LOGGING_INITIALIZED = "logging_initialized" 
    CONFIG_LOADED = "config_loaded"
    APP_LOGGING_READY = "app_logging_ready"
    STARTUP_COMPLETE = "startup_complete"


class StartupManager:
    """
    Manages the phased startup of the Romanian Text Editor application.
    Follows Python application startup conventions with proper phases.
    """

    def __init__(self, app_name: str = "RomanianTextEditor"):
        """Initialize startup manager with application name."""
        self.app_name = app_name
        self.startup_logger: Optional["StartupLogger"] = None
        self.app_logger: Optional["AppLogger"] = None
        self.app_config: Optional["AppConfig"] = None
        self.ollama_running: bool = False  # Track Ollama service status
        self._initialized_phases = set()
        self._startup_successful = False

    def phase_1_bootstrap_validation(self) -> StartupManager:
        """
        Phase 1: Validates runtime environment conditions not checked by Python's import mechanism.
        """
        try:
            # 1. Python version check (runtime requirement)
            self._validate_python_version()
            
            # 2. File system write access (runtime permission)
            self._validate_file_permissions()
            
            self._initialized_phases.add(StartupPhase.BOOTSTRAP_VALIDATED)
            return self
            
        except Exception as e:
            print(f"CRITICAL BOOTSTRAP FAILURE: {e}", file=sys.stderr)
            self._emergency_exit(1, str(e))

    def phase_2_initialize_logging(self) -> StartupManager:
        """
        Phase 2: Initialize startup logger
        """
        self._require_phase(StartupPhase.BOOTSTRAP_VALIDATED, "Bootstrap validation required")
        
        try:
            self.startup_logger = get_startup_logger()
            self.startup_logger.debug(f"Starting {self.app_name} application...")

            self._initialized_phases.add(StartupPhase.LOGGING_INITIALIZED)
            return self
            
        except Exception as e:
            print(f"CRITICAL: Logging initialization failed: {e}", file=sys.stderr)
            self._emergency_exit(2, f"Logging failed: {e}")

    def phase_3_load_configs(self) -> StartupManager:
        """
        Phase 3: Load application configuratio (AppConfig), using the startup logger for logging.
        """
        self._require_phase(StartupPhase.LOGGING_INITIALIZED, "Logging must be initialized first")
        
        try:
            # Load full application configuration
            self.app_config = get_app_config(logger=self.startup_logger)
            
            if not self.app_config.load_success:
                raise RuntimeError("Configuration loading failed - check startup logs")
            
            self._initialized_phases.add(StartupPhase.CONFIG_LOADED)
            if self.startup_logger:
                self.startup_logger.debug("Phase 3 (Configuration Loading) completed")
            return self
            
        except Exception as e:
            if self.startup_logger:
                self.startup_logger.error(f"Configuration loading failed: {e}")
            else:
                print(f"Configuration loading failed: {e}", file=sys.stderr)
            self._emergency_exit(3, f"Configuration loading failed: {e}")

    def phase_4_setup_logging(self) -> StartupManager:
        """
        Phase 4: Setup full application logging.
        This transfers startup logs to the main application logger.
        """
        self._require_phase(StartupPhase.CONFIG_LOADED, "Configuration must be loaded first")
        
        try:
            if self.startup_logger:
                self.startup_logger.debug("Setting up application logging...")
            
            # Get the main application logger (this will transfer startup logs)
            self.app_logger = get_logger(f'{self.app_name}.App')
            
            # Log successful transition
            self.app_logger.debug(f"Application logging initialized for {self.app_name}")
            self.app_logger.debug("Startup logs have been transferred to application logger")
            
            self._initialized_phases.add(StartupPhase.APP_LOGGING_READY)
            self.app_logger.debug("Phase 4 (Application Logging Setup) completed")
            return self
            
        except Exception as e:
            if self.startup_logger:
                self.startup_logger.error(f"Logging setup failed: {e}")
            else:
                print(f"Logging setup failed: {e}", file=sys.stderr)
            self._emergency_exit(4, f"Logging setup failed: {e}")

    def phase_5_finalize_startup(self) -> StartupManager:
        """
        Phase 5: Finalize startup process.
        Validate final environment requirements and mark startup complete.
        """
        self._require_phase(StartupPhase.APP_LOGGING_READY, "Application logging setup required")
        
        try:
            if self.app_logger:
                self.app_logger.debug("Finalizing application startup...")
            
            # Validate dependencies (if any external deps are required)
            self._validate_dependencies()
            
            # Check Ollama service availability (one-time check at startup)
            self._check_ollama_service()
            
            # Mark startup as successful
            self._startup_successful = True
            self._initialized_phases.add(StartupPhase.STARTUP_COMPLETE)
            
            if self.app_logger:
                self.app_logger.debug(f"{self.app_name} startup completed successfully")
            return self
            
        except Exception as e:
            if self.app_logger:
                self.app_logger.error(f"Startup finalization failed: {e}")
            else:
                print(f"Startup finalization failed: {e}", file=sys.stderr)
            self._emergency_exit(5, f"Startup finalization failed: {e}")

    def get_application_context(self) -> Dict[str, Any]:
        """
        Get the fully initialized application context.
        This should only be called after successful startup.
        """
        if not self._startup_successful:
            raise RuntimeError("Application startup not completed successfully")
            
        return {
            "app_name": self.app_name,
            "app_config": self.app_config,
            "logger": self.app_logger,
            "startup_logger": self.startup_logger,
            "ollama_running": self.ollama_running,
            "initialized_phases": self._initialized_phases.copy()
        }

    def create_text_processing_app(self) -> Optional[Any]:
        """
        Create and return a configured TextProcessingApplication instance.
        Only available after successful startup.
        """
        context = self.get_application_context()
        
        try:
            # Import here to avoid circular imports during startup
            from src.app.text_processing_app import TextProcessingApplication
            # Don't pass logger - let TextProcessingApplication create its own RomanianTextEditor.App logger
            return TextProcessingApplication(
                app_config=context["app_config"]
            )
        except ImportError as e:
            if self.app_logger:
                self.app_logger.warning(f"TextProcessingApplication not available: {e}")
            else:
                print(f"Warning: TextProcessingApplication not available: {e}")
            return None

    # Helper methods for startup phases
    def _require_phase(self, required_phase: StartupPhase, error_message: str) -> None:
        """Ensure a required phase has been completed."""
        if required_phase not in self._initialized_phases:
            raise RuntimeError(error_message)

    def _validate_python_version(self) -> None:
        """Validate Python version meets requirements."""
        if sys.version_info < (3, 7):
            raise RuntimeError(f"Python 3.7+ required, got {sys.version_info}")

    def _validate_file_permissions(self) -> None:
        """Validate file system permissions (works in both bootstrap and regular phases)."""
        # Test write access to current directory
        test_file = Path("file_access_test.tmp")
        try:
            test_file.write_text("test")
            test_file.unlink()
            # Only log if we have an app logger available (not in bootstrap phase)
            if self.app_logger:
                self.app_logger.debug("File write permissions validated")
        except Exception as e:
            raise RuntimeError(f"Insufficient file permissions: {e}")

    def _validate_dependencies(self) -> None:
        """Validate external dependencies if any."""
        # Add dependency validation logic here if needed
        if self.app_logger:
            self.app_logger.debug("Dependencies validation completed")

    def _check_ollama_service(self) -> None:
        """Check if Ollama service is running (one-time startup check with warning).
        
        Returns the status and stores it in instance variable for later display.
        """
        try:
            from src.services import get_ollama_service
            
            ollama_service = get_ollama_service()
            is_running = ollama_service.is_ollama_running()
            
            # Store status in instance variable for later display
            self.ollama_running = is_running
            
            if is_running:
                if self.app_logger:
                    self.app_logger.debug("✓ Ollama startup validation passed")
            else:
                # Warning only - give user time to start Ollama during parameter collection
                warning_msg = (
                    "⚠ WARNING: Ollama service is not currently running.\n"
                    "   Please start Ollama to enable text processing.\n"
                    "   The application will check again before processing begins."
                )
                if self.app_logger:
                    self.app_logger.debug("Ollama service not running at startup")
                print(warning_msg)
        except Exception as e:
            # Log error but don't fail startup - will be checked again before processing
            self.ollama_running = False
            error_msg = f"Could not check Ollama service status: {e}"
            if self.app_logger:
                self.app_logger.warning(error_msg)
            print(f"Warning: {error_msg}")

    # Bootstrap validation methods (no logging dependencies)
    def _emergency_exit(self, exit_code: int, message: str) -> NoReturn:
        """Emergency exit with proper cleanup."""
        error_msg = f"EMERGENCY EXIT ({exit_code}): {message}"
        
        if self.app_logger:
            self.app_logger.critical(error_msg)
        elif self.startup_logger:
            self.startup_logger.critical(error_msg)
            # The buffered startup messages would otherwise be lost
            StartupLogger.dump_to_file(error_msg)
        else:
            print(error_msg, file=sys.stderr)
            
        sys.exit(exit_code)


def initialize_application(app_name: str = "RomanianTextEditor") -> StartupManager:
    """
    Convenience function to initialize the application through all phases.
    Returns the fully initialized StartupManager instance.
    Args:
        app_name (str): Name of the application.    
    Returns:
        StartupManager: Fully initialized startup manager with all phases completed.
                       Call .get_application_context() or .create_text_processing_app()
                       on the returned instance.
    """
    startup_manager = StartupManager(app_name)
    
    # Execute all startup phases
    (startup_manager
     .phase_1_bootstrap_validation()
     .phase_2_initialize_logging()
     .phase_3_load_configs()
     .phase_4_setup_logging()
     .phase_5_finalize_startup())
    
    return startup_manager

if __name__ == "__main__":
    # Simple test run of the startup manager
    try:
        startup_manager = initialize_application("TestApp")
        context = startup_manager.get_application_context()
        logger = context.get("logger")
        if logger:
            logger.debug("Application initialized successfully in test mode")
            logger.debug(f"Application context: {list(context.keys())}")
        else:
            print("Application initialized successfully in test mode, but no logger available")
            print(f"Application context: {list(context.keys())}")
    except Exception as e:
        print(f"Startup failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)