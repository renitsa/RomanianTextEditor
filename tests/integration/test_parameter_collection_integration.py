"""
Integration tests for parameter collection orchestration.
Tests the interaction between ParameterCollectionOrchestrator and different collectors.
"""
import unittest
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from src.app.parameter_collection.param_orchestrator import ParameterCollectionOrchestrator
from src.app.parameter_collection.cli_collector import CLIParameterCollector
from src.app.parameter_collection.interactive_collector import InteractiveParameterCollector
from src.app.parameter_collection.base_collector import BaseParameterCollector
from src.app.path_manager import PathManager
from src.config.app_config import get_app_config


class TestOrchestratorWithRealCollectors(unittest.TestCase):
    """Test orchestrator with real collector implementations."""
    
    def setUp(self):
        """Setup orchestrator and path manager."""
        self.path_manager = PathManager()
        self.orchestrator = ParameterCollectionOrchestrator(self.path_manager)
    
    def test_orchestrator_initializes_collectors(self):
        """Orchestrator should initialize all collectors."""
        self.assertIsNotNone(self.orchestrator.cli_collector)
        self.assertIsNotNone(self.orchestrator.interactive_collector)
        
        self.assertIsInstance(self.orchestrator.cli_collector, CLIParameterCollector)
        self.assertIsInstance(self.orchestrator.interactive_collector, InteractiveParameterCollector)
    
    def test_orchestrator_has_path_manager_reference(self):
        """All collectors should have access to path manager."""
        self.assertIs(self.orchestrator.cli_collector.path_manager, self.path_manager)
        self.assertIs(self.orchestrator.interactive_collector.path_manager, self.path_manager)
    
    def test_cli_collector_lazy_parsing(self):
        """CLI collector should not parse arguments until needed."""
        # Create new CLI collector (should not parse on init)
        cli_collector = CLIParameterCollector(self.path_manager)
        
        # _args should be None initially
        self.assertIsNone(cli_collector._args)
        
        # After collecting, it should be parsed
        with patch.object(sys, 'argv', ['test', '--task', 'DIACRITICS']):
            cli_collector._ensure_args_parsed()
            self.assertIsNotNone(cli_collector._args)
    
    def test_interactive_collector_returns_none_for_chunkers(self):
        """Interactive collector should return None for chunkers."""
        result = self.orchestrator.interactive_collector.collect_chunkers()
        self.assertIsNone(result)


