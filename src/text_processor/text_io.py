"""
Text I/O Module

Provides classes for reading and writing text from various file formats.

"""

from pathlib import Path
from typing import Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.app_config import AppConfig

from src.config.app_config import get_app_config
from src.utils.app_logger import get_logger


class TextReader:
    """
    Class for reading text from various sources and formats.
    
    """
    
    def __init__(
        self, 
        default_encoding: Optional[str] = None,
        config: Optional["AppConfig"] = None
    ):
        """Initialize TextReader with optional config dependency injection.
        
        Args:
            default_encoding: Optional encoding override. If None, uses config.
            config: Optional AppConfig instance. If None, uses singleton.
        """

        self.logger = get_logger("RomanianTextEditor.TextProcessor")
        self.config: "AppConfig" = config if config is not None else get_app_config()

        # Load settings from config or use override
        if default_encoding is not None:
            self.default_encoding = default_encoding
            self.logger.debug(f"Reader: Using provided encoding: {default_encoding}")
        else:
            self.default_encoding = self.config.file_config.DEFAULT_ENCODING
            self.logger.debug(f"Reader: Using config encoding: {self.default_encoding}")

        self.text: Optional[str] = None  # Store the current text content
        self.logger.debug("Reader: TextReader initialized")
    
    def _read_textlike(self, file_path: Union[str, Path]) -> Optional[str]:
        """Read a text file and return its content.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            File content as string, or None if reading failed
        """
        try:
            with open(file_path, 'r', encoding=self.default_encoding) as f:
                content = f.read()
            self.logger.debug(f"Successfully read {len(content)} characters from {file_path}")
            return content
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def read_txt(self, file_path: Union[str, Path]) -> Optional[str]:
        """Read text from a .txt file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            File content or None if reading failed
        """
        self.logger.debug(f"Reader: Reading text file: {file_path}")
        return self._read_textlike(file_path)
    
    def read_markdown(self, file_path: Union[str, Path]) -> Optional[str]:
        """Read text from a markdown file, preserving text content.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            File content or None if reading failed
            
        Note:
            Currently treats markdown like regular text.
            Future enhancement: strip markdown formatting
        """
        self.logger.debug(f"Reader: Reading markdown file: {file_path}")
        # For now, treat markdown like regular text
        return self._read_textlike(file_path)
    
    def read_html(self, file_path: Union[str, Path]) -> Optional[str]:
        """Read text from an HTML file.
        
        Note:
            Currently not implemented. Would require HTML parsing library.
        """
        self.logger.warning(f"Reading HTML files is not implemented: {file_path}")
        return None

    def read_docx(self, file_path: Union[str, Path]) -> Optional[str]:
        """Read text from a DOCX file.
        
        Note:
            Currently not implemented. Would require python-docx library,
            which conflicts with project goal of avoiding external dependencies.
        """
        self.logger.warning(f"Reading DOCX files is not implemented: {file_path}")
        return None

    def read_pdf(self, file_path: Union[str, Path]) -> Optional[str]:
        """Read text from a PDF file.
        
        Note:
            Currently not implemented. Would require PyPDF2 or pdfplumber library,
            which conflicts with project goal of avoiding external dependencies.
        """
        self.logger.warning(f"Reading PDF files is not implemented: {file_path}")
        return None
    
    def read_by_format(self, file_path: Union[str, Path]) -> Optional[str]:
        """Auto-detect file format and read accordingly.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            File content or None if reading failed
        """
        if not file_path:
            self.logger.warning("Empty file path provided to read_by_format")
            return None

        file_path = Path(file_path)

        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return None

        suffix = file_path.suffix.lower()

        # Mapping of suffixes to handler methods
        format_map = {
            '.txt': self.read_txt,
            '.md': self.read_markdown,
            '.markdown': self.read_markdown,
            '.html': self.read_html,
            '.docx': self.read_docx,
            '.pdf': self.read_pdf,
        }

        handler = format_map.get(suffix, self.read_txt)
        if suffix not in format_map:
            self.logger.warning(f"Unknown file format '{suffix}', treating as text file")

        content = handler(file_path)

        # Store the content in the text attribute
        if content is not None:
            self.text = content
            self.logger.debug(f"Stored {len(content)} characters in self.text")

        return content
    
    def set_text(self, text: str) -> str:
        """Set text content directly (e.g., from command line input).
        
        Args:
            text: The text content to store
            
        Returns:
            The stored text
        """
        self.text = text
        self.logger.debug(f"Reader: Set text directly: {len(text)} characters")
        return text

