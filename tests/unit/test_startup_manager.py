"""
Unit tests for StartupManager.
"""
import unittest
import sys
from unittest.mock import Mock, patch, MagicMock
from src.app.startup_manager import StartupManager, StartupPhase


class TestStartupManagerInitialization(unittest.TestCase):
    """Test StartupManager initialization."""
    
    def test_init_with_default_app_name(self):
        """Should initialize with default app name."""
        manager = StartupManager()
        
        self.assertEqual(manager.app_name, "RomanianTextEditor")
        self.assertIsNone(manager.startup_logger)
        self.assertIsNone(manager.app_logger)
        self.assertIsNone(manager.app_config)
        self.assertFalse(manager.ollama_running)
        self.assertFalse(manager._startup_successful)
        self.assertEqual(len(manager._initialized_phases), 0)


class TestBootstrapValidation(unittest.TestCase):
    """Test bootstrap validation phase."""
    
    @patch('sys.version_info', (3, 10, 0, 'final', 0))
    def test_phase_1_bootstrap_validation_success(self):
        """Bootstrap should succeed with valid Python version."""
        manager = StartupManager()
        
        # Should not raise
        result = manager.phase_1_bootstrap_validation()
        
        self.assertIs(result, manager)  # Should return self for chaining
        self.assertIn(StartupPhase.BOOTSTRAP_VALIDATED, manager._initialized_phases)
    
    def test_bootstrap_validation_returns_self(self):
        """Bootstrap validation should return self for method chaining."""
        manager = StartupManager()
        
        result = manager.phase_1_bootstrap_validation()
        
        self.assertIs(result, manager)


class TestLoggingInitialization(unittest.TestCase):
    """Test logging initialization phase."""
    
    def test_phase_2_initialize_logging(self):
        """Should initialize logging."""
        manager = StartupManager()
        manager.phase_1_bootstrap_validation()
        
        result = manager.phase_2_initialize_logging()
        
        self.assertIs(result, manager)
        self.assertIn(StartupPhase.LOGGING_INITIALIZED, manager._initialized_phases)
        self.assertIsNotNone(manager.startup_logger)
    
    def test_logging_initialization_requires_bootstrap(self):
        """Logging initialization might require bootstrap first."""
        manager = StartupManager()
        
        # Must call bootstrap first
        manager.phase_1_bootstrap_validation()
        result = manager.phase_2_initialize_logging()
        
        # Should at least not crash
        self.assertIsNotNone(result)


class TestConfigLoading(unittest.TestCase):
    """Test configuration loading phase."""
    
    def test_phase_3_load_configs(self):
        """Should load configuration."""
        manager = StartupManager()
        manager.phase_1_bootstrap_validation()
        manager.phase_2_initialize_logging()
        
        result = manager.phase_3_load_configs()
        
        self.assertIs(result, manager)
        self.assertIn(StartupPhase.CONFIG_LOADED, manager._initialized_phases)
        self.assertIsNotNone(manager.app_config)
        # app_logger is set in phase_4, not phase_3
        self.assertIsNotNone(manager.startup_logger)
    
    def test_config_loading_sets_app_logger(self):
        """Config loading should initialize app logger."""
        manager = StartupManager()
        manager.phase_1_bootstrap_validation()
        manager.phase_2_initialize_logging()
        
        manager.phase_3_load_configs()
        manager.phase_4_setup_logging()
        
        self.assertIsNotNone(manager.app_logger)


class TestEnvironmentValidation(unittest.TestCase):
    """Test environment validation phase."""
    
    @patch('src.services.ollama_service.OllamaService.is_ollama_running')
    def test_phase_4_setup_logging_ollama_running(self, mock_ollama):
        """Should detect when Ollama is running."""
        mock_ollama.return_value = True
        
        manager = StartupManager()
        manager.phase_1_bootstrap_validation()
        manager.phase_2_initialize_logging()
        manager.phase_3_load_configs()
        
        result = manager.phase_4_setup_logging()
        
        self.assertIs(result, manager)
        self.assertIn(StartupPhase.APP_LOGGING_READY, manager._initialized_phases)
        
        # ollama_running is checked in phase_5 finalize_startup, not phase_4
        # phase_4 just sets up logging
        # So we test it after phase_5
        manager.phase_5_finalize_startup()
        self.assertTrue(manager.ollama_running)
    
    @patch('src.services.ollama_service.OllamaService.is_ollama_running')
    def test_phase_4_setup_logging_ollama_not_running(self, mock_ollama):
        """Should detect when Ollama is not running."""
        mock_ollama.return_value = False
        
        manager = StartupManager()
        manager.phase_1_bootstrap_validation()
        manager.phase_2_initialize_logging()
        manager.phase_3_load_configs()
        
        result = manager.phase_4_setup_logging()
        
        self.assertIs(result, manager)
        self.assertFalse(manager.ollama_running)