class TestParameterCollectionFlow(unittest.TestCase):
    """Test end-to-end parameter collection flows."""
    
    def setUp(self):
        """Setup components."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.path_manager = PathManager()
        self.orchestrator = ParameterCollectionOrchestrator(self.path_manager)
    
    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_collect_non_interactive_flag_from_cli(self):
        """Test collecting non-interactive flag from CLI."""
        with patch.object(sys, 'argv', ['test', '--non-interactive']):
            # Create fresh collector with mocked args
            cli_collector = CLIParameterCollector(self.path_manager)
            result = cli_collector.is_non_interactive()
            
            self.assertTrue(result)
    
    def test_collect_task_from_cli(self):
        """Test collecting task from CLI."""
        with patch.object(sys, 'argv', ['test', '--task', 'SUMMARIZE']):
            cli_collector = CLIParameterCollector(self.path_manager)
            task = cli_collector.collect_task()
            
            self.assertEqual(task, 'SUMMARIZE')
    
    def test_collect_model_from_cli(self):
        """Test collecting model from CLI."""
        with patch.object(sys, 'argv', ['test', '--model', 'llama3']):
            cli_collector = CLIParameterCollector(self.path_manager)
            model = cli_collector.collect_model_name()
            
            self.assertEqual(model, 'llama3')
    
    def test_collect_verbose_flag(self):
        """Test collecting verbose flag."""
        with patch.object(sys, 'argv', ['test', '--verbose']):
            cli_collector = CLIParameterCollector(self.path_manager)
            verbose = cli_collector.collect_verbose()
            
            self.assertTrue(verbose)
    
    def test_collect_input_file_from_cli(self):
        """Test collecting input file from CLI."""
        # Create a test file
        test_file = self.temp_path / "test_input.txt"
        test_file.write_text("Test content", encoding='utf-8')
        
        with patch.object(sys, 'argv', ['test', '--input', str(test_file)]):
            cli_collector = CLIParameterCollector(self.path_manager)
            input_path, input_text = cli_collector.collect_input()
            
            self.assertEqual(input_path, str(test_file))
            self.assertIsNone(input_text)
    
    def test_collect_input_text_from_cli(self):
        """Test collecting text directly from CLI."""
        with patch.object(sys, 'argv', ['test', '--text', 'Direct text input']):
            cli_collector = CLIParameterCollector(self.path_manager)
            input_path, input_text = cli_collector.collect_input()
            
            self.assertIsNone(input_path)
            self.assertEqual(input_text, 'Direct text input')
    
    def test_collect_output_file_from_cli(self):
        """Test collecting output file from CLI."""
        output_path = str(self.temp_path / "output.txt")
        
        with patch.object(sys, 'argv', ['test', '--task', 'DIACRITICS', '--output', output_path]):
            cli_collector = CLIParameterCollector(self.path_manager)
            result = cli_collector.collect_output(input_source='file', task='DIACRITICS')
            
            self.assertEqual(result, output_path)
    
    def test_collect_console_output_flag(self):
        """Test collecting console output flag."""
        with patch.object(sys, 'argv', ['test', '--task', 'DIACRITICS', '--console']):
            cli_collector = CLIParameterCollector(self.path_manager)
            result = cli_collector.collect_output(input_source='file', task='DIACRITICS')
            
            self.assertIsNone(result)  # Console output
    
    def test_collect_chunkers_from_cli(self):
        """Test collecting chunkers from CLI."""
        with patch.object(sys, 'argv', ['test', '--chunkers', 'sentence_split', 'paragraph_split']):
            cli_collector = CLIParameterCollector(self.path_manager)
            chunkers = cli_collector.collect_chunkers()
            
            self.assertEqual(chunkers, ['sentence_split', 'paragraph_split'])
    
    def test_collect_no_chunkers_from_cli(self):
        """Test collecting 'none' for chunkers from CLI."""
        with patch.object(sys, 'argv', ['test', '--chunkers', 'none']):
            cli_collector = CLIParameterCollector(self.path_manager)
            chunkers = cli_collector.collect_chunkers()
            
            self.assertEqual(chunkers, [])  # Empty list means no chunking


class TestOrchestratorCollectionMethods(unittest.TestCase):
    """Test orchestrator's collection methods with different modes."""
    
    def setUp(self):
        """Setup orchestrator."""
        self.path_manager = PathManager()
        self.orchestrator = ParameterCollectionOrchestrator(self.path_manager)
    
    def test_non_interactive_mode_detection(self):
        """Test that orchestrator can detect non-interactive mode from CLI."""
        with patch.object(sys, 'argv', ['test', '--non-interactive']):
            cli_collector = CLIParameterCollector(self.path_manager)
            is_non_interactive = cli_collector.is_non_interactive()
            
            self.assertTrue(is_non_interactive)
    
    def test_orchestrator_has_cli_and_interactive_collectors(self):
        """Test that orchestrator has both collector types."""
        self.assertIsInstance(self.orchestrator.cli_collector, CLIParameterCollector)
        self.assertIsInstance(self.orchestrator.interactive_collector, InteractiveParameterCollector)
    
    def test_orchestrator_has_validator(self):
        """Test that orchestrator has parameter validator."""
        from src.app.parameter_collection.param_validator import ParameterValidator
        self.assertIsInstance(self.orchestrator.validator, ParameterValidator)


