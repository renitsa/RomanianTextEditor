"""Dictionary utilities for the Romanian Text Editor project."""

from collections import OrderedDict
from typing import Any, List

class DotDict(dict):
    """Dictionary that supports dot notation access with deep nesting
     and list of dicts support."""
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Convert all existing values
        for key, value in list(self.items()): 
            self[key] = self._convert_value(value)
    
    def _convert_value(self, value: Any) -> Any:
        """Convert a value to DotDict format if needed."""
        if isinstance(value, (dict, OrderedDict)) and not isinstance(value, DotDict):
            return DotDict(value)
        elif isinstance(value, list):
            return self._convert_list(value)
        return value
    
    def _convert_list(self, lst: List[Any]) -> List[Any]:
        """Convert any dictionaries in a list to DotDict objects."""
        converted_list = []
        for item in lst:
            converted_list.append(self._convert_value(item))
        return converted_list
    
    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError:
            available_keys = list(self.keys())
            raise AttributeError(f"'DotDict' object has no attribute '{key}'. Available keys: {available_keys}")
    
    def __setattr__(self, key: str, value: Any) -> None:
        """Set attribute with automatic conversion."""
        self[key] = self._convert_value(value)
    
    def __delattr__(self, key: str) -> None:
        try:
            del self[key]
        except KeyError:
            available_keys = list(self.keys())
            raise AttributeError(f"'DotDict' object has no attribute '{key}'. Available keys: {available_keys}")

if __name__ == "__main__":
    print("Tests have been migrated to tests/unit/test_dict_utils.py")
    print("Run: python -m unittest tests.unit.test_dict_utils")
    print("Or: python -m unittest discover tests")
