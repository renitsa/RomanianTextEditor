"""
Processor Factory Module

Creates text processor instances based on task type.
Tasks are discovered from text_actions_config.json: the task name used on the
command line is the lower-case form of the config key (e.g. TRANSLATE_RO_EN ->
translate_ro_en). A task uses the class registered for it with @register_task,
or the default TextProcessor if it has none.
"""

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.app_config import AppConfig

from src.config.app_config import get_app_config
from src.text_processor import TextProcessor, TASK_REGISTRY
from src.text_processor.chunker import VALID_CHUNKER_NAMES


class ProcessorFactory:
    """Factory for creating text processors based on task type.
    
    The task list comes from the actions config, so adding a task to
    text_actions_config.json is enough to make it available. Classes registered
    in TASK_REGISTRY add custom behaviour to a task.
    """
    
    @classmethod
    def _actions_config(cls, actions_config: Optional[Any] = None) -> Any:
        """Return the given actions config, or the one from the AppConfig singleton."""
        return actions_config if actions_config is not None else get_app_config().actions_config
    
    @classmethod
    def create_processor(cls, task: str, model_name: str,
                         config: Optional["AppConfig"] = None) -> TextProcessor:
        """Create appropriate processor for the given task.
        
        Args:
            task: The task type (e.g., 'diacritics', 'summarize')
            model_name: The name of the model to use
            config: Optional AppConfig instance. If None, uses singleton.
            
        Returns:
            An instance of the registered processor class, or TextProcessor
            
        Raises:
            ValueError: If the task is not recognized
        """
        cfg = config if config is not None else get_app_config()
        if not cls.is_valid_task(task, cfg.actions_config):
            available_tasks = cls.get_available_tasks(cfg.actions_config)
            raise ValueError(
                f"Unknown task '{task}'. Available tasks: {', '.join(available_tasks)}"
            )
        
        processor_class = TASK_REGISTRY.get(task, TextProcessor)
        return processor_class(model_name, config=cfg, task_name=task)
    
    @classmethod
    def get_available_tasks(cls, actions_config: Optional[Any] = None) -> List[str]:
        """Get list of all available task names, in config order.
        
        Args:
            actions_config: Optional actions configuration (DotDict). If None, uses singleton.
        
        Returns:
            List of valid task names
        """
        return [key.lower() for key in cls._actions_config(actions_config).keys()]
    
    @classmethod
    def is_valid_task(cls, task: str, actions_config: Optional[Any] = None) -> bool:
        """Check if a task name is valid.
        
        Args:
            task: The task name to validate
            actions_config: Optional actions configuration (DotDict). If None, uses singleton.
            
        Returns:
            True if the task is valid, False otherwise
        """
        return bool(task) and task in cls.get_available_tasks(actions_config)
    
    @classmethod
    def validate_config(cls, actions_config: Any) -> Tuple[List[str], List[str]]:
        """Validate the actions config against the registry and the chunker names.
        
        Checks that:
        - every config key is upper-case, so it maps back to a task name
        - every task has the required fields (DESC, PROMPT)
        - every chunker name used by a task exists
        - every registered task class has a config entry
        
        Args:
            actions_config: The actions configuration object (DotDict)
            
        Returns:
            Tuple of (errors, warnings) where:
            - errors: Critical inconsistencies that should prevent startup
            - warnings: Non-critical issues that can be logged
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        config_keys = list(actions_config.keys()) if hasattr(actions_config, 'keys') else []
        
        for config_key in config_keys:
            if config_key != config_key.upper():
                errors.append(f"Config entry '{config_key}' must be upper-case (e.g. '{config_key.upper()}')")
            
            task_config = actions_config[config_key]
            for field_name in ('DESC', 'PROMPT'):
                if not hasattr(task_config, field_name):
                    errors.append(f"Config entry '{config_key}' missing required field '{field_name}'")
            
            for chunker_name in getattr(task_config, 'CHUNKERS', []):
                if chunker_name not in VALID_CHUNKER_NAMES:
                    errors.append(
                        f"Config entry '{config_key}' uses unknown chunker '{chunker_name}'. "
                        f"Valid chunkers: {', '.join(sorted(VALID_CHUNKER_NAMES))}"
                    )
        
        for task_name in TASK_REGISTRY:
            if task_name.upper() not in config_keys:
                errors.append(
                    f"Registered task '{task_name}' missing config entry '{task_name.upper()}'"
                )
        
        return errors, warnings
    
    @classmethod
    def get_task_config(cls, actions_config: Any, task: str) -> Any:
        """Get the configuration for a specific task.
        
        Args:
            actions_config: The actions configuration object (DotDict)
            task: The task name (e.g., 'diacritics', 'summarize')
            
        Returns:
            The task configuration object, or None if not found
        """
        return getattr(actions_config, task.upper(), None) if task else None
    
    @classmethod
    def get_task_descriptions(cls, actions_config: Optional[Any] = None) -> Dict[str, str]:
        """Get task descriptions from configuration.
        
        Args:
            actions_config: Optional actions configuration (DotDict). If None, uses singleton.
        
        Returns:
            Dictionary mapping task names to their descriptions
        """
        cfg = cls._actions_config(actions_config)
        return {
            key.lower(): getattr(cfg[key], 'DESC', "Process text")
            for key in cfg.keys()
        }