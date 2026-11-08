"""
Unit tests for OllamaService.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import urllib.error
from src.services.ollama_service import OllamaService, get_ollama_service


class TestOllamaServiceInitialization(unittest.TestCase):
    """Test OllamaService initialization."""
    
    def test_init_with_default_config(self):
        """Service should initialize with default config."""
        service = OllamaService()
        
        self.assertIsNotNone(service.base_url)
        self.assertIsNotNone(service.check_timeout)
        self.assertIsNotNone(service.generate_timeout)
        self.assertIsNotNone(service.logger)
    
    def test_init_with_custom_config(self):
        """Service should accept custom config, URL, and timeouts."""
        from src.config.app_config import get_app_config
        config = get_app_config()
        custom_url = "http://custom:11434"
        
        service = OllamaService(config=config, base_url=custom_url, check_timeout=10, generate_timeout=120)
        
        self.assertIs(service.config, config)
        self.assertEqual(service.base_url, custom_url)
        self.assertEqual(service.check_timeout, 10)
        self.assertEqual(service.generate_timeout, 120)


class TestOllamaServiceAvailability(unittest.TestCase):
    """Test Ollama service availability checking."""
    
    @patch('urllib.request.urlopen')
    def test_is_ollama_running_success(self, mock_urlopen):
        """Should return True when Ollama is running."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        service = OllamaService()
        result = service.is_ollama_running()
        
        self.assertTrue(result)
    
    @patch('urllib.request.urlopen')
    def test_is_ollama_running_connection_error(self, mock_urlopen):
        """Should return False when connection fails."""
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        
        service = OllamaService()
        result = service.is_ollama_running()
        
        self.assertFalse(result)
    
    @patch('urllib.request.urlopen')
    def test_is_ollama_running_timeout(self, mock_urlopen):
        """Should return False on timeout."""
        mock_urlopen.side_effect = TimeoutError("Request timed out")
        
        service = OllamaService()
        result = service.is_ollama_running()
        
        self.assertFalse(result)
    
    @patch('urllib.request.urlopen')
    def test_is_ollama_running_http_error(self, mock_urlopen):
        """Should return False on HTTP error."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "http://test", 500, "Internal Server Error", {}, None
        )
        
        service = OllamaService()
        result = service.is_ollama_running()
        
        self.assertFalse(result)


class TestOllamaServiceModelRetrieval(unittest.TestCase):
    """Test model retrieval from Ollama."""
    
    @patch('src.services.ollama_service.OllamaService.is_ollama_running')
    @patch('urllib.request.urlopen')
    def test_get_model_names_success(self, mock_urlopen, mock_is_running):
        """Should return list of model names."""
        # Mock Ollama as running
        mock_is_running.return_value = True
        
        # Mock response with model list
        mock_data = {
            "models": [
                {"name": "mistral:7b"},
                {"name": "codellama:13b"},
                {"name": "jobautomation/OpenEuroLLM-Romanian:latest"}
            ]
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        service = OllamaService()
        models = service.get_model_names()
        
        self.assertEqual(len(models), 3)
        self.assertIn("jobautomation/OpenEuroLLM-Romanian:latest", models)
        self.assertIn("mistral:7b", models)
        self.assertIn("codellama:13b", models)
    
    @patch('urllib.request.urlopen')
    def test_get_model_names_empty_list(self, mock_urlopen):
        """Should return empty list when no models available."""
        mock_data = {"models": []}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        service = OllamaService()
        models = service.get_model_names()
        
        self.assertEqual(len(models), 0)
    
    @patch('urllib.request.urlopen')
    def test_get_model_names_connection_error(self, mock_urlopen):
        """Should return empty list on connection error."""
        mock_urlopen.side_effect = urllib.error.URLError("Connection failed")
        
        service = OllamaService()
        models = service.get_model_names()
        
        self.assertEqual(len(models), 0)
    
    @patch('urllib.request.urlopen')
    def test_get_model_names_invalid_json(self, mock_urlopen):
        """Should return empty list on invalid JSON."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"invalid json"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        service = OllamaService()
        models = service.get_model_names()
        
        self.assertEqual(len(models), 0)


class TestOllamaServiceTextGeneration(unittest.TestCase):
    """Test text generation with Ollama."""
    
    @patch('urllib.request.urlopen')
    def test_generate_response_success(self, mock_urlopen):
        """Should generate text successfully."""
        # Mock single response (not streaming)
        mock_response = MagicMock()
        # Mock the read().decode() chain
        mock_bytes = MagicMock()
        mock_bytes.decode.return_value = json.dumps({"response": "Hello world!"})
        mock_response.read.return_value = mock_bytes
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        service = OllamaService()
        result = service.generate_response(
            model="test-model",
            prompt="Test prompt",
            system_prompt="System"
        )
        
        self.assertEqual(result, "Hello world!")
    
    @patch('urllib.request.urlopen')
    def test_generate_response_empty_response(self, mock_urlopen):
        """Should handle empty response."""
        # Mock response with empty text
        mock_response_data = json.dumps({"response": ""})
        mock_response = MagicMock()
        mock_response.read.return_value.decode.return_value = mock_response_data
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        service = OllamaService()
        result = service.generate_response(
            model="test-model",
            prompt="Test"
        )
        
        # Empty response returns None as per implementation
        self.assertIsNone(result)
    
    @patch('urllib.request.urlopen')
    def test_generate_response_connection_error(self, mock_urlopen):
        """Should return error message on connection failure."""
        mock_urlopen.side_effect = urllib.error.URLError("Connection failed")
        
        service = OllamaService()
        result = service.generate_response(
            model="test-model",
            prompt="Test"
        )
        
        # Method returns None on connection errors
        self.assertIsNone(result)
    
    @patch('urllib.request.urlopen')
    def test_generate_response_with_options(self, mock_urlopen):
        """Model options should be nested in the Ollama request payload."""
        mock_response_data = json.dumps({"response": "Test"})
        mock_response = MagicMock()
        mock_response.read.return_value.decode.return_value = mock_response_data
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        service = OllamaService()
        options = {"temperature": 0.7}
        result = service.generate_response(
            model="test-model",
            prompt="Test",
            options=options
        )
        
        self.assertEqual(result, "Test")
        request = mock_urlopen.call_args[0][0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["options"], options)
        self.assertNotIn("temperature", payload)
    
    @patch('urllib.request.urlopen')
    def test_generate_response_timeout(self, mock_urlopen):
        """Should handle timeout gracefully."""
        mock_urlopen.side_effect = TimeoutError("Request timed out")
        
        service = OllamaService()
        result = service.generate_response(
            model="test-model",
            prompt="Test"
        )
        
        # Method returns None on timeout
        self.assertIsNone(result)


class TestOllamaServiceSingleton(unittest.TestCase):
    """Test OllamaService singleton pattern."""
    
    def test_get_ollama_service_returns_instance(self):
        """get_ollama_service should return OllamaService instance."""
        service = get_ollama_service()
        
        self.assertIsInstance(service, OllamaService)
    
    def test_get_ollama_service_returns_same_instance(self):
        """get_ollama_service should return same instance."""
        service1 = get_ollama_service()
        service2 = get_ollama_service()
        
        self.assertIs(service1, service2)


if __name__ == '__main__':
    unittest.main()