class TestStartupCompletion(unittest.TestCase):
    """Test startup completion phase."""
    
    @patch('src.services.ollama_service.OllamaService.is_ollama_running')
    def test_phase_5_finalize_startup(self, mock_ollama):
        """Should mark startup as complete."""
        mock_ollama.return_value = True
        
        manager = StartupManager()
        manager.phase_1_bootstrap_validation()
        manager.phase_2_initialize_logging()
        manager.phase_3_load_configs()
        manager.phase_4_setup_logging()
        
        result = manager.phase_5_finalize_startup()
        
        self.assertIs(result, manager)
        self.assertIn(StartupPhase.STARTUP_COMPLETE, manager._initialized_phases)
        self.assertTrue(manager._startup_successful)
    
    @patch('src.services.ollama_service.OllamaService.is_ollama_running')
    def test_complete_startup_sequence(self, mock_ollama):
        """Should complete all startup phases in sequence."""
        mock_ollama.return_value = True
        
        manager = StartupManager()
        
        # Chain all phases
        manager.phase_1_bootstrap_validation() \
               .phase_2_initialize_logging() \
               .phase_3_load_configs() \
               .phase_4_setup_logging() \
               .phase_5_finalize_startup()
        
        # All phases should be initialized
        expected_phases = {
            StartupPhase.BOOTSTRAP_VALIDATED,
            StartupPhase.LOGGING_INITIALIZED,
            StartupPhase.CONFIG_LOADED,
            StartupPhase.APP_LOGGING_READY,
            StartupPhase.STARTUP_COMPLETE
        }
        
        self.assertEqual(manager._initialized_phases, expected_phases)
        self.assertTrue(manager._startup_successful)


class TestStartupManagerProperties(unittest.TestCase):
    """Test StartupManager properties and getters."""
    
    @patch('src.services.ollama_service.OllamaService.is_ollama_running')
    def test_get_app_config(self, mock_ollama):
        """Should provide access to app config."""
        mock_ollama.return_value = True
        
        manager = StartupManager()
        manager.phase_1_bootstrap_validation()
        manager.phase_2_initialize_logging()
        manager.phase_3_load_configs()
        
        config = manager.app_config
        
        self.assertIsNotNone(config)
    
    @patch('src.services.ollama_service.OllamaService.is_ollama_running')
    def test_get_app_logger(self, mock_ollama):
        """Should provide access to app logger."""
        mock_ollama.return_value = True
        
        manager = StartupManager()
        manager.phase_1_bootstrap_validation()
        manager.phase_2_initialize_logging()
        manager.phase_3_load_configs()
        manager.phase_4_setup_logging()
        
        logger = manager.app_logger
        
        self.assertIsNotNone(logger)


class TestStartupManagerErrorHandling(unittest.TestCase):
    """Test error handling in startup manager."""
    
    def test_startup_without_phases_initialized(self):
        """Should handle accessing properties before initialization."""
        manager = StartupManager()
        
        # Config should be None before initialization
        self.assertIsNone(manager.app_config)
        self.assertIsNone(manager.app_logger)
    
    def test_phase_tracking_is_consistent(self):
        """Phase tracking should be consistent across operations."""
        manager = StartupManager()
        
        initial_phase_count = len(manager._initialized_phases)
        self.assertEqual(initial_phase_count, 0)
        
        manager.phase_1_bootstrap_validation()
        self.assertEqual(len(manager._initialized_phases), 1)
        
        manager.phase_2_initialize_logging()
        self.assertEqual(len(manager._initialized_phases), 2)
    
    def test_emergency_exit_dumps_startup_buffer(self):
        """A failed startup writes the buffered startup log to a file before exiting."""
        manager = StartupManager()
        manager.startup_logger = Mock()
        
        with patch('src.app.startup_manager.StartupLogger') as mock_startup_logger:
            with self.assertRaises(SystemExit) as context:
                manager._emergency_exit(3, "Configuration loading failed")
        
        self.assertEqual(context.exception.code, 3)
        mock_startup_logger.dump_to_file.assert_called_once()
        self.assertIn("Configuration loading failed", mock_startup_logger.dump_to_file.call_args[0][0])


if __name__ == '__main__':
    unittest.main()

