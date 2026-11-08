"""
Unit tests for app_logger module.
"""

import logging
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.config.app_config import AppLoaderConfig
from src.utils.app_logger import (
    AppLogger,
    StartupLogger,
    get_startup_logger,
    get_logger,
    get_logger_summary
    # Note: reset_loggers may not be exported - tests will verify current behavior
)


class TestAppLogger(unittest.TestCase):
    """Test cases for app_logger module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Note: If reset_loggers is available, uncomment the line below
        # reset_loggers()
        pass
    
    def tearDown(self):
        """Clean up after tests."""
        # Note: If reset_loggers is available, uncomment the line below
        # reset_loggers()
        pass
    
    def test_startup_logger_singleton(self):
        """Test that startup logger returns the same instance."""
        logger1 = get_startup_logger()
        logger2 = get_startup_logger()
        
        self.assertIs(logger1, logger2, "Startup logger should be a singleton")
    
    def test_app_logger_singleton_by_name(self):
        """Test that app loggers with same name return same instance."""
        logger1 = get_logger("TestLogger")
        logger2 = get_logger("TestLogger")
        
        self.assertIs(logger1, logger2, "App loggers with same name should be same instance")
    
    def test_logger_summary(self):
        """Test logger summary functionality."""
        get_startup_logger()
        get_logger("TestLogger1")
        get_logger("TestLogger2")
        get_logger("TestLogger3")
        
        summary = get_logger_summary()
        
        self.assertTrue(summary['startup_logger_loaded'], "Startup logger should be loaded")
        self.assertGreaterEqual(summary['num_app_loggers'], 3, "At least three app loggers should exist")
        self.assertIn("TestLogger1", summary['app_logger_names'])
        self.assertIn("TestLogger2", summary['app_logger_names'])
        self.assertIn("TestLogger3", summary['app_logger_names'])
    
    def test_app_logger_has_required_methods(self):
        """Test that app logger has required logging methods."""
        logger = get_logger("TestLogger")
        
        self.assertTrue(hasattr(logger, 'debug'))
        self.assertTrue(hasattr(logger, 'info'))
        self.assertTrue(hasattr(logger, 'warning'))
        self.assertTrue(hasattr(logger, 'error'))
        self.assertTrue(hasattr(logger, 'critical'))
        self.assertTrue(callable(logger.debug))
        self.assertTrue(callable(logger.info))
    
    def test_logger_can_log_without_errors(self):
        """Test that loggers can log messages without errors."""
        startup_logger = get_startup_logger()
        app_logger = get_logger("TestLogger")
        
        # These should not raise exceptions
        try:
            startup_logger.debug("Test debug message")
            startup_logger.info("Test info message")
            app_logger.debug("Test debug message")
            app_logger.warning("Test warning message")
            app_logger.error("Test error message")
        except Exception as e:
            self.fail(f"Logging raised an exception: {e}")


class TestLoggerPaths(unittest.TestCase):
    """Test where the loggers read and write their files."""

    def test_log_dir_comes_from_logs_dir_setting(self):
        """The logs folder is taken from ESSENTIAL_DIRS.LOGS_DIR in file_config.json."""
        config = Mock()
        config.logging_config = SimpleNamespace(LOG_TO_CONSOLE=False, LOG_TO_FILE=False)
        config.file_config = SimpleNamespace(
            ESSENTIAL_DIRS={"LOGS_DIR": "custom_logs"}, DEFAULT_ENCODING="utf-8"
        )

        logger = AppLogger(name="LogDirTest", config=config)

        self.assertEqual(logger.log_dir, "custom_logs")

    def test_startup_dump_is_written_to_project_root(self):
        """Emergency dumps go to BASE_DIR, where AppLogger looks for them later."""
        record = logging.LogRecord("startup", logging.ERROR, __file__, 1, "boom", None, None)

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(AppLoaderConfig, 'BASE_DIR', Path(temp_dir)):
                with patch.object(StartupLogger, '_buffer', [record]):
                    with patch('builtins.print'):
                        StartupLogger.dump_to_file("test failure")

            dumps = list(Path(temp_dir).glob("startup_errors_*.log"))
            self.assertEqual(len(dumps), 1)
            self.assertIn("boom", dumps[0].read_text(encoding="utf-8"))


if __name__ == '__main__':
    unittest.main()
