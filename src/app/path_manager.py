"""
PathManager - Simplified file path operations

This module provides a thin wrapper around config-based path management.
Most path logic is handled by AppConfig; this class adds convenience methods
for the application layer.
"""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from src.config.app_config import AppConfig
    from src.utils.app_logger import AppLogger

from src.config.app_config import get_app_config
from src.utils.app_logger import get_logger


class PathManager:
    """
    This class provides convenience methods for common path operations
    without duplicating logic that already exists in AppConfig.
    """
    
    def __init__(self, app_config: Optional["AppConfig"] = None,
                 logger: Optional["AppLogger"] = None):
        """
        Args:
            app_config: Optional AppConfig instance. If not provided, will get default configuration.
            logger: Optional AppLogger instance. If not provided, will create one.
        """
        self.config = app_config if app_config is not None else get_app_config()
        self.logger = logger if logger is not None else get_logger("RomanianTextEditor.App")
        
        # Get directory paths from config
        base_dir = self.config.loadercfg.BASE_DIR
        self.input_dir = base_dir / self.config.file_config.ESSENTIAL_DIRS.INPUT_DIR
        self.output_dir = base_dir / self.config.file_config.ESSENTIAL_DIRS.OUTPUT_DIR

        self.logger.debug("PathManager: Initialized")
    
    def get_input_files(self) -> List[Path]:
        """Get list of available input files with supported extensions.
        
        Returns:
            List of Path objects for valid input files
        """
        if not self.input_dir.exists():
            self.logger.warning(f"PathManager: Input directory does not exist: {self.input_dir}")
            return []
        
        files = []
        # Only formats that can be read without extra dependencies are offered.
        # SUPPORTED_DOCUMENT_EXTENSIONS (pdf, docx, html) are reserved for forks
        # that add a reader for them.
        supported_extensions = self.config.file_config.SUPPORTED_TEXT_EXTENSIONS
        
        for file_path in self.input_dir.iterdir():
            # Skip hidden files (Unix convention: files starting with '.')
            # and only include files with supported extensions
            if (file_path.is_file() and 
                not file_path.name.startswith('.') and
                file_path.suffix.lower() in supported_extensions):
                files.append(file_path)
        
        self.logger.debug(f"PathManager: Found {len(files)} input files")
        return sorted(files)
    
    def generate_output_path(self, input_identifier: str, task: str) -> Path:
        """Generate a timestamped output path for a given input and task.
        
        The name is {base}{sep}{task}{sep}{timestamp}{extension}, built from the
        separator, timestamp format, default name and maximum length in file_config.json.
        
        Args:
            input_identifier: Either a file path OR a special identifier like "cli_text"
            task: The processing task name
            
        Returns:
            Path object for the output file
        """
        file_cfg = self.config.file_config
        default_name = Path(file_cfg.DEFAULT_OUTPUT_FILENAME)
        
        # Check if it's a special identifier
        if input_identifier in ("cli_text", "text_input", "cli_input", ""):
            # Use the identifier as the base name (or the default name for empty)
            base_name = input_identifier if input_identifier else default_name.stem
        else:
            # It's a file path - extract the stem
            input_path = Path(input_identifier)
            base_name = input_path.stem
        
        # Create filename with task and timestamp suffix, within the length limit
        separator = file_cfg.OUTPUT_SUFFIX_SEPARATOR
        timestamp = datetime.now().strftime(file_cfg.OUTPUT_TIMESTAMP_FORMAT)
        suffix = f"{separator}{task}{separator}{timestamp}{default_name.suffix}"
        base_name = base_name[:max(1, file_cfg.MAX_FILENAME_LENGTH - len(suffix))]
        output_path = self.output_dir / f"{base_name}{suffix}"
        
        self.logger.debug(f"PathManager: Generated output path: {output_path}")
        return output_path
    
    def get_file_size_str(self, file_path: Path) -> str:
        """Get human-readable file size string.
        
        Args:
            file_path: Path to the file
            
        Returns:
            String like "(1.5KB)" or empty string if error
        """
        try:
            size = file_path.stat().st_size
            if size < 1024:
                return f"({size}B)"
            elif size < 1024 * 1024:
                return f"({size/1024:.1f}KB)"
            else:
                return f"({size/(1024*1024):.1f}MB)"
        except Exception as e:
            self.logger.debug(f"PathManager: Could not get file size for {file_path}: {e}")
            return ""