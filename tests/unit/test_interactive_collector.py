"""
Unit tests for InteractiveParameterCollector.
"""
import unittest
from unittest.mock import Mock, patch
from src.app.exceptions import UserCancelled
from src.app.parameter_collection.interactive_collector import InteractiveParameterCollector
from src.app.path_manager import PathManager


class TestInteractiveCollectorInitialization(unittest.TestCase):
    """Test InteractiveParameterCollector initialization."""
    
    def test_init_with_path_manager_and_logger(self):
        """Should initialize with path manager and optional logger."""
        from src.utils.app_logger import get_logger
        path_manager = PathManager()
        logger = get_logger("Test")
        
        collector = InteractiveParameterCollector(path_manager, logger=logger)
        
        self.assertIs(collector.path_manager, path_manager)
        self.assertIs(collector.logger, logger)
        
    def test_get_task_options_returns_dict(self):
        """Should return dictionary of task options from ProcessorFactory."""
        path_manager = PathManager()
        collector = InteractiveParameterCollector(path_manager)
        
        options = collector._get_task_options()
        
        self.assertIsInstance(options, dict)
        self.assertGreater(len(options), 0, "Should have at least one task")
        # Verify all 6 tasks are present (including 'custom')
        self.assertGreaterEqual(len(options), 6, "Should have all 6 registered tasks")


class TestInteractiveCollectorTaskOptions(unittest.TestCase):
    """Test task option structure."""
    
    def test_task_options_structure(self):
        """Each task option should have name and description."""
        path_manager = PathManager()
        collector = InteractiveParameterCollector(path_manager)
        task_options = collector._get_task_options()
        
        for key, value in task_options.items():
            with self.subTest(key=key):
                self.assertIsInstance(key, int, "Key should be integer")
                self.assertIsInstance(value, tuple, "Value should be tuple")
                self.assertEqual(len(value), 2, "Tuple should have 2 elements")
                self.assertIsInstance(value[0], str, "Task name should be string")
                self.assertIsInstance(value[1], str, "Description should be string")
    
    def test_task_options_include_custom(self):
        """Task options should include the 'custom' task."""
        path_manager = PathManager()
        collector = InteractiveParameterCollector(path_manager)
        task_options = collector._get_task_options()
        
        # Extract all task names from options
        task_names = [task_name for task_name, desc in task_options.values()]
        self.assertIn('custom', task_names, "'custom' task should be available")


class TestCollectTaskInteractive(unittest.TestCase):
    """Test collect_task method."""
    
    def setUp(self):
        """Setup collector."""
        self.path_manager = PathManager()
        self.collector = InteractiveParameterCollector(self.path_manager)
    
    @patch('builtins.input', return_value='1')
    @patch('builtins.print')
    def test_collect_task_valid_selection(self, mock_print, mock_input):
        """Should return task for valid selection."""
        result = self.collector.collect_task()
        
        # Should return first task (get it dynamically)
        task_options = self.collector._get_task_options()
        expected_task = task_options[1][0]
        self.assertEqual(result, expected_task)
    
    @patch('builtins.input', side_effect=['99', '1'])  # Invalid then valid
    @patch('builtins.print')
    def test_collect_task_invalid_then_valid(self, mock_print, mock_input):
        """Should re-prompt on invalid selection."""
        result = self.collector.collect_task()
        
        # Should eventually return valid task
        task_options = self.collector._get_task_options()
        expected_task = task_options[1][0]
        self.assertEqual(result, expected_task)
    
    @patch('builtins.input', side_effect=['abc', '2'])  # Non-numeric then valid
    @patch('builtins.print')
    def test_collect_task_non_numeric_input(self, mock_print, mock_input):
        """Should handle non-numeric input."""
        result = self.collector.collect_task()
        
        task_options = self.collector._get_task_options()
        expected_task = task_options[2][0]
        self.assertEqual(result, expected_task)
    
    @patch('builtins.input', return_value='0')
    @patch('builtins.print')
    def test_collect_task_exit_selection(self, mock_print, mock_input):
        """Should raise UserCancelled on 0 selection."""
        with self.assertRaises(UserCancelled):
            self.collector.collect_task()
    
    @patch('builtins.input', side_effect=KeyboardInterrupt())
    @patch('builtins.print')
    def test_collect_task_keyboard_interrupt(self, mock_print, mock_input):
        """Ctrl+C is treated as a cancellation."""
        with self.assertRaises(UserCancelled):
            self.collector.collect_task()


