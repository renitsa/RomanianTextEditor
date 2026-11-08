"""
Text Chunking Module

Provides strategies for splitting text into processable chunks with configurable
size limits and delimiter handling.

"""

from abc import ABC, abstractmethod
from typing import List, Set, Optional, Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from src.utils.dict_utils import DotDict
    from src.config.app_config import AppConfig

from src.config.app_config import get_app_config
from src.utils.app_logger import get_logger


class ChunkStrategy(ABC):
    """
    Abstract base class for chunking strategies.
    """
    
    def __init__(self, config: Optional["AppConfig"] = None):
        """Initialize strategy with text processing configuration.
        
        Args:
            config: Optional AppConfig instance. If None, uses singleton.
        """
        # Initialize logger and get config
        self.logger = get_logger("RomanianTextEditor.TextProcessor")
        cfg = config if config is not None else get_app_config()
        
        # DotDict with chunking parameters from text_processing_config.json
        self.tcfg: "DotDict" = cfg.text_config  # type: ignore[assignment]
        self.logger.debug(f"Strategy.{self.__class__.__name__}: Initialized")

    @abstractmethod
    def apply(self, chunks: List[str]) -> List[str]:
        """Apply this strategy to a list of text chunks, returning a new list."""
        pass

    def _merge_small_chunks(self, chunks: List[str], min_size: int, max_size: Optional[int] = None) -> List[str]:
        """Merge chunks smaller than min_size with subsequent ones.
        
        Args:
            chunks: List of text chunks to merge
            min_size: Minimum chunk size to maintain (takes precedence)
            max_size: Maximum chunk size to respect where possible
            
        Returns:
            List of merged chunks meeting size requirements
        """

        if not isinstance(chunks, list):
            raise TypeError("The chunks must be a list of strings.")
        
        if not chunks:
            return []
        
        # Filter out empty chunks first
        non_empty_chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        if not non_empty_chunks:
            return []
        
        result: List[str] = []
        current_chunk = ""
        
        last_index = len(non_empty_chunks) - 1
        for i, chunk in enumerate(non_empty_chunks):
            is_last_chunk = (i == last_index)

            if len(current_chunk) > 0:
                # Try to merge with current chunk
                combined = current_chunk + " " + chunk
                
                # Check if combined chunk exceeds max_size (if specified)
                if max_size and len(combined) > max_size:
                    # Don't merge, add current chunk to result and start a new one
                    result.append(current_chunk)
                    current_chunk = chunk
                elif len(combined) >= min_size or is_last_chunk:
                    result.append(combined)
                    current_chunk = ""
                else:
                    current_chunk = combined
            else:
                # Start new chunk or add if meets minimum size
                if len(chunk) >= min_size:
                    result.append(chunk)
                else:
                    current_chunk = chunk
        
        # Add any remaining chunk (this handles the final small chunk case)
        if len(current_chunk) > 0:
            result.append(current_chunk)

        return result


