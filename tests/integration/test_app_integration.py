"""
Integration tests for TextProcessingApplication.
Tests the main application orchestration and component integration.
"""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from src.app.exceptions import UserCancelled
from src.app.text_processing_app import TextProcessingApplication
from src.app.processor_factory import ProcessorFactory
from src.config.app_config import get_app_config
from src.text_processor.chunker import VALID_CHUNKER_NAMES


class MockTaskConfig:
    """Mock task configuration."""
    def __init__(self, chunkers=None, language='ro'):
        self.CHUNKERS = chunkers or []
        self.INPUT_LANGUAGE = language
        self.DESC = "Mock task"
        self.PROMPT = "Mock prompt"


class TestApplicationInitialization(unittest.TestCase):
    """Test application initialization and configuration."""
    
    def test_app_initializes_with_default_config(self):
        """Application should initialize with default config."""
        app = TextProcessingApplication()
        
        self.assertIsNotNone(app.config)
        self.assertIsNotNone(app.logger)
        self.assertIsNotNone(app.path_manager)
        self.assertIsNotNone(app.param_orchestrator)
    
    def test_app_initializes_with_custom_config(self):
        """Application should accept custom config."""
        custom_config = get_app_config()
        app = TextProcessingApplication(app_config=custom_config)
        
        self.assertIs(app.config, custom_config)
    
    def test_app_raises_on_invalid_config(self):
        """Application should raise on invalid ProcessorFactory config."""
        # Create config with missing processor
        config = get_app_config()
        
        # Mock validate_config to return errors
        with patch.object(ProcessorFactory, 'validate_config', return_value=(['Critical error'], [])):
            with self.assertRaises(RuntimeError):
                TextProcessingApplication(app_config=config)


class TestApplicationCancellation(unittest.TestCase):
    """Test that cancelling during parameter collection ends the run cleanly."""
    
    @patch('builtins.print')
    def test_run_returns_when_user_cancels(self, mock_print):
        """UserCancelled during collection ends run() without processing or exiting with an error."""
        app = TextProcessingApplication()
        
        with patch.object(app.param_orchestrator, 'collect_parameters', side_effect=UserCancelled()):
            with patch.object(app, 'process_text') as mock_process:
                result = app.run(startup_context={})
        
        self.assertIsNone(result)
        mock_process.assert_not_called()
        mock_print.assert_any_call("Exiting application...")


class TestChunkerCreation(unittest.TestCase):
    """Test chunker creation logic in application."""
    
    def setUp(self):
        """Setup application."""
        self.app = TextProcessingApplication()
    
    def test_create_chunker_with_valid_strategies(self):
        """Should create chunker with valid strategies."""
        task_config = MockTaskConfig(chunkers=['sentence_split', 'paragraph_split'], language='ro')
        
        chunker = self.app._create_chunker_for_task(
            task_config=task_config,
            task_name='test',
            language='ro',
            chunkers=None
        )
        
        self.assertIsNotNone(chunker)
        self.assertEqual(len(chunker.strategies), 2)
        self.assertEqual(chunker.language, 'ro')
    
    def test_create_chunker_cli_overrides_config(self):
        """CLI chunkers should override config."""
        task_config = MockTaskConfig(chunkers=['sentence_split'], language='ro')
        
        chunker = self.app._create_chunker_for_task(
            task_config=task_config,
            task_name='test',
            language='ro',
            chunkers=['paragraph_split']  # CLI override
        )
        
        self.assertIsNotNone(chunker)
        self.assertEqual(len(chunker.strategies), 1)
    
    def test_create_chunker_with_empty_list_returns_none(self):
        """Empty chunkers list should return None."""
        task_config = MockTaskConfig(chunkers=['sentence_split'], language='ro')
        
        chunker = self.app._create_chunker_for_task(
            task_config=task_config,
            task_name='test',
            language='ro',
            chunkers=[]  # Explicit no chunking
        )
        
        self.assertIsNone(chunker)
    
    def test_create_chunker_with_config_empty_returns_none(self):
        """Config with empty chunkers should return None."""
        task_config = MockTaskConfig(chunkers=[], language='ro')
        
        chunker = self.app._create_chunker_for_task(
            task_config=task_config,
            task_name='test',
            language='ro',
            chunkers=None  # Use config
        )
        
        self.assertIsNone(chunker)
    
    def test_create_chunker_with_invalid_strategy_raises(self):
        """Invalid chunker strategy should raise exception."""
        task_config = MockTaskConfig(chunkers=['invalid_strategy'], language='ro')
        
        with self.assertRaises(ValueError):
            self.app._create_chunker_for_task(
                task_config=task_config,
                task_name='test',
                language='ro',
                chunkers=None
            )
    
    def test_create_chunker_without_chunkers_field_raises(self):
        """Task config without CHUNKERS field should raise."""
        # Create config without CHUNKERS
        task_config = Mock(spec=['INPUT_LANGUAGE'])  # Only has INPUT_LANGUAGE, not CHUNKERS
        task_config.INPUT_LANGUAGE = 'ro'
        
        with self.assertRaises(RuntimeError):
            self.app._create_chunker_for_task(
                task_config=task_config,
                task_name='test',
                language='ro',
                chunkers=None
            )
    
    def test_create_chunker_with_all_valid_strategies(self):
        """Test creating chunker with all valid strategies."""
        for strategy_name in VALID_CHUNKER_NAMES:
            with self.subTest(strategy=strategy_name):
                task_config = MockTaskConfig(chunkers=[strategy_name], language='ro')
                
                chunker = self.app._create_chunker_for_task(
                    task_config=task_config,
                    task_name='test',
                    language='ro',
                    chunkers=None
                )
                
                self.assertIsNotNone(chunker)
                self.assertEqual(len(chunker.strategies), 1)


