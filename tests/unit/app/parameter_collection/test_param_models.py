"""
Unit tests for parameter collection models.
Tests ProcessingParameters and ValidationResult dataclasses.
"""
import unittest
from src.app.parameter_collection.param_models import (
    ProcessingParameters,
    ValidationResult,
    OutputMode
)


class TestOutputMode(unittest.TestCase):
    """Test OutputMode enum."""
    
    def test_output_mode_values(self):
        """Test enum values."""
        self.assertEqual(OutputMode.FILE.value, "file")
        self.assertEqual(OutputMode.CONSOLE.value, "console")


class TestValidationResult(unittest.TestCase):
    """Test ValidationResult dataclass."""
    
    def test_validation_result_default(self):
        """Test default validation result."""
        result = ValidationResult(is_valid=True)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])
    
    def test_validation_result_with_errors(self):
        """Test validation result with errors."""
        result = ValidationResult(is_valid=False)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors, [])
    
    def test_add_error(self):
        """Test adding errors to validation result."""
        result = ValidationResult(is_valid=True)
        
        result.add_error("First error")
        self.assertFalse(result.is_valid)
        self.assertIn("First error", result.errors)
        
        result.add_error("Second error")
        self.assertEqual(len(result.errors), 2)
        self.assertFalse(result.is_valid)
    
    def test_add_warning(self):
        """Test adding warnings to validation result."""
        result = ValidationResult(is_valid=True)
        
        result.add_warning("First warning")
        self.assertTrue(result.is_valid)  # Warnings don't invalidate
        self.assertIn("First warning", result.warnings)
        
        result.add_warning("Second warning")
        self.assertEqual(len(result.warnings), 2)


class TestProcessingParameters(unittest.TestCase):
    """Test ProcessingParameters dataclass."""
    
    def test_default_initialization(self):
        """Test default parameter initialization."""
        params = ProcessingParameters()
        
        self.assertIsNone(params.task)
        self.assertIsNone(params.model_name)
        self.assertIsNone(params.input_path)
        self.assertIsNone(params.input_text)
        self.assertIsNone(params.output_path)
        self.assertFalse(params.verbose)
        self.assertIsNone(params.chunkers)
        self.assertEqual(params._source, {})
    
    def test_is_complete_with_file_input(self):
        """Test is_complete with file input."""
        params = ProcessingParameters(
            task="diacritics",
            model_name="jobautomation/OpenEuroLLM-Romanian:latest",
            input_path="/path/to/file.txt"
        )
        
        self.assertTrue(params.is_complete())
    
    def test_is_complete_with_text_input(self):
        """Test is_complete with text input."""
        params = ProcessingParameters(
            task="summarize",
            model_name="jobautomation/OpenEuroLLM-Romanian:latest",
            input_text="Some direct text"
        )
        
        self.assertTrue(params.is_complete())
    
    def test_is_complete_missing_required_fields(self):
        """Test is_complete with various missing required fields."""
        # Missing task
        params1 = ProcessingParameters(model_name="jobautomation/OpenEuroLLM-Romanian:latest", input_path="/path/to/file.txt")
        self.assertFalse(params1.is_complete())
        
        # Missing model
        params2 = ProcessingParameters(task="diacritics", input_path="/path/to/file.txt")
        self.assertFalse(params2.is_complete())
        
        # Missing input
        params3 = ProcessingParameters(task="diacritics", model_name="jobautomation/OpenEuroLLM-Romanian:latest")
        self.assertFalse(params3.is_complete())
    
    def test_get_missing_required(self):
        """Test getting missing required parameters."""
        params = ProcessingParameters()
        
        missing = params.get_missing_required()
        
        self.assertIn("task", missing)
        self.assertIn("model", missing)
        self.assertIn("input", missing)
        self.assertEqual(len(missing), 3)
    
    def test_get_missing_required_complete(self):
        """Test getting missing parameters when complete."""
        params = ProcessingParameters(
            task="diacritics",
            model_name="jobautomation/OpenEuroLLM-Romanian:latest",
            input_path="/path/to/file.txt"
        )
        
        missing = params.get_missing_required()
        
        self.assertEqual(missing, [])
    
    def test_get_input_source_text(self):
        """Test getting input source when using direct text."""
        params = ProcessingParameters(input_text="Direct text")
        
        source = params.get_input_source()
        
        self.assertEqual(source, "Direct text")
    
    def test_get_input_source_text_priority(self):
        """Test that text input takes priority over path."""
        params = ProcessingParameters(
            input_text="Direct text",
            input_path="/path/to/file.txt"
        )
        
        source = params.get_input_source()
        
        self.assertEqual(source, "Direct text")
    
    def test_get_output_mode_console(self):
        """Test output mode when no output path."""
        params = ProcessingParameters()
        
        mode = params.get_output_mode()
        
        self.assertEqual(mode, OutputMode.CONSOLE)
    
    def test_get_output_mode_file(self):
        """Test output mode when output path is set."""
        params = ProcessingParameters(output_path="/path/to/output.txt")
        
        mode = params.get_output_mode()
        
        self.assertEqual(mode, OutputMode.FILE)
    
    def test_to_dict(self):
        """Test converting parameters to dictionary."""
        params = ProcessingParameters(
            task="diacritics",
            model_name="jobautomation/OpenEuroLLM-Romanian:latest",
            input_path="/path/to/file.txt",
            output_path="/path/to/output.txt",
            verbose=True,
            chunkers=["sentence_split", "size_optimizing"]
        )
        
        result = params.to_dict()
        
        self.assertEqual(result["task"], "diacritics")
        self.assertEqual(result["model_name"], "jobautomation/OpenEuroLLM-Romanian:latest")
        self.assertEqual(result["input_path"], "/path/to/file.txt")
        self.assertEqual(result["output_path"], "/path/to/output.txt")
        self.assertTrue(result["verbose"])
        self.assertEqual(result["chunkers"], ["sentence_split", "size_optimizing"])
        self.assertIsNone(result["input_text"])
    
    def test_mark_source(self):
        """Test marking parameter sources."""
        params = ProcessingParameters()
        
        params.mark_source("task", "cli")
        params.mark_source("model_name", "interactive")
        
        self.assertEqual(params._source["task"], "cli")
        self.assertEqual(params._source["model_name"], "interactive")
    
    def test_with_optional_parameters(self):
        """Test parameters with optional fields set."""
        params = ProcessingParameters(
            task="edit",
            model_name="jobautomation/OpenEuroLLM-Romanian:latest",
            input_text="Test text",
            verbose=True,
            chunkers=["paragraph_split"]
        )
        
        self.assertTrue(params.is_complete())
        self.assertTrue(params.verbose)
        self.assertEqual(params.chunkers, ["paragraph_split"])


if __name__ == "__main__":
    unittest.main()