class StringSplitStrategy(ChunkStrategy):
    """Strategy to split chunks using specified string delimiters.
    
    This strategy can split text at:
    - Empty lines (by using '\n\n' as delimiter) - section breaks
    - Single newlines (by using '\n' as delimiter) - paragraph breaks
    - Any custom string or list of strings
    """
    
    def __init__(self, min_size: Optional[int] = None, max_size: Optional[int] = None, 
                 delimiters: Union[str, List[str]] = '\n', 
                 preserve_delimiters: str = "keep_with_previous",
                 language: str = "ro",
                 **kwargs):
        """Initialize with specified delimiters.
        
        Args:
            min_size: Minimum chunk size to maintain (defaults to TextProcessingConfig.STRINGSPLIT_MIN_SIZE)
            max_size: Maximum chunk size to enforce (defaults to TextProcessingConfig.STRINGSPLIT_MAX_SIZE)
            delimiters: String or list of strings to use as split points
            preserve_delimiters: How to handle delimiters when splitting
                "discard" - Remove delimiters
                "keep_with_previous" - Keep delimiters at the end of the previous chunk (default)
                "keep_with_next" - Keep delimiters at the beginning of the next chunk
            language: Language code (accepted for uniform interface, not used by this strategy)
            **kwargs: Additional arguments including optional 'config' for dependency injection
        """
        super().__init__(**kwargs)
        
        self.min_size = self.tcfg.STRINGSPLIT_MIN_SIZE if min_size is None else min_size
        self.max_size = self.tcfg.STRINGSPLIT_MAX_SIZE if max_size is None else max_size

        self.delimiters = [delimiters] if isinstance(delimiters, str) else delimiters
        
        # Validate preserve_delimiters option
        valid_options = ["discard", "keep_with_previous", "keep_with_next"]
        if preserve_delimiters not in valid_options:
            raise ValueError(f"preserve_delimiters must be one of {valid_options}")
        self.preserve_delimiters = preserve_delimiters
        
    def apply(self, chunks: List[str]) -> List[str]:
        """Split chunks at specified delimiters."""
        split_chunks: List[str] = []
        
        for chunk in chunks:
            if not chunk.strip():
                continue
            
            # Start with the original chunk
            current_parts = [chunk]
            
            # Apply each delimiter in sequence
            for delimiter in self.delimiters:
                new_parts = []
                for part in current_parts:
                    # Use custom split that handles delimiter preservation
                    subparts = self._split_with_delimiter_handling(part, delimiter)
                    new_parts.extend([sp for sp in subparts if sp.strip()])
                current_parts = new_parts
            
            # Add all resulting parts to our results
            split_chunks.extend(current_parts)
        
        # Merge small chunks to meet minimum size requirement while respecting max_size
        return self._merge_small_chunks(split_chunks, self.min_size, self.max_size)
    
    def _split_with_delimiter_handling(self, text: str, delimiter: str) -> List[str]:
        """Split text on delimiter with control over delimiter preservation."""
        
        if not text:
            return []
            
        # Standard split behavior - discard delimiter
        if self.preserve_delimiters == "discard":
            return text.split(delimiter)
        
        # For preservation options, we need to track the delimiters
        result = []
        segments = text.split(delimiter)

        if self.preserve_delimiters == "keep_with_previous":
            # For all but last segment, append delimiter to the end
            for i in range(len(segments) - 1):
                result.append(segments[i] + delimiter)
                
            # Handle last segment (no following delimiter)
            if segments:
                result.append(segments[-1])
                
        elif self.preserve_delimiters == "keep_with_next":
            # Handle first segment (no preceding delimiter)
            if segments and len(segments) > 0:
                result.append(segments[0])
                
            # For remaining segments, prepend delimiter
            for i in range(1, len(segments)):
                result.append(delimiter + segments[i])
        
        return result


