import json
import urllib.request
import urllib.error
from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.app_config import AppConfig

from src.config.app_config import get_app_config
from src.utils.app_logger import get_logger

# --- Module-level singleton storage ---
_ollama_service: Optional["OllamaService"] = None


class OllamaService:
    """
    Service class for managing Ollama model interactions.
    """
    
    def __init__(self, base_url: Optional[str] = None,
                 check_timeout: Optional[int] = None,
                 generate_timeout: Optional[int] = None,
                 config: Optional["AppConfig"] = None):
        """Initialize the Ollama service.
        
        Args:
            base_url: The base URL for the Ollama API. If not provided, uses config value.
            check_timeout: Timeout for checking if service is running. If not provided, uses config value.
            generate_timeout: Timeout for text generation. If not provided, uses config value.
            config: Optional AppConfig instance. If None, uses singleton.
        """
        # Initialize logger and config
        self.logger = get_logger("OllamaService")
        self.config = config if config is not None else get_app_config()
        # Determine base URL and timeouts from config or parameters
        if base_url is not None:
            self.base_url = base_url
            self.logger.debug(f"Using provided base_url: {base_url}")
        else:
            # Get config (injected or default)
            self.base_url = self.config.llm_services_config.OLLAMA.url
            self.logger.debug(f"Using base_url from config: {self.base_url}")
        
        # Set timeouts from parameters or config
        self.check_timeout = check_timeout if check_timeout is not None else self.config.llm_services_config.OLLAMA.check_timeout
        self.generate_timeout = generate_timeout if generate_timeout is not None else self.config.llm_services_config.OLLAMA.generate_timeout
        self.logger.debug(f"Using timeouts - check: {self.check_timeout}s, generate: {self.generate_timeout}s")
        
        self.logger.debug(f"OllamaService initialized with base_url: {self.base_url}")
    
    def is_ollama_running(self) -> bool:
        """Check if Ollama service is running.
        
        Returns:
            True if Ollama service is accessible, False otherwise
            
        Note:
            This method does not log on success to avoid cluttering logs
            when called frequently. Callers should log as appropriate for their context.
        """
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=self.check_timeout) as response:
                is_running = response.status == 200
                if not is_running:
                    self.logger.warning(f"Ollama service returned status: {response.status}")
                return is_running
        except urllib.error.URLError as e:
            self.logger.error(f"Ollama service not accessible: {e.reason}")
            return False
        except OSError as e:
            self.logger.error(f"OS error checking Ollama service: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error checking Ollama service: {e}")
            return False
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available models with full information from Ollama.
        
        Returns:
            List of model dictionaries containing full model information 
            (name, size, modified_at, etc.). Returns empty list if service 
            is not accessible or on error.
        """
        if not self.is_ollama_running():
            self.logger.warning("Cannot list models: Ollama service not running")
            return []
        
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=self.check_timeout) as response:
                data = json.loads(response.read().decode())
                models = data.get("models", [])
                self.logger.debug(f"Found {len(models)} models with full info")
                return models
                    
        except urllib.error.URLError as e:
            self.logger.error(f"Network error listing models: {e.reason}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response when listing models: {e}")
            return []
        except OSError as e:
            self.logger.error(f"OS error listing models: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error listing models: {e}")
            return []
    
    def get_model_names(self) -> List[str]:
        """Get list of available model names only from Ollama.
        
        Returns:
            List of model names as strings. Returns empty list if service 
            is not accessible or on error.
        """
        models = self.get_models()
        model_names = [model.get("name", "") for model in models if model.get("name")]
        self.logger.debug(f"Extracted {len(model_names)} model names: {model_names}")
        return model_names
    
    def model_exists(self, model_name: str) -> bool:
        """Check if a specific model exists in Ollama.
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            True if model exists, False otherwise
        """
        if not model_name:
            self.logger.warning("model_exists called with empty model_name")
            return False
            
        model_names = self.get_model_names()
        exists = model_name in model_names
        
        if exists:
            self.logger.debug(f"Model '{model_name}' exists")
        else:
            self.logger.warning(f"Model '{model_name}' not found. Available models: {model_names}")
        
        return exists
    
    def generate_response(self, model: str, prompt: str, **kwargs) -> Optional[str]:
        """Generate a response using the specified model.
        
        Args:
            model: Name of the model to use
            prompt: The prompt text
            **kwargs: Additional top-level fields of the Ollama /api/generate request.
                Model settings such as temperature must be passed inside an
                'options' dict, e.g. options={"temperature": 0.2}.
            
        Returns:
            Generated response text or None if failed
            
        """
        # Validate inputs
        if not model:
            self.logger.error("generate_response called with empty model name")
            return None
            
        if not prompt:
            self.logger.warning("generate_response called with empty prompt")
            return None
        
        # Prepare payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        
        self.logger.debug(f"Generating response with model '{model}', prompt length: {len(prompt)} chars")
        if kwargs:
            self.logger.debug(f"Additional generation parameters: {kwargs}")
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=self.generate_timeout) as response:
                result = json.loads(response.read().decode())
                response_text = result.get("response", "")
                
                if response_text:
                    self.logger.debug(f"Successfully generated response, length: {len(response_text)} chars")
                    self.logger.debug(f"Response preview: {response_text[:100]}...")
                    return response_text
                else:
                    self.logger.warning("Generated response is empty")
                    return None
                    
        except urllib.error.HTTPError as e:
            self.logger.error(f"HTTP error generating response: {e.code} {e.reason}")
            return None
        except urllib.error.URLError as e:
            self.logger.error(f"Network error generating response: {e.reason}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response: {e}")
            return None
        except OSError as e:
            self.logger.error(f"OS error generating response: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error generating response: {e}")
            return None


# --- Module-level functions ---

def get_ollama_service(base_url: Optional[str] = None,
                      check_timeout: Optional[int] = None,
                      generate_timeout: Optional[int] = None,
                      config: Optional["AppConfig"] = None) -> OllamaService:
    """Get the OllamaService instance, creating it if necessary (Singleton pattern).
    
    Args:
        base_url: The base URL for the Ollama API. Only used on first creation.
        check_timeout: Timeout for checking if service is running. Only used on first creation.
        generate_timeout: Timeout for text generation. Only used on first creation.
        config: Optional AppConfig instance. Only used on first creation.
    
    Returns:
        OllamaService singleton instance
        
    """
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService(
            base_url=base_url,
            check_timeout=check_timeout,
            generate_timeout=generate_timeout,
            config=config
        )
    return _ollama_service


def is_ollama_service_loaded() -> bool:
    """Check if OllamaService singleton has been created."""
    return _ollama_service is not None


def reset_ollama_service() -> None:
    """Reset the OllamaService singleton for testing purposes."""
    global _ollama_service
    _ollama_service = None