class TestCollectChunkers(unittest.TestCase):
    """Test collect_chunkers method."""
    
    def test_collect_chunkers_returns_none(self):
        """Interactive collector should always return None for chunkers."""
        path_manager = PathManager()
        collector = InteractiveParameterCollector(path_manager)
        
        result = collector.collect_chunkers()
        
        self.assertIsNone(result)


class TestCollectVerbose(unittest.TestCase):
    """Test collect_verbose method."""
    
    @patch('builtins.input', return_value='n')
    @patch('builtins.print')
    def test_collect_verbose_returns_false(self, mock_print, mock_input):
        """Interactive collector should return False for verbose."""
        path_manager = PathManager()
        collector = InteractiveParameterCollector(path_manager)
        
        result = collector.collect_verbose()
        
        self.assertFalse(result)


class TestCollectModelName(unittest.TestCase):
    """Test collect_model_name method."""
    
    @patch('src.services.ollama_service.OllamaService.is_ollama_running')
    @patch('src.services.ollama_service.OllamaService.get_model_names')
    @patch('builtins.input', return_value='1')
    @patch('builtins.print')
    def test_collect_model_with_available_models(self, mock_print, mock_input,
                                                   mock_get_models, mock_running):
        """Should prompt for model selection when models are available."""
        mock_running.return_value = True
        mock_get_models.return_value = ['jobautomation/OpenEuroLLM-Romanian:latest', 'mistral:7b']
        
        path_manager = PathManager()
        collector = InteractiveParameterCollector(path_manager)
        
        result = collector.collect_model_name()
        
        # Should return a model name
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
    
    @patch('src.services.ollama_service.OllamaService.is_ollama_running')
    @patch('builtins.print')
    def test_collect_model_ollama_not_running(self, mock_print, mock_running):
        """Should exit when Ollama is not running."""
        mock_running.return_value = False
        
        path_manager = PathManager()
        collector = InteractiveParameterCollector(path_manager)
        
        with self.assertRaises(SystemExit):
            collector.collect_model_name()
    
    @patch('src.services.ollama_service.OllamaService.is_ollama_running')
    @patch('src.services.ollama_service.OllamaService.get_model_names')
    @patch('builtins.print')
    def test_collect_model_no_models_available(self, mock_print, mock_get_models, mock_running):
        """Should exit when no models are available."""
        mock_running.return_value = True
        mock_get_models.return_value = []
        
        path_manager = PathManager()
        collector = InteractiveParameterCollector(path_manager)
        
        with self.assertRaises(SystemExit):
            collector.collect_model_name()


class TestCollectInput(unittest.TestCase):
    """Test collect_input method."""
    
    def setUp(self):
        """Setup collector and temp directory."""
        self.path_manager = PathManager()
        self.collector = InteractiveParameterCollector(self.path_manager)
        
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temp directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('builtins.input', side_effect=['1', 'Test line 1', 'Test line 2', EOFError()])
    @patch('builtins.print')
    def test_collect_input_valid_file(self, mock_print, mock_input):
        """Should return CLI text input."""
        # Mock get_input_files to return empty list
        self.path_manager.get_input_files = Mock(return_value=[])
        
        input_path, input_text = self.collector.collect_input()
        
        # When choosing CLI input (option 1), path should be None and text should be set
        self.assertIsNone(input_path)
        self.assertIsNotNone(input_text)
        self.assertIn('Test line 1', input_text)
    
    @patch('builtins.input', side_effect=['invalid', '1', 'Test text', EOFError()])
    @patch('builtins.print')
    def test_collect_input_retry_on_invalid_file(self, mock_print, mock_input):
        """Should re-prompt on invalid choice."""
        # Mock get_input_files to return empty list
        self.path_manager.get_input_files = Mock(return_value=[])
        
        input_path, input_text = self.collector.collect_input()
        
        # Should eventually succeed with CLI input
        self.assertIsNone(input_path)
        self.assertIsNotNone(input_text)


