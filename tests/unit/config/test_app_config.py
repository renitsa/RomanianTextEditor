"""
Unit tests for app_config module.
"""

import unittest

from src.config.app_config import (
    get_app_config,
    get_config_summary,
    reset_app_config
)


class TestAppConfig(unittest.TestCase):
    """Test cases for app_config module."""
    
    def setUp(self):
        """Set up test fixtures - reset config before each test."""
        reset_app_config()
    
    def tearDown(self):
        """Clean up after tests - reset config."""
        reset_app_config()
    
    def test_app_config_singleton(self):
        """Test that get_app_config returns the same instance."""
        config1 = get_app_config()
        config2 = get_app_config()
        
        self.assertIs(config1, config2, "AppConfig should be a singleton")
    
    def test_app_config_loads_successfully(self):
        """Test that config loads without errors."""
        config = get_app_config()
        
        self.assertIsNotNone(config, "Config should not be None")
        self.assertTrue(config.load_success, "Config should load successfully")
    
    def test_app_config_has_all_sub_configs(self):
        """Test that all sub-configs are loaded."""
        config = get_app_config()
        
        self.assertIsNotNone(config.logging_config, "Logging config should be loaded")
        self.assertIsNotNone(config.file_config, "File config should be loaded")
        self.assertIsNotNone(config.text_config, "Text config should be loaded")
        self.assertIsNotNone(config.llm_services_config, "LLM services config should be loaded")
        self.assertIsNotNone(config.actions_config, "Actions config should be loaded")
    
    def test_config_summary_after_load(self):
        """Test config summary after loading."""
        config = get_app_config()
        summary = get_config_summary()
        
        self.assertTrue(summary['app_config_loaded'], "Config should be loaded")
        self.assertTrue(summary['app_config_load_success'], "Config load should be successful")
    
    def test_reset_app_config(self):
        """Test that reset_app_config clears the config."""
        # Load config
        config = get_app_config()
        self.assertIsNotNone(config)
        
        summary_before = get_config_summary()
        self.assertTrue(summary_before['app_config_loaded'])
        
        # Reset
        reset_app_config()
        
        summary_after = get_config_summary()
        self.assertFalse(summary_after['app_config_loaded'])
    
    def test_logging_config_structure(self):
        """Test that logging config has expected structure."""
        config = get_app_config()
        logging_cfg = config.logging_config
        
        self.assertIsNotNone(logging_cfg, "Logging config should not be None")
        # Check for actual fields in logging_config.json
        self.assertTrue(hasattr(logging_cfg, 'CONSOLE_LEVEL'), "Should have CONSOLE_LEVEL")
        self.assertTrue(hasattr(logging_cfg, 'LOG_TO_FILE'), "Should have log to file config")
    
    def test_file_config_structure(self):
        """Test that file config has expected structure."""
        config = get_app_config()
        file_cfg = config.file_config
        
        self.assertIsNotNone(file_cfg, "File config should not be None")
        self.assertTrue(hasattr(file_cfg, 'DEFAULT_ENCODING'), "Should have default encoding")
        self.assertTrue(hasattr(file_cfg, 'CREATE_DIRS_IF_MISSING'), "Should have create dirs config")
        self.assertTrue(hasattr(file_cfg, 'OUTPUT_TIMESTAMP_FORMAT'), "Should have output timestamp format")
    
    def test_llm_services_config_structure(self):
        """Test that LLM services config has expected structure."""
        config = get_app_config()
        llm_cfg = config.llm_services_config
        
        self.assertIsNotNone(llm_cfg, "LLM services config should not be None")
        self.assertTrue(hasattr(llm_cfg, 'OLLAMA'), "Should have Ollama config")
    
    def test_actions_config_structure(self):
        """Test that actions config has expected structure."""
        config = get_app_config()
        actions_cfg = config.actions_config
        
        self.assertIsNotNone(actions_cfg, "Actions config should not be None")
        # Check for common action configs
        self.assertTrue(hasattr(actions_cfg, 'DIACRITICS'), "Should have diacritics config")
        self.assertTrue(hasattr(actions_cfg, 'SUMMARIZE'), "Should have summarize config")
    
    def test_text_config_has_abbreviations(self):
        """Test that text config has abbreviation sets."""
        config = get_app_config()
        text_cfg = config.text_config
        
        self.assertIsNotNone(text_cfg, "Text config should not be None")
        
        # Check if abbreviation fields exist
        if hasattr(text_cfg, 'COMMON_RO_ABBREVIATIONS'):
            self.assertIsInstance(text_cfg.COMMON_RO_ABBREVIATIONS, set, "Romanian abbreviations should be a set")
        
        if hasattr(text_cfg, 'COMMON_ENG_ABBREVIATIONS'):
            self.assertIsInstance(text_cfg.COMMON_ENG_ABBREVIATIONS, set, "English abbreviations should be a set")


if __name__ == '__main__':
    unittest.main()
