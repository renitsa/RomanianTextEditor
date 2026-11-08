"""
Text Processor Module

Provides the text processor used by every task. A task is defined by an entry
in text_actions_config.json (prompt, chunkers, language). A task that needs
extra behaviour subclasses TextProcessor, overrides preprocess/postprocess
and registers itself with @register_task.

"""

from typing import Callable, Dict, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from src.utils.dict_utils import DotDict
    from src.config.app_config import AppConfig

from src.services.ollama_service import OllamaService
from src.config.app_config import get_app_config
from src.utils.app_logger import get_logger


# Registry of task names to processor classes with custom behaviour.
# Tasks that only need a prompt are not listed here: they use TextProcessor itself.
TASK_REGISTRY: Dict[str, Type["TextProcessor"]] = {}


def register_task(name: str) -> Callable[[Type["TextProcessor"]], Type["TextProcessor"]]:
    """Class decorator that registers a processor class under a task name.

    The task name is the name used on the command line (e.g. 'diacritics') and
    its upper-case form is the key of the task in text_actions_config.json.

    Args:
        name: Lower-case task name

    Returns:
        The decorator that registers the class and returns it unchanged

    Raises:
        ValueError: If the name is empty, not lower-case, or already registered
            to a different class
    """
    if not name or name != name.lower():
        raise ValueError(f"Task name '{name}' must be a non-empty lower-case string")

    def decorator(cls: Type["TextProcessor"]) -> Type["TextProcessor"]:
        existing = TASK_REGISTRY.get(name)
        if existing is not None and existing is not cls:
            raise ValueError(f"Task '{name}' is already registered to {existing.__name__}")
        cls.TASK_NAME = name
        TASK_REGISTRY[name] = cls
        return cls

    return decorator


class TextProcessor:
    """Processes text for one task using an LLM, with the prompt taken from config.

    Template Method: process_text() fixes the order of the steps
    (preprocess -> LLM call -> postprocess). Subclasses override the hooks only.
    """

    TASK_NAME: Optional[str] = None

    def __init__(self, model_name: str, 
                 base_url: Optional[str] = None, 
                 config: Optional["AppConfig"] = None,
                 task_name: Optional[str] = None) -> None:
        """Initialize the text processor.
        
        Args:
            model_name: Name of the LLM model to use
            base_url: Optional base URL for the LLM service. If not provided, 
                     uses the URL from configuration.
            config: Optional AppConfig instance. If None, uses singleton.
            task_name: Task name (e.g. 'summarize'). Defaults to the task name
                      the class was registered under.

        Raises:
            ValueError: If no task name is available, or the task has no
                entry in text_actions_config.json
        """

        self.logger = get_logger("RomanianTextEditor.TextProcessor")
        cfg = config if config is not None else get_app_config()

        self.model_name: str = model_name
        self.task_name: Optional[str] = task_name if task_name is not None else self.TASK_NAME
        if not self.task_name:
            raise ValueError(
                f"{self.__class__.__name__} needs a task name: pass task_name "
                f"or register the class with @register_task"
            )
        self.config_key: str = self.task_name.upper()
        
        # DotDict is a dict-like object with dynamic attributes, 
        # which confuses most type checkers, hence the ignore comment
        self.llm_services_cfg: "DotDict" = cfg.llm_services_config  # type: ignore[assignment]
        self.actions_cfg: "DotDict" = cfg.actions_config  # type: ignore[assignment]
        if self.config_key not in self.actions_cfg:
            raise ValueError(
                f"Task '{self.task_name}' has no entry '{self.config_key}' in text_actions_config.json. "
                f"Available entries: {', '.join(self.actions_cfg.keys())}"
            )
        self.base_url: str = base_url if base_url is not None else self.llm_services_cfg.OLLAMA.url
        
        # Use OllamaService
        from src.services import get_ollama_service
        self.ollama_service: OllamaService = get_ollama_service(base_url=self.base_url, config=cfg)
        
        self.logger.debug(f"{self.__class__.__name__}: Initialized with model: {model_name}, base_url: {self.base_url}")
        
    @property
    def prompt(self) -> str:
        """The prompt of this task, as configured in text_actions_config.json."""
        return self.actions_cfg[self.config_key].PROMPT

    def preprocess(self, text: str) -> str:
        """Hook: prepare a chunk before it is sent to the LLM. Returns it unchanged by default."""
        return text

    def postprocess(self, text: str) -> str:
        """Hook: clean the LLM response for a chunk. Returns it unchanged by default."""
        return text

    def process_text(self, text: str, custom_prompt: Optional[str] = None) -> Optional[str]:
        """Process one chunk of text: preprocess, ask the LLM, postprocess.
        
        Args:
            text: The text to process
            custom_prompt: Optional prompt to use instead of the configured one
            
        Returns:
            The processed text, or None if the LLM call fails
        """
        prompt = custom_prompt if custom_prompt else self.prompt
        response = self.ollama_service.generate_response(
            self.model_name, f'{prompt} {self.preprocess(text)}'
        )
        return None if response is None else self.postprocess(response)


@register_task("diacritics")
class DiacriticAdder(TextProcessor):
    """Adds diacritics to Romanian text.

    Example of a task with custom behaviour: LLMs often answer with the legacy
    cedilla letters (ş, ţ) instead of the correct comma-below ones (ș, ț).
    """

    CEDILLA_TO_COMMA_BELOW = str.maketrans("şŞţŢ", "șȘțȚ")

    def postprocess(self, text: str) -> str:
        """Replace cedilla letters with the correct comma-below letters."""
        return text.translate(self.CEDILLA_TO_COMMA_BELOW)

