"""
Unit tests for DotDict functionality.
Migrated from src/utils/dict_utils.py __main__ section.
"""
import unittest
from src.utils.dict_utils import DotDict


class TestDotDictBasicAccess(unittest.TestCase):
    """Test basic dictionary access functionality."""
    
    def test_simple_attribute_access(self):
        """Should access simple values via dot notation."""
        basic_dict = DotDict({
            'name': 'test',
            'value': 42,
            'enabled': True
        })
        
        self.assertEqual(basic_dict.name, 'test')
        self.assertEqual(basic_dict.value, 42)
        self.assertTrue(basic_dict.enabled)
    
    def test_bracket_access_still_works(self):
        """Should still support traditional bracket notation."""
        basic_dict = DotDict({'name': 'test'})
        
        self.assertEqual(basic_dict['name'], 'test')
        self.assertEqual(basic_dict.name, basic_dict['name'])
    
    def test_both_access_methods_work(self):
        """Both key and dot notation access should work."""
        both_access = DotDict({
            'name': 'test',
            'config': {
                'debug': True,
                'timeout': 30
            }
        })
        
        # Dictionary-style access
        self.assertEqual(both_access['name'], 'test')
        self.assertTrue(both_access['config']['debug'])
        
        # Dot notation access
        self.assertEqual(both_access.name, 'test')
        self.assertTrue(both_access.config.debug)
        
        # Mixed access
        self.assertEqual(both_access['config'].timeout, 30)
        self.assertEqual(both_access.config['timeout'], 30)
    
    def test_both_assignment_methods_work(self):
        """Both key and dot notation assignment should work."""
        both_access = DotDict({'initial': 'value'})
        
        both_access['new_key'] = 'dictionary_style'
        both_access.new_attr = 'dot_style'
        
        self.assertEqual(both_access.new_key, 'dictionary_style')
        self.assertEqual(both_access['new_attr'], 'dot_style')


class TestDotDictNestedAccess(unittest.TestCase):
    """Test nested dictionary access."""
    
    def test_nested_dict_conversion(self):
        """Should convert nested dicts to DotDict."""
        nested_dict = DotDict({
            'database': {
                'host': 'localhost',
                'port': 5432,
                'credentials': {
                    'username': 'admin',
                    'password': 'secret'
                }
            }
        })
        
        self.assertEqual(nested_dict.database.host, 'localhost')
        self.assertEqual(nested_dict.database.port, 5432)
        self.assertEqual(nested_dict.database.credentials.username, 'admin')
        self.assertEqual(nested_dict.database.credentials.password, 'secret')
    
    def test_nested_dict_types(self):
        """Nested dicts should be DotDict instances."""
        nested_dict = DotDict({
            'level1': {
                'level2': {
                    'value': 'deep'
                }
            }
        })
        
        self.assertIsInstance(nested_dict.level1, DotDict)
        self.assertIsInstance(nested_dict.level1.level2, DotDict)
    
    def test_deeply_nested_structure(self):
        """Should handle deeply nested structures (5 levels)."""
        deep = DotDict({
            'l1': {
                'l2': {
                    'l3': {
                        'l4': {
                            'l5': {
                                'value': 'deep_value',
                                'number': 999
                            }
                        }
                    }
                }
            }
        })
        
        self.assertEqual(deep.l1.l2.l3.l4.l5.value, 'deep_value')
        self.assertEqual(deep.l1.l2.l3.l4.l5.number, 999)