class TestCollectOutput(unittest.TestCase):
    """Test collect_output method."""
    
    def setUp(self):
        """Setup collector."""
        self.path_manager = PathManager()
        self.collector = InteractiveParameterCollector(self.path_manager)
    
    @patch('builtins.input', return_value='1')  # Choose option 1 (file)
    @patch('builtins.print')
    def test_collect_output_file_input(self, mock_print, mock_input):
        """Should prompt for output path for file input."""
        # Note: This will still try to generate output path
        # Just verify it doesn't crash
        try:
            result = self.collector.collect_output(input_source='file', task='DIACRITICS')
            # Should return output path or None (console)
            self.assertIsInstance(result, (str, type(None)))
        except SystemExit:
            # May exit if user chooses exit option
            pass
    
    @patch('builtins.input', return_value='2')  # Choose console output
    @patch('builtins.print')
    def test_collect_output_cli_text_input(self, mock_print, mock_input):
        """Should default to console for CLI text input."""
        # For CLI text input, it defaults to console but still prompts
        result = self.collector.collect_output(input_source='cli_text', task='DIACRITICS')
        
        # For CLI text, typically defaults to console (None)
        self.assertIsNone(result)


class TestCancellation(unittest.TestCase):
    """Test that every prompt can be cancelled with UserCancelled instead of exiting the process."""
    
    def setUp(self):
        """Setup collector."""
        self.path_manager = PathManager()
        self.path_manager.get_input_files = Mock(return_value=[])
        self.collector = InteractiveParameterCollector(self.path_manager)
    
    @patch('builtins.input', return_value='0')
    @patch('builtins.print')
    def test_input_selection_exit(self, mock_print, mock_input):
        """Choosing 0 in the input menu cancels."""
        with self.assertRaises(UserCancelled):
            self.collector.collect_input()
    
    @patch('builtins.input', side_effect=['1', 'exit', '0'])
    @patch('builtins.print')
    def test_cancelled_text_entry_returns_to_menu(self, mock_print, mock_input):
        """Typing 'exit' while entering text returns to the input menu."""
        with self.assertRaises(UserCancelled):
            self.collector.collect_input()
        
        self.assertEqual(mock_input.call_count, 3)
    
    @patch('builtins.input', return_value='0')
    @patch('builtins.print')
    def test_output_selection_exit(self, mock_print, mock_input):
        """Choosing 0 in the output menu cancels."""
        with self.assertRaises(UserCancelled):
            self.collector.collect_output(input_source='file.txt', task='edit')
    
    @patch('builtins.input', side_effect=['1', 'exit'])
    @patch('builtins.print')
    def test_output_path_exit(self, mock_print, mock_input):
        """Typing 'exit' at the output path prompt cancels."""
        with self.assertRaises(UserCancelled):
            self.collector.collect_output(input_source='file.txt', task='edit')
    
    @patch('builtins.input', return_value='exit')
    @patch('builtins.print')
    def test_verbose_exit(self, mock_print, mock_input):
        """Typing 'exit' at the verbose prompt cancels."""
        with self.assertRaises(UserCancelled):
            self.collector.collect_verbose()
    
    @patch('builtins.input', side_effect=KeyboardInterrupt())
    @patch('builtins.print')
    def test_ctrl_c_during_output_selection(self, mock_print, mock_input):
        """Ctrl+C at any prompt is a cancellation."""
        with self.assertRaises(UserCancelled):
            self.collector.collect_output(input_source='file.txt', task='edit')
    
    @patch('builtins.input', side_effect=['abc', '9', '0'])
    @patch('builtins.print')
    def test_invalid_choices_are_retried(self, mock_print, mock_input):
        """Non-numeric and out-of-range choices re-prompt until a valid one."""
        with self.assertRaises(UserCancelled):
            self.collector.collect_input()
        
        self.assertEqual(mock_input.call_count, 3)


class TestLoggingInInteractiveCollector(unittest.TestCase):
    """Test logging functionality in interactive collector."""
    
    def test_log_collection_called(self):
        """Should call _log_collection when collecting parameters."""
        path_manager = PathManager()
        collector = InteractiveParameterCollector(path_manager)
        
        # Mock _log_collection
        with patch.object(collector, '_log_collection') as mock_log:
            with patch('builtins.input', return_value='1'):
                with patch('builtins.print'):
                    collector.collect_task()
            
            # Should have logged the collection
            mock_log.assert_called()


if __name__ == '__main__':
    unittest.main()