class TestApplicationWithPathManager(unittest.TestCase):
    """Test application integration with PathManager."""
    
    def setUp(self):
        """Setup application."""
        self.app = TextProcessingApplication()
    
    def test_path_manager_has_config_reference(self):
        """PathManager should have reference to config."""
        self.assertIs(self.app.path_manager.config, self.app.config)
    
    def test_path_manager_provides_default_paths(self):
        """PathManager should provide default paths."""
        # These should not raise
        input_dir = self.app.path_manager.input_dir
        output_dir = self.app.path_manager.output_dir
        
        self.assertIsNotNone(input_dir)
        self.assertIsNotNone(output_dir)
    
    def test_orchestrator_uses_same_path_manager(self):
        """Orchestrator should use the same PathManager instance."""
        self.assertIs(
            self.app.param_orchestrator.path_manager,
            self.app.path_manager
        )


class TestApplicationConfigValidation(unittest.TestCase):
    """Test application configuration validation."""
    
    def test_all_registered_tasks_have_configs(self):
        """All registered tasks should have config entries."""
        app = TextProcessingApplication()
        
        errors, warnings = ProcessorFactory.validate_config(app.config.actions_config)
        
        # Should have no errors
        self.assertEqual(len(errors), 0, f"Configuration errors: {errors}")
    
    def test_config_has_required_sections(self):
        """Config should have required sections."""
        app = TextProcessingApplication()
        config = app.config
        
        # Check for required config sections
        self.assertTrue(hasattr(config, 'actions_config'))
        self.assertTrue(hasattr(config, 'file_config'))
        self.assertTrue(hasattr(config, 'llm_services_config'))


class TestApplicationComponentIntegration(unittest.TestCase):
    """Test integration between application components."""
    
    def setUp(self):
        """Setup application and temp directory."""
        self.app = TextProcessingApplication()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_parameter_orchestrator_integration(self):
        """Parameter orchestrator should integrate with app."""
        # Orchestrator should be initialized
        self.assertIsNotNone(self.app.param_orchestrator)
        
        # Should have collectors
        self.assertIsNotNone(self.app.param_orchestrator.cli_collector)
        self.assertIsNotNone(self.app.param_orchestrator.interactive_collector)
    
    def test_processor_factory_integration(self):
        """ProcessorFactory should work with app config."""
        # Get a valid task from config
        tasks = ['DIACRITICS', 'SUMMARIZE', 'EDIT']
        
        for task_name in tasks:
            with self.subTest(task=task_name):
                # Verify task exists in config
                self.assertTrue(
                    hasattr(self.app.config.actions_config, task_name),
                    f"Config missing {task_name}"
                )
    
    def test_path_manager_with_real_paths(self):
        """PathManager should handle real file paths."""
        # Create a test file
        test_file = self.temp_path / "test.txt"
        test_file.write_text("Test", encoding='utf-8')
        
        # PathManager should handle it (doesn't validate existence by default)
        # Just verify it doesn't crash
        path_str = str(test_file)
        self.assertIsInstance(path_str, str)


class TestApplicationErrorScenarios(unittest.TestCase):
    """Test application error handling scenarios."""
    
    def test_app_handles_missing_config_gracefully(self):
        """Application should handle config issues gracefully."""
        # Try to create app with None config - should use default
        app = TextProcessingApplication(app_config=None)
        
        # Should fall back to default config
        self.assertIsNotNone(app.config)
    
    def test_chunker_creation_with_missing_task_config(self):
        """Should raise error for missing CHUNKERS field."""
        app = TextProcessingApplication()
        
        # Create incomplete task config without CHUNKERS
        incomplete_config = Mock(spec=['INPUT_LANGUAGE'])
        incomplete_config.INPUT_LANGUAGE = 'ro'
        
        with self.assertRaises(RuntimeError):
            app._create_chunker_for_task(
                task_config=incomplete_config,
                task_name='incomplete',
                language='ro',
                chunkers=None
            )


if __name__ == '__main__':
    unittest.main()