class SentenceSplitStrategy(ChunkStrategy):
    """Strategy to split chunks at sentence boundaries with rules-based sentence detection."""
    
    def __init__(self, min_size: Optional[int] = None, max_size: Optional[int] = None, 
                 language: str = "ro", **kwargs):
        """Initialize with language-specific settings.
        
        Args:
            min_size: Minimum chunk size to maintain (defaults to TextProcessingConfig.SENTENCESPLIT_MIN_SIZE)
            max_size: Maximum chunk size to enforce (defaults to TextProcessingConfig.SENTENCESPLIT_MAX_SIZE)
            language: Language code for abbreviation detection ("ro" or "en")
            **kwargs: Additional arguments including optional 'config' for dependency injection
        """
        super().__init__(**kwargs)

        # Use strategy defaults if not specified
        self.min_size = self.tcfg.SENTENCESPLIT_MIN_SIZE if min_size is None else min_size
        self.max_size = self.tcfg.SENTENCESPLIT_MAX_SIZE if max_size is None else max_size
        
        self.language = language
        self.abbreviations = self._get_abbreviations(language)
        self.abbrev_max_len = max(len(abbrev) for abbrev in self.abbreviations) if self.abbreviations else 0

    def apply(self, chunks: List[str]) -> List[str]:
        result: List[str] = []
        
        for chunk in chunks:
            result.extend(self._split_by_sentences(chunk))
        
        # Merge small chunks to meet minimum size requirement while respecting max_size
        return self._merge_small_chunks(result, self.min_size, self.max_size)

    def _get_abbreviations(self, language: str = "ro") -> Set[str]:
        """Get abbreviations for the specified language, all lowercased."""
        if language.lower() in ["en", "english"]:
            return {abbr.lower() for abbr in self.tcfg.COMMON_ENG_ABBREVIATIONS}
        return {abbr.lower() for abbr in self.tcfg.COMMON_RO_ABBREVIATIONS}
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """Split text into chunks that end with complete sentences."""
        sentences = self._detect_sentences(text)
        if not sentences:
            return self._fallback_split(text)

        return sentences

    def _detect_sentences(self, text: str) -> List[str]:
        """Advanced sentence detection with improved period handling."""
        if not text.strip():
            return []
            
        sentences: List[str] = []
        current_sentence = ""
        i = 0
        
        while i < len(text):
            char = text[i]
            current_sentence += char
            
            if i == len(text) - 1:
                # If it's the last character, just add the current text
                sentences.append(current_sentence)
                break

            # Check for sentence terminators
            if char in self.tcfg.SENTENCE_TERMINATORS:
                if char == '.':
                    # Special handling for periods
                    if self._is_sentence_end(text, i):
                        sentences.append(current_sentence)
                        current_sentence = ""
                else:
                    # For ! and ?, simpler logic
                    if i < len(text) - 1 and text[i + 1] in self.tcfg.SPACE_SEPARATORS:
                        sentences.append(current_sentence)
                        current_sentence = ""
            i += 1
            
        # Return all sentences (small ones will be merged later)
        return [s for s in sentences if s.strip()]
    
    def _is_sentence_end(self, text: str, pos: int) -> bool:
        """Check if a period at position 'pos' marks the end of a sentence."""

        if pos >= len(text) - 1:
            # If it's the last character, treat it as a sentence end
            return True
        
        if pos <= 1:                
            return False
        
        # Rule a: Check if period is not followed by space
        if text[pos + 1] not in self.tcfg.SPACE_SEPARATORS:
            return False
        
        # Rule b: Check if preceded by abbreviation
        if self._is_preceded_by_abbreviation(text, pos):
            return False
        
        # Rule c: Check if preceded by an alphanumeric character and that character is preceded by a space/newline/tab
        if text[pos - 1].isalnum() and (text[pos - 2] in self.tcfg.SPACE_SEPARATORS):
            return False
        
        return True

    
    def _is_preceded_by_abbreviation(self, text: str, pos: int) -> bool:
        """Check if the period is part of a known abbreviation.

        The abbreviation must start a word, so 'hotel.' does not match 'tel.'.
        """

        # Look backwards for potential abbreviation
        start = max(0, pos - self.abbrev_max_len)  
        fragment_lower = text[start:pos+1].lower()
        
        # Check against known abbreviations - use case-insensitive comparison
        for abbrev in self.abbreviations:
            if not fragment_lower.endswith(abbrev):
                continue
            abbrev_start = pos + 1 - len(abbrev)
            if abbrev_start == 0 or not text[abbrev_start - 1].isalnum():
                return True
            
        return False

    
    def _fallback_split(self, text: str) -> List[str]:
        """Fallback splitting when sentence detection fails."""
        if not text:
            return []
            
        result: List[str] = []
        remaining = text
        
        while len(remaining) > self.max_size:
            # Find the last natural boundary within max_size
            boundary_text = remaining[:self.max_size]
            last_boundary = -1
            
            # First try secondary terminators (: ;)
            for separator in self.tcfg.SECONDARY_TERMINATORS:
                last_boundary = boundary_text.rfind(separator)
                if last_boundary != -1:
                    break
            
            # If no secondary terminator found, try fallback separators
            if last_boundary == -1:
                for separator in self.tcfg.FALLBACK_SEPARATORS:
                    last_boundary = boundary_text.rfind(separator)
                    if last_boundary != -1:
                        break
            
            if last_boundary == -1:
                # No natural boundary found, just take max_size chars
                result.append(boundary_text)
                remaining = remaining[self.max_size:]
            else:
                # Split at boundary
                result.append(remaining[:last_boundary + 1])
                remaining = remaining[last_boundary + 1:]
        
        # Add remaining text if any
        if remaining:
            result.append(remaining)
            
        return result


