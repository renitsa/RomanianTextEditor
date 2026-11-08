import json
from pathlib import Path
from typing import Any, Optional, Union

def read_json(file_path: Union[str, Path]) -> Optional[Any]:
    """Read a JSON file and return its content as a Python object."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading JSON file {file_path}: {e}")
        return None