class TestCollectorInterfaceCompliance(unittest.TestCase):
    """Test that all collectors implement the base interface correctly."""
    
    def setUp(self):
        """Setup collectors."""
        self.path_manager = PathManager()
        self.collectors = [
            CLIParameterCollector(self.path_manager),
            InteractiveParameterCollector(self.path_manager)
        ]
    
    def test_all_collectors_have_required_methods(self):
        """All collectors should implement required collection methods."""
        required_methods = [
            'collect_task',
            'collect_model_name',
            'collect_input',
            'collect_output',
            'collect_verbose',
            'collect_chunkers'
        ]
        
        for collector in self.collectors:
            for method_name in required_methods:
                with self.subTest(collector=type(collector).__name__, method=method_name):
                    self.assertTrue(hasattr(collector, method_name),
                                  f"{type(collector).__name__} missing {method_name}")
    
    def test_all_collectors_have_path_manager(self):
        """All collectors should have path_manager attribute."""
        for collector in self.collectors:
            with self.subTest(collector=type(collector).__name__):
                self.assertTrue(hasattr(collector, 'path_manager'))
                self.assertIsInstance(collector.path_manager, PathManager)


class TestVerboseFlagWithInteractiveMode(unittest.TestCase):
    """Test that --verbose flag alone triggers interactive mode with verbose enabled."""
    
    def setUp(self):
        """Setup test components."""
        self.path_manager = PathManager()
        self.orchestrator = ParameterCollectionOrchestrator(self.path_manager)
    
    def test_verbose_only_triggers_pure_interactive_mode(self):
        """When only --verbose is provided, should enter pure interactive mode."""
        with patch.object(sys, 'argv', ['test', '--verbose']):
            cli_collector = CLIParameterCollector(self.path_manager)
            
            # Verify that --verbose alone does NOT count as having processing args
            has_processing = cli_collector.has_processing_args()
            self.assertFalse(has_processing, 
                           "Verbose flag alone should NOT trigger CLI processing mode")
            
            # Verify that verbose flag is still collected correctly
            verbose_flag = cli_collector.collect_verbose()
            self.assertTrue(verbose_flag, 
                          "Verbose flag should be True when --verbose is provided")
    
    def test_verbose_flag_collected_in_interactive_mode(self):
        """Verify --verbose is respected even in interactive mode."""
        with patch.object(sys, 'argv', ['test', '--verbose']):
            # Create collectors
            cli_collector = CLIParameterCollector(self.path_manager)
            
            # In interactive mode, CLI collector should still see --verbose
            verbose = cli_collector.collect_verbose()
            self.assertTrue(verbose)
            
            # Verify no processing args are present
            self.assertFalse(cli_collector.has_processing_args())
    
    def test_verbose_with_other_args_triggers_cli_mode(self):
        """When --verbose is combined with processing args, should use CLI mode."""
        with patch.object(sys, 'argv', ['test', '--verbose', '--task', 'diacritics']):
            cli_collector = CLIParameterCollector(self.path_manager)
            
            # With --task provided, should have processing args
            has_processing = cli_collector.has_processing_args()
            self.assertTrue(has_processing,
                          "Verbose plus processing args should trigger CLI mode")
            
            # Verbose flag should still be collected
            verbose_flag = cli_collector.collect_verbose()
            self.assertTrue(verbose_flag)
            
            # Task should be collected
            task = cli_collector.collect_task()
            self.assertEqual(task, 'diacritics')
    
    def test_no_args_triggers_pure_interactive_mode(self):
        """When no arguments are provided, should enter pure interactive mode."""
        with patch.object(sys, 'argv', ['test']):
            cli_collector = CLIParameterCollector(self.path_manager)
            
            # No args should mean no processing args
            has_processing = cli_collector.has_processing_args()
            self.assertFalse(has_processing,
                           "No arguments should trigger pure interactive mode")
            
            # Verbose should default to False
            verbose = cli_collector.collect_verbose()
            self.assertFalse(verbose)


if __name__ == '__main__':
    unittest.main()
