"""
Unit tests for parameter validator.
Tests syntax and runtime validation logic.
"""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from src.app.parameter_collection.param_validator import ParameterValidator
from src.app.parameter_collection.param_models import ProcessingParameters, ValidationResult


class TestParameterValidator(unittest.TestCase):
    """Test ParameterValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = ParameterValidator()
    
    def test_initialization_with_logger(self):
        """Test validator initialization with optional logger."""
        validator = ParameterValidator()
        self.assertIsNotNone(validator.logger)
        
        mock_logger = Mock()
        validator_with_logger = ParameterValidator(logger=mock_logger)
        self.assertEqual(validator_with_logger.logger, mock_logger)


class TestSyntaxValidation(unittest.TestCase):
    """Test syntax validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = ParameterValidator()
    
    def test_validate_syntax_valid_params(self):
        """Test syntax validation with valid parameters."""
        params = ProcessingParameters(
            task="diacritics",
            model_name="jobautomation/OpenEuroLLM-Romanian:latest",
            input_path="/path/to/file.txt"
        )
        
        result = self.validator.validate_syntax(params)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_validate_syntax_invalid_task(self):
        """Test syntax validation with invalid task."""
        params = ProcessingParameters(
            task="invalid_task",
            model_name="jobautomation/OpenEuroLLM-Romanian:latest",
            input_path="/path/to/file.txt"
        )
        
        result = self.validator.validate_syntax(params)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        self.assertIn("Invalid task", result.errors[0])
    
    def test_validate_syntax_both_input_types(self):
        """Test syntax validation with both input_path and input_text."""
        params = ProcessingParameters(
            task="diacritics",
            model_name="jobautomation/OpenEuroLLM-Romanian:latest",
            input_path="/path/to/file.txt",
            input_text="Direct text"
        )
        
        result = self.validator.validate_syntax(params)
        
        self.assertFalse(result.is_valid)
        self.assertIn("Cannot specify both", result.errors[0])
    
    def test_validate_syntax_unknown_chunker(self):
        """An unknown --chunkers name is rejected before any processing starts."""
        params = ProcessingParameters(
            task="diacritics",
            model_name="m",
            input_path="/path/to/file.txt",
            chunkers=["sentence_split", "no_such_chunker"]
        )
        
        result = self.validator.validate_syntax(params)
        
        self.assertFalse(result.is_valid)
        self.assertIn("no_such_chunker", result.errors[0])
        self.assertIn("sentence_split", result.errors[0])
    
    def test_validate_syntax_valid_and_empty_chunkers(self):
        """Valid chunker names and 'no chunking' ([]) are accepted."""
        for chunkers in (["paragraph_split", "size_optimizing"], [], None):
            with self.subTest(chunkers=chunkers):
                params = ProcessingParameters(
                    task="diacritics", model_name="m",
                    input_path="/path/to/file.txt", chunkers=chunkers
                )
                
                self.assertTrue(self.validator.validate_syntax(params).is_valid)
    
    def test_validate_syntax_with_logger(self):
        """Test that syntax validation logs warnings on failure."""
        mock_logger = Mock()
        validator = ParameterValidator(logger=mock_logger)
        
        params = ProcessingParameters(
            task="invalid_task",
            model_name="jobautomation/OpenEuroLLM-Romanian:latest",
            input_path="/path/to/file.txt"
        )
        
        validator.validate_syntax(params)
        
        mock_logger.warning.assert_called_once()


