"""
Integration tests for chunking with configuration and application.
Tests configuration loading, parameter collection, and app integration.
Migrated from test_chunking_language.py.
"""
import unittest
from src.text_processor.chunker import (
    TextChunker,
    get_chunker_strategy,
    VALID_CHUNKER_NAMES
)
from src.config.app_config import get_app_config
from src.app.text_processing_app import TextProcessingApplication
from src.app.parameter_collection.interactive_collector import InteractiveParameterCollector
from src.app.path_manager import PathManager
from src.app.processor_factory import ProcessorFactory


class TestChunkerConfigIntegration(unittest.TestCase):
    """Test configuration integration with chunking."""
    
    @classmethod
    def setUpClass(cls):
        """Load configuration once for all tests."""
        cls.config = get_app_config()
        cls.actions_cfg = cls.config.actions_config
    
    def test_all_tasks_have_required_fields(self):
        """All task configurations should have CHUNKERS and INPUT_LANGUAGE."""
        # Get tasks dynamically from ProcessorFactory
        available_tasks = ProcessorFactory.get_available_tasks()
        
        for task in available_tasks:
            with self.subTest(task=task):
                # Get task config directly using ProcessorFactory
                task_config = ProcessorFactory.get_task_config(self.actions_cfg, task)
                
                self.assertTrue(hasattr(task_config, 'DESC'), 
                              f"{task} missing DESC")
                self.assertTrue(hasattr(task_config, 'PROMPT'), 
                              f"{task} missing PROMPT")
                self.assertTrue(hasattr(task_config, 'CHUNKERS'), 
                              f"{task} missing CHUNKERS")
                self.assertTrue(hasattr(task_config, 'INPUT_LANGUAGE'), 
                              f"{task} missing INPUT_LANGUAGE")
    
    def test_all_configured_chunkers_are_valid(self):
        """All chunker names in config should be valid."""
        # Get tasks dynamically from ProcessorFactory
        available_tasks = ProcessorFactory.get_available_tasks()
        
        for task in available_tasks:
            with self.subTest(task=task):
                # Get task config directly using ProcessorFactory
                task_config = ProcessorFactory.get_task_config(self.actions_cfg, task)
                
                for chunker_name in task_config.CHUNKERS:
                    self.assertIn(chunker_name, VALID_CHUNKER_NAMES,
                                f"{task} has invalid chunker '{chunker_name}'")
    
    def test_input_language_values_are_valid(self):
        """INPUT_LANGUAGE should be 'ro' or 'en'."""
        # Get tasks dynamically from ProcessorFactory
        available_tasks = ProcessorFactory.get_available_tasks()
        valid_languages = {'ro', 'en'}
        
        for task in available_tasks:
            with self.subTest(task=task):
                # Get task config directly using ProcessorFactory
                task_config = ProcessorFactory.get_task_config(self.actions_cfg, task)
                self.assertIn(task_config.INPUT_LANGUAGE, valid_languages,
                            f"{task} has invalid INPUT_LANGUAGE")


class TestParameterCollectionIntegration(unittest.TestCase):
    """Test parameter collection for chunkers."""
    
    def setUp(self):
        """Create path manager for collectors."""
        self.path_manager = PathManager()
    
    def test_interactive_collector_returns_none(self):
        """InteractiveParameterCollector.collect_chunkers() should always return None."""
        collector = InteractiveParameterCollector(self.path_manager)
        result = collector.collect_chunkers()
        
        self.assertIsNone(result, 
                         "Interactive collector should always return None for chunkers")

class MockTaskConfig:
    """Mock task configuration for testing."""
    def __init__(self, chunkers, language):
        self.CHUNKERS = chunkers
        self.INPUT_LANGUAGE = language
        self.DESC = "Mock task"
        self.PROMPT = "Mock prompt"