class SizeOptimizingStrategy(ChunkStrategy):
    """Strategy to combine smaller chunks to optimize size utilization while respecting limits."""
    
    def __init__(self, min_size: Optional[int] = None, max_size: Optional[int] = None, 
                 separator: str = "\n", language: str = "ro", **kwargs):
        """Initialize with size optimization settings.
        
        Args:
            min_size: Minimum chunk size to maintain (defaults to TextProcessingConfig.SIZEOPTIMIZING_MIN_SIZE)
            max_size: Maximum chunk size to enforce (defaults to TextProcessingConfig.SIZEOPTIMIZING_MAX_SIZE)
            separator: String to use when joining chunks
            language: Language code (accepted for uniform interface, not used by this strategy)
            **kwargs: Additional arguments including optional 'config' for dependency injection
        """

        super().__init__(**kwargs)

        # Use strategy defaults if not specified
        self.min_size = self.tcfg.SIZEOPTIMIZING_MIN_SIZE if min_size is None else min_size
        self.max_size = self.tcfg.SIZEOPTIMIZING_MAX_SIZE if max_size is None else max_size
        
        self.separator = separator

    def apply(self, chunks: List[str]) -> List[str]:
        if not chunks:
            return []
            
        result: List[str] = []
        current_chunk: str = ""
        
        for chunk in chunks:
            if not chunk.strip():
                continue
                
            # If adding this chunk exceeds max_size, start a new chunk
            combined_length = len(current_chunk) + len(self.separator) + len(chunk)
            
            if current_chunk and combined_length > self.max_size:
                result.append(current_chunk)
                current_chunk = chunk
            else:
                # Add to current chunk
                if current_chunk:
                    current_chunk += self.separator + chunk
                else:
                    current_chunk = chunk
        
        # Add the last chunk if not empty
        if current_chunk:
            result.append(current_chunk)
        
        # Apply minimum size merging while respecting max_size
        return self._merge_small_chunks(result, self.min_size, self.max_size)


class TextChunker:
    """Class for breaking text into manageable chunks using multiple strategies.
    
       TextChunker can build a pipeline of strategies for flexible chunking workflows
    """
    
    def __init__(self, use_default_strategies: bool = False, language: str = "ro",
                 config: Optional["AppConfig"] = None) -> None:
        """Initialize a text chunker with specified strategies.
        
        Args:
            use_default_strategies: Whether to initialize with default strategies
            language: Language code for language-specific strategies
            config: Optional AppConfig instance. If None, uses singleton.
        """
        # Initialize logger (infrastructure detail)
        self.logger = get_logger("RomanianTextEditor.TextProcessor")
        cfg = config if config is not None else get_app_config()
        
        self.language = language
        self.fallback_separator: str = cfg.text_config.FALLBACK_CHUNK_SEPARATOR
        self.strategies: List[ChunkStrategy] = []
        
        # Initialize with default strategies if requested
        if use_default_strategies:
            self.logger.debug(f"Chunker: Initializing with default strategies for language: {language}")
            # Use strategy defaults by passing None for sizes
            self.add_strategy(StringSplitStrategy(None, None, '\n\n', "keep_with_previous"))
            self.add_strategy(SentenceSplitStrategy(None, None, language))
        else:
            self.logger.debug("Chunker: Initialized without default strategies")
    
    def add_strategy(self, strategy: ChunkStrategy) -> 'TextChunker':
        """Add a chunking strategy to the processing pipeline."""
        self.strategies.append(strategy)
        self.logger.debug(f"Chunker: Added strategy: {strategy.__class__.__name__}")
        return self
    
    def chunk_text(self, text: Optional[str]) -> List[str]:
        """Split text into chunks using the configured strategies.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks after applying all strategies
        """
        if not text or not text.strip():
            self.logger.warning("Empty or None text provided to chunk_text")
            return []
        
        # Start with the entire text as a single chunk
        chunks: List[str] = [text.strip()]
        
        self.logger.debug(f"Chunker: Starting chunking on text of length {len(text)} with {len(self.strategies)} strategies")
        
        for i, strategy in enumerate(self.strategies):
            try:
                chunks_before = len(chunks)
                chunks = strategy.apply(chunks)
                self.logger.debug(f"Chunker: Strategy {i+1} ({strategy.__class__.__name__}): {chunks_before} → {len(chunks)} chunks")
            except Exception as e:
                # Log error and continue with current chunks
                self.logger.error(f"Chunker: Strategy {strategy.__class__.__name__} failed: {e}", exc_info=True)
                continue
        
        self.logger.debug(f"Chunker: Chunking complete: produced {len(chunks)} final chunks")
        return chunks
    
    def chunk_text_with_separators(self, text: Optional[str]) -> Tuple[List[str], List[str]]:
        """Split text into chunks and recover the original layout between them.
        
        Strategies only change whitespace, never the other characters or their
        order, so every chunk can be matched back to its place in the original
        text. The chunks returned are the original pieces of text, and the
        separators are the original whitespace between them (a blank line, a
        line break, a single space, or nothing).
        
        If the chunks cannot be matched (for example a custom strategy rewrote
        the text), the chunks as produced are returned together with the
        configured fallback separator.
        
        Args:
            text: Input text to chunk
            
        Returns:
            Tuple (chunks, separators); separators[i] sits between chunks[i] and
            chunks[i + 1], so there is one separator fewer than there are chunks
        """
        chunks = [chunk.strip() for chunk in self.chunk_text(text) if chunk.strip()]
        if not chunks:
            return [], []
        
        spans = self._locate_chunks(text, chunks)
        if spans is None:
            self.logger.warning("Chunker: Chunks could not be matched to the original text, using the fallback separator")
            return chunks, [self.fallback_separator] * (len(chunks) - 1)
        
        originals = [text[start:end] for start, end in spans]
        separators = [text[spans[i][1]:spans[i + 1][0]] for i in range(len(spans) - 1)]
        return originals, separators
    
    @staticmethod
    def _locate_chunks(text: str, chunks: List[str]) -> Optional[List[Tuple[int, int]]]:
        """Find where each chunk sits in the text, ignoring differences in whitespace.
        
        Args:
            text: The original text
            chunks: Non-empty chunks, in text order
            
        Returns:
            List of (start, end) positions in the text, one per chunk, or None if
            the chunks do not cover the text's non-whitespace characters exactly
        """
        spans: List[Tuple[int, int]] = []
        pos = 0
        length = len(text)
        
        for chunk in chunks:
            start = -1
            for char in chunk:
                if char.isspace():
                    continue
                while pos < length and text[pos].isspace():
                    pos += 1
                if pos >= length or text[pos] != char:
                    return None
                if start < 0:
                    start = pos
                pos += 1
            spans.append((start, pos))
        
        # Anything but whitespace left over means a strategy dropped some text
        if text[pos:].strip():
            return None
        return spans
    
