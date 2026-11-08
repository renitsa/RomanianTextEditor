"""
Unit tests for PathManager.
Tests path management and file operations.
"""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock
from src.app.path_manager import PathManager
from src.config.app_config import get_app_config


class TestPathManager(unittest.TestCase):
    """Test PathManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = get_app_config()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization_with_dependencies(self):
        """Test PathManager initialization with injected dependencies."""
        mock_logger = Mock()
        
        pm = PathManager(app_config=self.config, logger=mock_logger)
        
        self.assertEqual(pm.config, self.config)
        self.assertEqual(pm.logger, mock_logger)
        self.assertIsInstance(pm.input_dir, Path)
        self.assertIsInstance(pm.output_dir, Path)
    
    def test_get_input_files_nonexistent_dir(self):
        """Test get_input_files when directory doesn't exist."""
        mock_logger = Mock()
        pm = PathManager(logger=mock_logger)
        
        # Temporarily override input_dir to nonexistent path
        pm.input_dir = Path(self.temp_dir) / "nonexistent"
        
        files = pm.get_input_files()
        
        self.assertEqual(files, [])
        mock_logger.warning.assert_called_once()
    
    def test_get_input_files_empty_dir(self):
        """Test get_input_files with empty directory."""
        mock_logger = Mock()
        pm = PathManager(logger=mock_logger)
        
        # Create empty directory
        test_input_dir = Path(self.temp_dir) / "input"
        test_input_dir.mkdir()
        pm.input_dir = test_input_dir
        
        files = pm.get_input_files()
        
        self.assertEqual(files, [])
    
    def test_get_input_files_with_txt_files(self):
        """Test get_input_files with .txt files."""
        pm = PathManager()
        
        # Create test directory with files
        test_input_dir = Path(self.temp_dir) / "input"
        test_input_dir.mkdir()
        pm.input_dir = test_input_dir
        
        # Create test files
        (test_input_dir / "file1.txt").write_text("Content 1", encoding='utf-8')
        (test_input_dir / "file2.txt").write_text("Content 2", encoding='utf-8')
        
        files = pm.get_input_files()
        
        self.assertEqual(len(files), 2)
        self.assertTrue(all(f.suffix == '.txt' for f in files))
    

    def test_get_input_files_skips_hidden_files(self):
        """Test that get_input_files skips hidden files."""
        pm = PathManager()
        
        test_input_dir = Path(self.temp_dir) / "input"
        test_input_dir.mkdir()
        pm.input_dir = test_input_dir
        
        # Create visible and hidden files
        (test_input_dir / "visible.txt").write_text("Visible", encoding='utf-8')
        (test_input_dir / ".hidden.txt").write_text("Hidden", encoding='utf-8')
        
        files = pm.get_input_files()
        
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "visible.txt")
    
    def test_get_input_files_skips_unsupported_extensions(self):
        """Test that get_input_files skips unsupported file types."""
        pm = PathManager()
        
        test_input_dir = Path(self.temp_dir) / "input"
        test_input_dir.mkdir()
        pm.input_dir = test_input_dir
        
        # Create supported and unsupported files
        (test_input_dir / "doc.txt").write_text("Text", encoding='utf-8')
        (test_input_dir / "image.jpg").write_bytes(b"fake image")
        (test_input_dir / "data.json").write_text("{}", encoding='utf-8')
        
        files = pm.get_input_files()
        
        # Should only get .txt file
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].suffix, '.txt')
    
    def test_get_input_files_skips_formats_without_reader(self):
        """Document formats (pdf, docx, html) have no reader, so they are not offered."""
        pm = PathManager()
        
        test_input_dir = Path(self.temp_dir) / "input"
        test_input_dir.mkdir()
        pm.input_dir = test_input_dir
        
        (test_input_dir / "doc.txt").write_text("Text", encoding='utf-8')
        (test_input_dir / "paper.pdf").write_bytes(b"%PDF")
        (test_input_dir / "letter.docx").write_bytes(b"PK")
        
        files = pm.get_input_files()
        
        self.assertEqual([f.name for f in files], ["doc.txt"])
    
    def test_get_input_files_sorted(self):
        """Test that get_input_files returns sorted results."""
        pm = PathManager()
        
        test_input_dir = Path(self.temp_dir) / "input"
        test_input_dir.mkdir()
        pm.input_dir = test_input_dir
        
        # Create files in non-alphabetical order
        (test_input_dir / "zebra.txt").write_text("Z", encoding='utf-8')
        (test_input_dir / "alpha.txt").write_text("A", encoding='utf-8')
        (test_input_dir / "beta.txt").write_text("B", encoding='utf-8')
        
        files = pm.get_input_files()
        
        file_names = [f.name for f in files]
        self.assertEqual(file_names, sorted(file_names))
    
    def test_generate_output_path_from_file(self):
        """Test generate_output_path with file input."""
        pm = PathManager()
        pm.output_dir = Path(self.temp_dir) / "output"
        
        output = pm.generate_output_path("/path/to/document.txt", "diacritics")
        
        self.assertEqual(output.parent, pm.output_dir)
        self.assertRegex(output.name, r"^document_diacritics_\d{8}_\d{6}\.txt$")
    
    def test_generate_output_path_text_input_identifier(self):
        """Test generate_output_path with text_input identifier."""
        pm = PathManager()
        pm.output_dir = Path(self.temp_dir) / "output"
        
        output = pm.generate_output_path("text_input", "edit")
        
        self.assertRegex(output.name, r"^text_input_edit_\d{8}_\d{6}\.txt$")
    
    def test_generate_output_path_empty_identifier_uses_default_name(self):
        """An empty identifier uses the base name of DEFAULT_OUTPUT_FILENAME."""
        pm = PathManager()
        
        output = pm.generate_output_path("", "edit")
        
        self.assertRegex(output.name, r"^output_edit_\d{8}_\d{6}\.txt$")
    
    def test_generate_output_path_changes_with_time(self):
        """Different runs get different names, so results are not overwritten."""
        from datetime import datetime
        from unittest.mock import patch
        pm = PathManager()
        
        with patch('src.app.path_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 2, 3, 4, 5)
            first = pm.generate_output_path("doc.txt", "edit")
            mock_datetime.now.return_value = datetime(2026, 1, 2, 3, 4, 6)
            second = pm.generate_output_path("doc.txt", "edit")
        
        self.assertEqual(first.name, "doc_edit_20260102_030405.txt")
        self.assertEqual(second.name, "doc_edit_20260102_030406.txt")
    
    def test_generate_output_path_respects_max_filename_length(self):
        """Long input names are shortened to fit MAX_FILENAME_LENGTH."""
        pm = PathManager()
        
        output = pm.generate_output_path("a" * 400 + ".txt", "edit")
        
        self.assertLessEqual(len(output.name), pm.config.file_config.MAX_FILENAME_LENGTH)
        self.assertTrue(output.name.endswith(".txt"))
    
    def test_get_file_size_str_bytes(self):
        """Test get_file_size_str for small files (bytes)."""
        pm = PathManager()
        
        test_file = Path(self.temp_dir) / "small.txt"
        test_file.write_text("Hi", encoding='utf-8')  # 2 bytes
        
        size_str = pm.get_file_size_str(test_file)
        
        self.assertIn("B", size_str)
        self.assertIn("(", size_str)
    
    def test_get_file_size_str_kilobytes(self):
        """Test get_file_size_str for KB files."""
        pm = PathManager()
        
        test_file = Path(self.temp_dir) / "medium.txt"
        test_file.write_text("x" * 2000, encoding='utf-8')  # ~2KB
        
        size_str = pm.get_file_size_str(test_file)
        
        self.assertIn("KB", size_str)
    
    def test_get_file_size_str_megabytes(self):
        """Test get_file_size_str for MB files."""
        pm = PathManager()
        
        test_file = Path(self.temp_dir) / "large.txt"
        test_file.write_text("x" * 2_000_000, encoding='utf-8')  # ~2MB
        
        size_str = pm.get_file_size_str(test_file)
        
        self.assertIn("MB", size_str)
    
    def test_get_file_size_str_nonexistent_file(self):
        """Test get_file_size_str with nonexistent file."""
        pm = PathManager()
        
        test_file = Path(self.temp_dir) / "nonexistent.txt"
        
        size_str = pm.get_file_size_str(test_file)
        
        self.assertEqual(size_str, "")
    

if __name__ == "__main__":
    unittest.main()
