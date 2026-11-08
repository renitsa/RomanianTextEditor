"""
Unit tests for text_io module (TextReader and TextWriter).
"""

import unittest
import tempfile
from pathlib import Path

from src.text_processor.text_io import TextReader, TextWriter


class TestTextReader(unittest.TestCase):
    """Test cases for TextReader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.reader = TextReader()
        self.test_content = "Line 1\nLine 2\nLine 3"
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_read_txt(self):
        """Test reading a .txt file."""
        test_file = self.temp_path / "test.txt"
        test_file.write_text(self.test_content, encoding='utf-8')
        
        result = self.reader.read_txt(test_file)
        self.assertEqual(result, self.test_content)
        # Note: read_txt doesn't set self.text, only read_by_format does
    
    def test_read_by_format_txt(self):
        """Test read_by_format with .txt file."""
        test_file = self.temp_path / "test.txt"
        test_file.write_text(self.test_content, encoding='utf-8')
        
        result = self.reader.read_by_format(test_file)
        self.assertEqual(result, self.test_content)
    
    def test_read_by_format_html_not_implemented(self):
        """Test read_by_format with .html file (not implemented)."""
        test_file = self.temp_path / "test.html"
        test_file.write_text("<html><body>Test</body></html>", encoding='utf-8')
        
        result = self.reader.read_by_format(test_file)
        self.assertIsNone(result)
    
    def test_read_by_format_unsupported_extension(self):
        """Test read_by_format with unsupported extension."""
        test_file = self.temp_path / "test.unknown"
        test_file.write_text(self.test_content, encoding='utf-8')
        
        result = self.reader.read_by_format(test_file)
        # Treats unknown formats as text files with warning
        self.assertEqual(result, self.test_content)
    
    def test_set_text(self):
        """Test setting text directly."""
        direct_text = "Direct input text"
        result = self.reader.set_text(direct_text)
        
        self.assertEqual(result, direct_text)
        self.assertEqual(self.reader.text, direct_text)
    
    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        nonexistent_file = self.temp_path / "nonexistent.txt"
        result = self.reader.read_txt(nonexistent_file)
        
        self.assertIsNone(result)


class TestTextWriter(unittest.TestCase):
    """Test cases for TextWriter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_content = "Line 1\nLine 2\nLine 3"
        self.test_append = "\nAppended line"
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_write_txt(self):
        """Test writing to a .txt file."""
        test_file = self.temp_path / "test.txt"
        writer = TextWriter()
        
        success = writer.write_txt(self.test_content, test_file)
        self.assertTrue(success)
        
        # Verify content was written
        written_content = test_file.read_text(encoding='utf-8')
        self.assertEqual(written_content, self.test_content)
    
    def test_append_txt(self):
        """Test appending to a .txt file."""
        test_file = self.temp_path / "test.txt"
        writer = TextWriter()
        
        # Write initial content
        writer.write_txt(self.test_content, test_file)
        
        # Append content
        success = writer.append_txt(self.test_append, test_file)
        self.assertTrue(success)
        
        # Verify both contents are present
        written_content = test_file.read_text(encoding='utf-8')
        self.assertEqual(written_content, self.test_content + self.test_append)
    
    def test_write_creates_directory(self):
        """Test that write creates parent directories."""
        test_file = self.temp_path / "subdir" / "test.txt"
        writer = TextWriter()
        
        success = writer.write_txt(self.test_content, test_file)
        self.assertTrue(success)
        self.assertTrue(test_file.exists())
    
    def test_write_with_output_path(self):
        """Test write method with output_path set."""
        test_file = self.temp_path / "test.txt"
        writer = TextWriter(output_path=test_file)
        
        success = writer.write(self.test_content)
        self.assertTrue(success)
        
        # Verify content was written
        written_content = test_file.read_text(encoding='utf-8')
        self.assertEqual(written_content, self.test_content)
    
    def test_write_to_console(self):
        """Test write method with no output_path (console output)."""
        writer = TextWriter(output_path=None)
        
        # Console output should succeed
        success = writer.write(self.test_content)
        self.assertTrue(success)


class TestTextReaderWriterIntegration(unittest.TestCase):
    """Integration tests for TextReader and TextWriter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_content = "Test content for integration"
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_write_and_read_cycle(self):
        """Test writing then reading the same file."""
        test_file = self.temp_path / "test.txt"
        
        # Write
        writer = TextWriter()
        write_success = writer.write_txt(self.test_content, test_file)
        self.assertTrue(write_success)
        
        # Read
        reader = TextReader()
        read_content = reader.read_txt(test_file)
        self.assertEqual(read_content, self.test_content)


if __name__ == '__main__':
    unittest.main()