class TestAppChunkerIntegration(unittest.TestCase):
    """Test TextProcessingApplication chunker creation."""
    
    @classmethod
    def setUpClass(cls):
        """Initialize app once for all tests."""
        config = get_app_config()
        cls.app = TextProcessingApplication(config)
    
    def test_create_chunker_with_config_defaults(self):
        """Should create chunker using config when CLI is None."""
        task_config = MockTaskConfig(['sentence_split', 'size_optimizing'], 'ro')
        
        chunker = self.app._create_chunker_for_task(
            task_config=task_config,
            task_name='test',
            language='ro',
            chunkers=None  # No CLI override
        )
        
        self.assertIsNotNone(chunker)
        self.assertEqual(len(chunker.strategies), 2)
    
    def test_create_chunker_with_cli_override(self):
        """Should use CLI chunkers when provided."""
        task_config = MockTaskConfig(['sentence_split', 'size_optimizing'], 'ro')
        
        chunker = self.app._create_chunker_for_task(
            task_config=task_config,
            task_name='test',
            language='ro',
            chunkers=['paragraph_split']  # CLI override
        )
        
        self.assertIsNotNone(chunker)
        self.assertEqual(len(chunker.strategies), 1)
    
    def test_create_chunker_with_empty_config(self):
        """Should return None when config has empty chunkers list."""
        task_config = MockTaskConfig([], 'ro')  # Empty chunkers
        
        chunker = self.app._create_chunker_for_task(
            task_config=task_config,
            task_name='test',
            language='ro',
            chunkers=None  # Use config
        )
        
        self.assertIsNone(chunker)
    
    def test_create_chunker_with_cli_none(self):
        """Should return None when CLI specifies empty list (none)."""
        task_config = MockTaskConfig(['sentence_split'], 'ro')
        
        chunker = self.app._create_chunker_for_task(
            task_config=task_config,
            task_name='test',
            language='ro',
            chunkers=[]  # CLI "none"
        )
        
        self.assertIsNone(chunker)
    
    def test_language_parameter_flows_correctly(self):
        """Language parameter should flow to chunker correctly."""
        # Test Romanian
        task_config_ro = MockTaskConfig(['sentence_split'], 'ro')
        chunker_ro = self.app._create_chunker_for_task(
            task_config=task_config_ro,
            task_name='test',
            language='ro',
            chunkers=None
        )
        
        # Test English
        task_config_en = MockTaskConfig(['sentence_split'], 'en')
        chunker_en = self.app._create_chunker_for_task(
            task_config=task_config_en,
            task_name='test',
            language='en',
            chunkers=None
        )
        
        self.assertIsNotNone(chunker_ro)
        self.assertIsNotNone(chunker_en)
        self.assertEqual(chunker_ro.language, 'ro')
        self.assertEqual(chunker_en.language, 'en')


class TestEndToEndChunking(unittest.TestCase):
    """Test end-to-end chunking scenarios."""
    
    def test_romanian_text_with_abbreviations_e2e(self):
        """End-to-end test with Romanian text containing abbreviations."""
        sample_text = """Acesta este primul paragraf. Conține mai multe propoziții. 
Dr. Popescu a venit ieri. A adus documente importante.

Al doilea paragraf este mai scurt. Dar tot are sens.

Al treilea paragraf. Și ultimul."""
        
        # Create chunker with typical Romanian configuration
        chunker = TextChunker(language="ro")
        chunker.add_strategy(get_chunker_strategy("sentence_split", language="ro"))
        chunker.add_strategy(get_chunker_strategy("size_optimizing"))
        
        chunks = chunker.chunk_text(sample_text)
        
        # Should create multiple chunks
        self.assertGreater(len(chunks), 0)
        
        # Verify Dr. abbreviation was handled correctly (not split)
        found_dr_popescu = any("Dr. Popescu" in chunk for chunk in chunks)
        self.assertTrue(found_dr_popescu, 
                       "Dr. Popescu should stay together in a chunk")
    
    def test_english_vs_romanian_abbreviations_e2e(self):
        """Test that language affects abbreviation handling."""
        ro_text = "Dr. Ion a venit. Apoi Dna. Maria a plecat."
        en_text = "Dr. Smith arrived. Then Mrs. Johnson left. Mr. Brown stayed."
        
        # Romanian chunking
        ro_chunker = TextChunker(language="ro")
        ro_chunker.add_strategy(get_chunker_strategy("sentence_split", language="ro"))
        ro_chunks = ro_chunker.chunk_text(ro_text)
        
        # English chunking
        en_chunker = TextChunker(language="en")
        en_chunker.add_strategy(get_chunker_strategy("sentence_split", language="en"))
        en_chunks = en_chunker.chunk_text(en_text)
        
        # Both should handle their respective abbreviations
        self.assertGreater(len(ro_chunks), 0)
        self.assertGreater(len(en_chunks), 0)
        
        # Verify abbreviations stay together
        ro_has_dr = any("Dr. Ion" in chunk for chunk in ro_chunks)
        en_has_dr = any("Dr. Smith" in chunk for chunk in en_chunks)
        
        self.assertTrue(ro_has_dr, "Romanian Dr. should not be split")
        self.assertTrue(en_has_dr, "English Dr. should not be split")


if __name__ == '__main__':
    unittest.main()