class TestDotDictListHandling(unittest.TestCase):
    """Test list handling - with and without dicts."""
    
    def test_lists_without_dicts_unchanged(self):
        """Lists without dicts should remain as lists."""
        list_dict = DotDict({
            'simple_list': ['apple', 'banana', 'cherry'],
            'number_list': [1, 2, 3, 4, 5],
            'mixed_list': ['text', 42, True, None]
        })
        
        # Lists should be lists
        self.assertIsInstance(list_dict.simple_list, list)
        self.assertIsInstance(list_dict.number_list, list)
        self.assertIsInstance(list_dict.mixed_list, list)
        
        # Content should be unchanged
        self.assertEqual(list_dict.simple_list, ['apple', 'banana', 'cherry'])
        self.assertEqual(list_dict.number_list, [1, 2, 3, 4, 5])
        
        # Types should be preserved
        self.assertIsInstance(list_dict.mixed_list[0], str)
        self.assertIsInstance(list_dict.mixed_list[1], int)
        self.assertIsInstance(list_dict.mixed_list[2], bool)
        self.assertIsNone(list_dict.mixed_list[3])
    
    def test_lists_with_only_dicts(self):
        """Lists containing only dicts should convert to DotDict."""
        list_dict = DotDict({
            'servers': [
                {'name': 'server1', 'ip': '192.168.1.1'},
                {'name': 'server2', 'ip': '192.168.1.2'},
                {'name': 'server3', 'ip': '192.168.1.3'}
            ]
        })
        
        # List should still be a list
        self.assertIsInstance(list_dict.servers, list)
        
        # Items should be DotDict
        self.assertIsInstance(list_dict.servers[0], DotDict)
        self.assertIsInstance(list_dict.servers[1], DotDict)
        self.assertIsInstance(list_dict.servers[2], DotDict)
        
        # Access should work
        self.assertEqual(list_dict.servers[0].name, 'server1')
        self.assertEqual(list_dict.servers[1].ip, '192.168.1.2')
    
    def test_lists_with_mixed_content(self):
        """Lists with mixed types (some dicts, some not) should stay as list."""
        list_dict = DotDict({
            'mixed': [
                'simple_string',
                42,
                {'config': {'timeout': 30, 'retries': 3}},
                ['nested', 'list'],
                {'settings': {'debug': True}},
                None
            ]
        })
        
        self.assertIsInstance(list_dict.mixed, list)
        self.assertEqual(len(list_dict.mixed), 6)
        
        # Check types
        self.assertIsInstance(list_dict.mixed[0], str)
        self.assertIsInstance(list_dict.mixed[1], int)
        self.assertIsInstance(list_dict.mixed[2], DotDict)
        self.assertIsInstance(list_dict.mixed[3], list)
        self.assertIsInstance(list_dict.mixed[4], DotDict)
        self.assertIsNone(list_dict.mixed[5])
        
        # Dicts in mixed list should be DotDict and work
        self.assertEqual(list_dict.mixed[2].config.timeout, 30)
        self.assertTrue(list_dict.mixed[4].settings.debug)
    
    def test_nested_lists_with_dictionaries(self):
        """Should handle nested lists with dictionaries."""
        nested_lists = DotDict({
            'matrix': [
                [
                    {'cell': 'A1', 'value': 10},
                    {'cell': 'A2', 'value': 20}
                ],
                [
                    {'cell': 'B1', 'value': 30},
                    {'cell': 'B2', 'value': 40}
                ]
            ]
        })
        
        self.assertEqual(nested_lists.matrix[0][0].cell, 'A1')
        self.assertEqual(nested_lists.matrix[0][0].value, 10)
        self.assertEqual(nested_lists.matrix[1][1].cell, 'B2')
        self.assertEqual(nested_lists.matrix[1][1].value, 40)


class TestDotDictEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_empty_dict(self):
        """Should handle empty dictionary."""
        empty = DotDict({})
        self.assertEqual(len(empty), 0)
    
    def test_none_values(self):
        """Should handle None values."""
        with_none = DotDict({'value': None})
        self.assertIsNone(with_none.value)
    
    def test_empty_string_values(self):
        """Should handle empty strings."""
        with_empty = DotDict({'text': ''})
        self.assertEqual(with_empty.text, '')
    
    def test_zero_values(self):
        """Should handle zero/false values correctly."""
        with_zeros = DotDict({
            'zero': 0,
            'false': False,
            'empty_list': []
        })
        
        self.assertEqual(with_zeros.zero, 0)
        self.assertFalse(with_zeros.false)
        self.assertEqual(with_zeros.empty_list, [])
    
    def test_attribute_error_on_missing_key(self):
        """Should raise AttributeError for missing keys."""
        d = DotDict({'exists': 'value'})
        
        with self.assertRaises(AttributeError) as cm:
            _ = d.missing_key
        
        self.assertIn('DotDict', str(cm.exception))
        self.assertIn('missing_key', str(cm.exception))


class TestDotDictComplexScenarios(unittest.TestCase):
    """Test complex real-world scenarios."""
    
    def test_config_like_structure(self):
        """Should handle configuration-like nested structures."""
        config = DotDict({
            'app': {
                'name': 'TestApp',
                'version': '1.0',
                'features': {
                    'logging': True,
                    'caching': False
                }
            },
            'database': {
                'connections': [
                    {'name': 'primary', 'url': 'db1.example.com'},
                    {'name': 'replica', 'url': 'db2.example.com'}
                ]
            }
        })
        
        self.assertEqual(config.app.name, 'TestApp')
        self.assertTrue(config.app.features.logging)
        self.assertEqual(config.database.connections[0].name, 'primary')
    
    def test_deeply_nested_with_lists(self):
        """Should handle deep nesting with lists and mixed content."""
        complex_structure = DotDict({
            'applications': {
                'web_servers': [
                    {
                        'name': 'nginx',
                        'config': {
                            'locations': [
                                {
                                    'path': '/',
                                    'settings': {
                                        'proxy_pass': 'http://backend',
                                        'headers': {
                                            'custom': ['X-Real-IP', 'X-Forwarded-For']
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        })
        
        web_server = complex_structure.applications.web_servers[0]
        location = web_server.config.locations[0]
        
        self.assertEqual(web_server.name, 'nginx')
        self.assertEqual(location.settings.proxy_pass, 'http://backend')
        self.assertEqual(location.settings.headers.custom[0], 'X-Real-IP')
    
    def test_dynamic_assignment(self):
        """Should handle dynamic assignment with automatic conversion."""
        dynamic = DotDict({'initial': 'value'})
        dynamic.new_dict = {'nested': {'deep': 'assigned'}}
        dynamic.new_list = [{'item': 'converted'}, 'regular_string']
        
        self.assertEqual(dynamic.new_dict.nested.deep, 'assigned')
        self.assertEqual(dynamic.new_list[0].item, 'converted')
        self.assertEqual(dynamic.new_list[1], 'regular_string')


class TestDotDictDictionaryFunctionality(unittest.TestCase):
    """Test that original dict functionality is preserved."""
    
    def test_keys_method(self):
        """Should preserve keys() method."""
        d = DotDict({'a': 1, 'b': 2, 'c': 3})
        keys = list(d.keys())
        self.assertEqual(sorted(keys), ['a', 'b', 'c'])
    
    def test_values_method(self):
        """Should preserve values() method."""
        d = DotDict({'a': 1, 'b': 2, 'c': 3})
        values = list(d.values())
        self.assertEqual(sorted(values), [1, 2, 3])
    
    def test_items_method(self):
        """Should preserve items() method."""
        d = DotDict({'a': 1, 'b': 2})
        items = dict(d.items())
        self.assertEqual(items, {'a': 1, 'b': 2})
    
    def test_get_method_with_default(self):
        """Should preserve get() method with default value."""
        d = DotDict({'exists': 'value'})
        self.assertEqual(d.get('exists'), 'value')
        self.assertEqual(d.get('nonexistent', 'default'), 'default')
        self.assertIsNone(d.get('nonexistent'))


if __name__ == '__main__':
    unittest.main()