class TestRuntimeValidation(unittest.TestCase):
    """Test runtime validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = ParameterValidator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.services.get_ollama_service')
    def test_validate_runtime_ollama_not_running(self, mock_get_service):
        """Test runtime validation when Ollama is not running."""
        mock_service = Mock()
        mock_service.is_ollama_running.return_value = False
        mock_get_service.return_value = mock_service
        
        params = ProcessingParameters(
            task="diacritics",
            model_name="jobautomation/OpenEuroLLM-Romanian:latest",
            input_text="Test text"
        )
        
        result = self.validator.validate_runtime(params)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        self.assertIn("Ollama service is not running", result.errors[0])
    
    @patch('src.services.get_ollama_service')
    def test_validate_runtime_model_not_available(self, mock_get_service):
        """Test runtime validation when model is not available."""
        mock_service = Mock()
        mock_service.is_ollama_running.return_value = True
        mock_service.get_model_names.return_value = ['jobautomation/OpenEuroLLM-Romanian:latest', 'mistral:7b']
        mock_get_service.return_value = mock_service
        
        params = ProcessingParameters(
            task="diacritics",
            model_name="nonexistent_model",
            input_text="Test text"
        )
        
        result = self.validator.validate_runtime(params)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        self.assertIn("not found", result.errors[0])
    
    @patch('src.services.get_ollama_service')
    def test_validate_runtime_input_file_not_found(self, mock_get_service):
        """Test runtime validation when input file doesn't exist."""
        mock_service = Mock()
        mock_service.is_ollama_running.return_value = True
        mock_service.get_model_names.return_value = ['jobautomation/OpenEuroLLM-Romanian:latest']
        mock_get_service.return_value = mock_service
        
        params = ProcessingParameters(
            task="diacritics",
            model_name="jobautomation/OpenEuroLLM-Romanian:latest",
            input_path="/nonexistent/file.txt"
        )
        
        result = self.validator.validate_runtime(params)
        
        self.assertFalse(result.is_valid)
        self.assertIn("not found", result.errors[0])
    
    @patch('src.services.get_ollama_service')
    def test_validate_runtime_success(self, mock_get_service):
        """Test successful runtime validation."""
        mock_service = Mock()
        mock_service.is_ollama_running.return_value = True
        mock_service.get_model_names.return_value = ['jobautomation/OpenEuroLLM-Romanian:latest']
        mock_get_service.return_value = mock_service
        
        # Create temporary input file
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("Test content", encoding='utf-8')
        
        params = ProcessingParameters(
            task="diacritics",
            model_name="jobautomation/OpenEuroLLM-Romanian:latest",
            input_path=str(test_file)
        )
        
        result = self.validator.validate_runtime(params)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
    
    @patch('src.services.get_ollama_service')
    def test_validate_runtime_with_text_input(self, mock_get_service):
        """Test runtime validation with direct text input (no file check)."""
        mock_service = Mock()
        mock_service.is_ollama_running.return_value = True
        mock_service.get_model_names.return_value = ['jobautomation/OpenEuroLLM-Romanian:latest']
        mock_get_service.return_value = mock_service
        
        params = ProcessingParameters(
            task="summarize",
            model_name="jobautomation/OpenEuroLLM-Romanian:latest",
            input_text="Direct text input for testing"
        )
        
        result = self.validator.validate_runtime(params)
        
        self.assertTrue(result.is_valid)
    
    @patch('src.services.get_ollama_service')
    def test_check_output_writable_creates_directory(self, mock_get_service):
        """Test that runtime validation creates output directory if needed."""
        mock_service = Mock()
        mock_service.is_ollama_running.return_value = True
        mock_service.get_model_names.return_value = ['jobautomation/OpenEuroLLM-Romanian:latest', 'mistral:7b']
        mock_get_service.return_value = mock_service
        
        output_dir = Path(self.temp_dir) / "new_output_dir"
        output_file = output_dir / "output.txt"
        
        params = ProcessingParameters(
            task="edit",
            model_name="jobautomation/OpenEuroLLM-Romanian:latest",
            input_text="Test text",
            output_path=str(output_file)
        )
        
        result = self.validator.validate_runtime(params)
        
        self.assertTrue(result.is_valid)
        self.assertTrue(output_dir.exists())


class TestValidationHelpers(unittest.TestCase):
    """Test validation helper methods."""
    
    def test_check_input_file_exists(self):
        """Test _check_input_file with existing file."""
        validator = ParameterValidator()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            exists, error = validator._check_input_file(temp_path)
            self.assertTrue(exists)
            self.assertIsNone(error)
        finally:
            # Python 3.7 compatible cleanup (missing_ok added in 3.8)
            try:
                Path(temp_path).unlink()
            except FileNotFoundError:
                pass
    
    def test_check_input_file_not_exists(self):
        """Test _check_input_file with non-existent file."""
        validator = ParameterValidator()
        
        exists, error = validator._check_input_file("/nonexistent/file.txt")
        
        self.assertFalse(exists)
        self.assertIsNotNone(error)
        self.assertIn("not found", error)
    
    def test_check_input_file_document_format_not_supported(self):
        """Formats that need extra libraries are rejected with an actionable message."""
        validator = ParameterValidator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for suffix in (".pdf", ".docx", ".html"):
                with self.subTest(suffix=suffix):
                    path = Path(temp_dir) / f"file{suffix}"
                    path.write_bytes(b"data")
                    
                    ok, error = validator._check_input_file(str(path))
                    
                    self.assertFalse(ok)
                    self.assertIn("not supported", error)
                    self.assertIn(".txt", error)
    
    def test_check_input_file_rejects_wrong_encoding(self):
        """A file that is not valid in the configured encoding is rejected with a hint."""
        validator = ParameterValidator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "latin.txt"
            path.write_bytes(b"\xe3\xe2\xee")
            
            ok, error = validator._check_input_file(str(path))
        
        self.assertFalse(ok)
        self.assertIn("utf-8", error)
    
    def test_suggest_fix_for_task(self):
        """Test suggest_fix for similar task names."""
        suggestion = ParameterValidator.suggest_fix("task", "diacritic")
        
        # Should suggest "diacritics"
        self.assertIn("diacritics", suggestion.lower())


if __name__ == "__main__":
    unittest.main()