if __name__ == "__main__":
    print("Tests have been migrated to tests/unit/test_chunker.py")
    print("Run: python -m unittest tests.unit.test_chunker")
    print("Or: python -m unittest discover tests")


# Chunker Registry - maps simple chunker names to actual strategy classes
CHUNKER_REGISTRY = {
    "sentence_split": SentenceSplitStrategy,
    "paragraph_split": lambda **kwargs: StringSplitStrategy(delimiters='\n\n', **kwargs),
    "line_split": lambda **kwargs: StringSplitStrategy(delimiters='\n', **kwargs),
    "size_optimizing": SizeOptimizingStrategy,
}


# Valid chunker names for configuration validation
# 
# IMPORTANT FOR MAINTAINERS:
# This constant is imported by config_data_validator.py during startup to validate
# chunker names in configuration files. It works safely because:
# 1. Importing this constant does NOT instantiate any chunker classes
# 2. The classes are only defined, not executed, when this module loads
#
# WARNING: If you add any module-level code that executes during import (e.g., calling
# get_app_config() or instantiating chunkers at module level), this will break the
# startup validation phase. In that case, move this constant to a separate file like
# 'chunker_constants.py' to keep config validation lightweight and independent.
VALID_CHUNKER_NAMES: frozenset = frozenset(CHUNKER_REGISTRY.keys())


def get_chunker_strategy(name: str, **kwargs):
    """
    Get a chunker strategy instance by name.
    
    Args:
        name: The simple name of the chunker (e.g., 'sentence_split', 'paragraph_split')
        **kwargs: Additional parameters to pass to the strategy constructor
        
    Returns:
        An instance of the requested chunker strategy
        
    Raises:
        ValueError: If the chunker name is not found in the registry
        
    Example:
        >>> strategy = get_chunker_strategy('sentence_split', language='ro')  # Language from config
        >>> chunks = strategy.apply(['Some text here.'])
    """
    if name not in CHUNKER_REGISTRY:
        available = ', '.join(CHUNKER_REGISTRY.keys())
        raise ValueError(f"Unknown chunker '{name}'. Available chunkers: {available}")
    
    chunker_class_or_factory = CHUNKER_REGISTRY[name]
    return chunker_class_or_factory(**kwargs)
