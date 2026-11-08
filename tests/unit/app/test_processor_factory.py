"""
Unit tests for ProcessorFactory.
Tests processor creation and task validation.
"""
import unittest
from src.app.processor_factory import ProcessorFactory
from src.config.app_config import get_app_config
from src.text_processor import TextProcessor, DiacriticAdder, TASK_REGISTRY
from src.utils.dict_utils import DotDict

MODEL = "jobautomation/OpenEuroLLM-Romanian:latest"
CONFIG_ONLY_TASKS = ["summarize", "edit", "translate_ro_en", "translate_en_ro", "custom"]


class TestProcessorFactory(unittest.TestCase):
    """Test ProcessorFactory class methods."""
    
    def test_create_processor_registered_task(self):
        """A task with a registered class gets that class."""
        processor = ProcessorFactory.create_processor("diacritics", MODEL)
        
        self.assertIsInstance(processor, DiacriticAdder)
        self.assertEqual(processor.model_name, MODEL)
        self.assertEqual(processor.task_name, "diacritics")
    
    def test_create_processor_config_only_tasks(self):
        """Tasks without a registered class get the default TextProcessor."""
        for task in CONFIG_ONLY_TASKS:
            with self.subTest(task=task):
                processor = ProcessorFactory.create_processor(task, MODEL)
                
                self.assertIs(type(processor), TextProcessor)
                self.assertEqual(processor.task_name, task)
                self.assertEqual(processor.prompt, get_app_config().actions_config[task.upper()].PROMPT)
    
    def test_create_processor_invalid_task(self):
        """Test creating processor with invalid task."""
        with self.assertRaises(ValueError) as context:
            ProcessorFactory.create_processor("invalid_task", MODEL)
        
        self.assertIn("Unknown task", str(context.exception))
        self.assertIn("invalid_task", str(context.exception))
    
    def test_get_available_tasks(self):
        """Test getting list of available tasks, in config order."""
        tasks = ProcessorFactory.get_available_tasks()
        
        self.assertEqual(
            tasks,
            ["diacritics", "summarize", "edit", "translate_ro_en", "translate_en_ro", "custom"]
        )
    
    def test_get_available_tasks_from_given_config(self):
        """Tasks are the lower-case config keys of the given config."""
        config = DotDict({"MY_TASK": {"DESC": "d", "PROMPT": "p"}})
        
        self.assertEqual(ProcessorFactory.get_available_tasks(config), ["my_task"])
    
    def test_is_valid_task_valid(self):
        """Test is_valid_task with valid tasks."""
        self.assertTrue(ProcessorFactory.is_valid_task("diacritics"))
        self.assertTrue(ProcessorFactory.is_valid_task("summarize"))
        self.assertTrue(ProcessorFactory.is_valid_task("translate_ro_en"))
    
    def test_is_valid_task_invalid(self):
        """Test is_valid_task with invalid tasks."""
        self.assertFalse(ProcessorFactory.is_valid_task("invalid"))
        self.assertFalse(ProcessorFactory.is_valid_task(""))
        self.assertFalse(ProcessorFactory.is_valid_task("ro_to_en"))
    
    def test_validate_config_valid(self):
        """Test validate_config with valid configuration."""
        config = get_app_config()
        errors, warnings = ProcessorFactory.validate_config(config.actions_config)
        
        self.assertEqual(errors, [])
    
    def test_validate_config_missing_entry_for_registered_task(self):
        """A registered task class without a config entry is an error."""
        config = DotDict({"SUMMARIZE": {"DESC": "d", "PROMPT": "p", "CHUNKERS": []}})
        
        errors, warnings = ProcessorFactory.validate_config(config)
        
        self.assertTrue(any("'diacritics' missing config entry 'DIACRITICS'" in e for e in errors))
    
    def test_validate_config_missing_desc_field(self):
        """Test validate_config with missing DESC field."""
        config = DotDict({"DIACRITICS": {"PROMPT": "p", "CHUNKERS": []}})
        
        errors, warnings = ProcessorFactory.validate_config(config)
        
        self.assertTrue(any("DESC" in error for error in errors))
    
    def test_validate_config_unknown_chunker(self):
        """An unknown chunker name in a task is an error at startup."""
        config = DotDict({
            "DIACRITICS": {"DESC": "d", "PROMPT": "p", "CHUNKERS": ["no_such_chunker"]}
        })
        
        errors, warnings = ProcessorFactory.validate_config(config)
        
        self.assertTrue(any("no_such_chunker" in error for error in errors))
    
    def test_validate_config_lowercase_key(self):
        """Config keys must be upper-case so they map back to task names."""
        config = DotDict({
            "DIACRITICS": {"DESC": "d", "PROMPT": "p", "CHUNKERS": []},
            "my_task": {"DESC": "d", "PROMPT": "p", "CHUNKERS": []}
        })
        
        errors, warnings = ProcessorFactory.validate_config(config)
        
        self.assertTrue(any("'my_task' must be upper-case" in error for error in errors))
    
    def test_config_entry_without_class_is_valid(self):
        """A config entry with no registered class is a valid, config-only task."""
        config = DotDict({
            "DIACRITICS": {"DESC": "d", "PROMPT": "p", "CHUNKERS": []},
            "GRAMMAR_CHECK": {"DESC": "d", "PROMPT": "p", "CHUNKERS": ["sentence_split"]}
        })
        
        errors, warnings = ProcessorFactory.validate_config(config)
        
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
    
    def test_get_task_config(self):
        """Test getting task configuration."""
        config = get_app_config()
        task_config = ProcessorFactory.get_task_config(config.actions_config, "translate_ro_en")
        
        self.assertIsNotNone(task_config)
        self.assertTrue(hasattr(task_config, 'DESC'))
        self.assertTrue(hasattr(task_config, 'PROMPT'))
    
    def test_get_task_config_invalid_task(self):
        """Test getting config for invalid task."""
        config = get_app_config()
        task_config = ProcessorFactory.get_task_config(config.actions_config, "invalid_task")
        
        self.assertIsNone(task_config)
    
    def test_get_task_descriptions(self):
        """Test getting task descriptions."""
        descriptions = ProcessorFactory.get_task_descriptions()
        
        self.assertEqual(list(descriptions), ProcessorFactory.get_available_tasks())
        for task, desc in descriptions.items():
            self.assertIsInstance(desc, str)
            self.assertGreater(len(desc), 0)
    
    def test_create_multiple_processors(self):
        """Test creating multiple processors with different models."""
        proc1 = ProcessorFactory.create_processor("diacritics", MODEL)
        proc2 = ProcessorFactory.create_processor("diacritics", "mistral:7b")
        proc3 = ProcessorFactory.create_processor("summarize", MODEL)
        
        self.assertIsNot(proc1, proc2)
        self.assertIsNot(proc1, proc3)
        self.assertIsInstance(proc1, DiacriticAdder)
        self.assertIsInstance(proc2, DiacriticAdder)
        self.assertIs(type(proc3), TextProcessor)
        self.assertEqual(proc1.model_name, MODEL)
        self.assertEqual(proc2.model_name, "mistral:7b")


class TestTaskRegistry(unittest.TestCase):
    """Test the registry that backs ProcessorFactory."""
    
    def test_registered_tasks_have_config_entries(self):
        """Every registered task name maps to an entry in the real config."""
        actions_config = get_app_config().actions_config
        
        for task_name, processor_class in TASK_REGISTRY.items():
            with self.subTest(task=task_name):
                self.assertIn(task_name.upper(), actions_config)
                self.assertTrue(issubclass(processor_class, TextProcessor))
                self.assertEqual(processor_class.TASK_NAME, task_name)


if __name__ == "__main__":
    unittest.main()
