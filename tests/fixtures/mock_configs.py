"""
Mock configurations for testing.
Provides various config scenarios without requiring actual JSON files.
"""

VALID_ACTION_CONFIG = {
    "DESC": "Test action description",
    "PROMPT": "Test prompt for the action",
    "CHUNKERS": ["sentence_split", "size_optimizing"],
    "INPUT_LANGUAGE": "ro"
}

VALID_ACTION_CONFIG_NO_CHUNKERS = {
    "DESC": "Test action without chunking",
    "PROMPT": "Test prompt",
    "CHUNKERS": [],
    "INPUT_LANGUAGE": "ro"
}

VALID_ACTION_CONFIG_ENGLISH = {
    "DESC": "English test action",
    "PROMPT": "Test prompt in English",
    "CHUNKERS": ["sentence_split"],
    "INPUT_LANGUAGE": "en"
}

INVALID_ACTION_CONFIG_MISSING_DESC = {
    "PROMPT": "Test prompt",
    "CHUNKERS": ["sentence_split"],
    "INPUT_LANGUAGE": "ro"
}

INVALID_ACTION_CONFIG_EMPTY_PROMPT = {
    "DESC": "Test description",
    "PROMPT": "",
    "CHUNKERS": ["sentence_split"],
    "INPUT_LANGUAGE": "ro"
}

INVALID_ACTION_CONFIG_WRONG_CHUNKER_TYPE = {
    "DESC": "Test description",
    "PROMPT": "Test prompt",
    "CHUNKERS": "not_a_list",  # Should be list
    "INPUT_LANGUAGE": "ro"
}

INVALID_ACTION_CONFIG_INVALID_CHUNKER = {
    "DESC": "Test description",
    "PROMPT": "Test prompt",
    "CHUNKERS": ["invalid_chunker_name"],
    "INPUT_LANGUAGE": "ro"
}