class TextWriter:
    """
    Class for writing text to txt files or console.
    
    """
    
    def __init__(
        self,
        output_path: Optional[Union[str, Path]] = None,
        default_encoding: Optional[str] = None,
        config: Optional["AppConfig"] = None
    ):
        """Initialize TextWriter with optional config dependency injection.
        
        Args:
            output_path: Where to write output. If None, writes to console.
            default_encoding: Optional encoding override. If None, uses config.
            config: Optional AppConfig instance. If None, uses config.
        """
        # Initialize logger (infrastructure detail)
        self.logger = get_logger("RomanianTextEditor.TextProcessor")
        
        # Store output destination
        self.output_path = Path(output_path) if output_path else None
        if self.output_path:
            self.logger.debug(f"Writer: TextWriter will write to: {self.output_path}")
        else:
            self.logger.debug("Writer: TextWriter will write to console")
        
        # Load settings from config or use override
        if default_encoding is not None:
            self.default_encoding = default_encoding
            self.create_dirs = True  # Default when encoding is overridden
            self.logger.debug(f"Writer: Using provided encoding: {default_encoding}")
        else:
            # Get config (injected or singleton)
            cfg = config if config is not None else get_app_config()
            # Trust the config - it's already validated
            self.default_encoding = cfg.file_config.DEFAULT_ENCODING
            self.create_dirs = cfg.file_config.CREATE_DIRS_IF_MISSING
            self.logger.debug(f"Writer: Using config: encoding={self.default_encoding}, create_dirs={self.create_dirs}")
        
        self.logger.debug("Writer: TextWriter initialized")
    
    def write(self, content: str) -> bool:
        """Write content to configured destination (file or console).
        
        Args:
            content: Text content to write
            
        Returns:
            True if write succeeded, False otherwise
        """
        if self.output_path:
            # Write to file
            return self.write_txt(content, self.output_path)
        else:
            # Write to console
            print("\n" + "=" * 50)
            print("PROCESSED OUTPUT:")
            print("=" * 50)
            print(content)
            print("=" * 50)
            self.logger.debug(f"Writer: Wrote {len(content)} characters to console")
            return True
    
    def write_txt(self, content: str, file_path: Union[str, Path]) -> bool:
        """Write content to a .txt file.
        
        Args:
            content: Text content to write
            file_path: Path where the file should be written
            
        Returns:
            True if write succeeded, False otherwise
        """
        try:
            path = Path(file_path)
            if self.create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Writer: Ensured directory exists: {path.parent}")
            
            path.write_text(content, encoding=self.default_encoding)
            self.logger.debug(f"Writer: Successfully wrote {len(content)} characters to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Writer: Error writing to file {file_path}: {e}")
            return False
    
    def append_txt(self, content: str, file_path: Union[str, Path]) -> bool:
        """Append content to an existing txt file.
        
        Args:
            content: Text content to append
            file_path: Path to the file to append to
            
        Returns:
            True if append succeeded, False otherwise
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('a', encoding=self.default_encoding) as f:
                f.write(content)
            self.logger.debug(f"Writer: Successfully appended {len(content)} characters to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Writer: Error appending to file {file_path}: {e}")
            return False
        
    def write_to_console(self, content: str) -> bool:
        """Output content to console/screen.
        
        Args:
            content: Text content to display
            
        Returns:
            Always True (console output doesn't fail)
        """
        print(content)
        self.logger.debug(f"Wrote {len(content)} characters to console")
        return True



if __name__ == "__main__":
    print("Tests have been migrated to tests/unit/text_processor/test_text_io.py")
    print("Run: python -m unittest tests.unit.text_processor.test_text_io")
    print("Or: python -m unittest discover tests")
