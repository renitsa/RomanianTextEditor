"""
Unit tests for text chunking strategies.
Migrated and enhanced from src/text_processor/chunker.py __main__ section.
"""
import unittest
from src.text_processor.chunker import (
    TextChunker,
    StringSplitStrategy,
    SentenceSplitStrategy,
    SizeOptimizingStrategy,
    get_chunker_strategy,
    VALID_CHUNKER_NAMES,
    CHUNKER_REGISTRY
)

# Import from fixtures package (tests is in sys.path via conftest.py)
from tests.fixtures.sample_texts import (
    ROMANIAN_SIMPLE,
    ROMANIAN_WITH_ABBREVIATIONS,
    ROMANIAN_MULTI_PARAGRAPH,
    ENGLISH_WITH_ABBREVIATIONS,
    EMPTY_TEXT,
    SINGLE_SENTENCE,
    VERY_LONG_TEXT,
    TEXT_WITH_NO_PUNCTUATION,
    CHUNKING_TEST_CASES
)


class TestChunkerRegistry(unittest.TestCase):
    """Test chunker registry and factory function."""
    
    def test_registry_has_expected_chunkers(self):
        """Registry should contain all expected chunker types."""
        expected = {'sentence_split', 'paragraph_split', 'line_split', 'size_optimizing'}
        self.assertEqual(VALID_CHUNKER_NAMES, expected)
    
    def test_get_chunker_strategy_sentence_split(self):
        """Should create SentenceSplitStrategy."""
        strategy = get_chunker_strategy('sentence_split', language='ro')
        self.assertIsInstance(strategy, SentenceSplitStrategy)
    
    def test_get_chunker_strategy_paragraph_split(self):
        """Should create StringSplitStrategy with paragraph delimiters."""
        strategy = get_chunker_strategy('paragraph_split')
        self.assertIsInstance(strategy, StringSplitStrategy)
    
    def test_get_chunker_strategy_line_split(self):
        """Should create StringSplitStrategy with line delimiters."""
        strategy = get_chunker_strategy('line_split')
        self.assertIsInstance(strategy, StringSplitStrategy)
    
    def test_get_chunker_strategy_size_optimizing(self):
        """Should create SizeOptimizingStrategy."""
        strategy = get_chunker_strategy('size_optimizing')
        self.assertIsInstance(strategy, SizeOptimizingStrategy)
    
    def test_get_chunker_strategy_invalid_name(self):
        """Should raise ValueError for invalid chunker name."""
        with self.assertRaises(ValueError) as cm:
            get_chunker_strategy('invalid_chunker')
        
        self.assertIn('Unknown chunker', str(cm.exception))
    

class TestStringSplitStrategy(unittest.TestCase):
    """Test StringSplitStrategy (paragraph/line splitting)."""
    
    def test_paragraph_split_basic(self):
        """Should split on double newlines (paragraphs)."""
        strategy = StringSplitStrategy(delimiters='\n\n')
        chunks = strategy.apply([ROMANIAN_MULTI_PARAGRAPH])
        
        self.assertEqual(len(chunks), 3)  # 3 paragraphs
    
    def test_line_split_basic(self):
        """Should split on single newlines."""
        text = "Line 1\nLine 2\nLine 3"
        # Set min_size=0 to prevent merging of small chunks
        strategy = StringSplitStrategy(delimiters='\n', min_size=0)
        chunks = strategy.apply([text])
        
        self.assertGreater(len(chunks), 1)
    
    def test_empty_text_returns_empty(self):
        """Empty text should return empty list."""
        strategy = StringSplitStrategy(delimiters='\n\n')
        chunks = strategy.apply([EMPTY_TEXT])
        
        self.assertEqual(chunks, [])
    
    def test_delimiter_preservation_discard(self):
        """Should discard delimiters in discard mode."""
        text = "Part1\n\nPart2\n\nPart3"
        strategy = StringSplitStrategy(
            delimiters='\n\n',
            preserve_delimiters='discard'
        )
        chunks = strategy.apply([text])
        self.assertGreater(len(chunks), 0)
        # Check that delimiters are not in chunks
        for chunk in chunks:
            self.assertNotIn('\n\n', chunk)
    
    def test_invalid_preserve_delimiters_raises_error(self):
        """Invalid preserve_delimiters option should raise ValueError."""
        with self.assertRaises(ValueError):
            StringSplitStrategy(
                delimiters='\n\n',
                preserve_delimiters='invalid_option'
            )


class TestSentenceSplitStrategy(unittest.TestCase):
    """Test SentenceSplitStrategy with language-specific abbreviations."""
    
    def test_romanian_abbreviations_not_split(self):
        """Romanian abbreviations (Dr., Dna.) should not cause splits."""
        strategy = SentenceSplitStrategy(language='ro')
        chunks = strategy.apply([ROMANIAN_WITH_ABBREVIATIONS])
        
        # Check that Dr. Popescu stays together
        found_together = any('Dr. Popescu' in chunk for chunk in chunks)
        self.assertTrue(found_together, "Dr. Popescu should stay in same chunk")
    
    def test_english_abbreviations_not_split(self):
        """English abbreviations (Dr., Mrs.) should not cause splits."""
        strategy = SentenceSplitStrategy(language='en')
        chunks = strategy.apply([ENGLISH_WITH_ABBREVIATIONS])
        
        # Check that Dr. Smith stays together
        found_together = any('Dr. Smith' in chunk for chunk in chunks)
        self.assertTrue(found_together, "Dr. Smith should stay in same chunk")
    
    def test_language_parameter_affects_behavior(self):
        """Different languages should use different abbreviation sets."""
        ro_strategy = SentenceSplitStrategy(language='ro')
        en_strategy = SentenceSplitStrategy(language='en')
        
        # Abbreviation sets should be different
        self.assertNotEqual(ro_strategy.abbreviations, en_strategy.abbreviations)
    
    def test_abbreviation_must_start_a_word(self):
        """A word that merely ends like an abbreviation (hotel. / tel.) still ends the sentence."""
        strategy = SentenceSplitStrategy(language='ro', min_size=5)
        
        for text in ("Am fost la hotel. Apoi am plecat.", "Un exemplu complex. Altul."):
            with self.subTest(text=text):
                self.assertEqual(len(strategy._detect_sentences(text)), 2)
    
    def test_abbreviation_at_word_start_not_split(self):
        """Real abbreviations are still recognised, also after punctuation and at the text start."""
        strategy = SentenceSplitStrategy(language='ro', min_size=5)
        
        for text in ("Vezi pag. 5 si cap. 2. Final.", "(Dr. Popescu a venit.) Bine.", "Dr. Popescu a venit."):
            with self.subTest(text=text):
                sentences = strategy._detect_sentences(text)
                self.assertTrue(any(s.strip().startswith(("Vezi pag. 5 si cap. 2.", "(Dr. Popescu", "Dr. Popescu"))
                                    for s in sentences))
                self.assertFalse(any(s.strip() in ("Vezi pag.", "(Dr.", "Dr.") for s in sentences))
    
    def test_single_sentence_returns_one_chunk(self):
        """Single sentence should return single chunk."""
        strategy = SentenceSplitStrategy(language='ro')
        chunks = strategy.apply([SINGLE_SENTENCE])
        
        self.assertEqual(len(chunks), 1)
    
    def test_text_with_no_punctuation(self):
        """Text without sentence delimiters should return as-is."""
        strategy = SentenceSplitStrategy(language='ro')
        chunks = strategy.apply([TEXT_WITH_NO_PUNCTUATION])
        
        # Should return at least one chunk
        self.assertGreater(len(chunks), 0)
    
    def test_multiple_sentence_terminators(self):
        """Should split on various sentence terminators (. ! ?)."""
        text = "First sentence. Second sentence! Third sentence? Fourth sentence."
        strategy = SentenceSplitStrategy(language='ro')
        chunks = strategy.apply([text])
        
        # Should have multiple chunks (at least 2)
        self.assertGreaterEqual(len(chunks), 2)


class TestSizeOptimizingStrategy(unittest.TestCase):
    """Test SizeOptimizingStrategy for combining chunks."""
    
    def test_combines_small_chunks(self):
        """Should combine chunks smaller than min_size."""
        small_chunks = CHUNKING_TEST_CASES['many_small']
        
        strategy = SizeOptimizingStrategy(min_size=100, max_size=200)
        optimized = strategy.apply(small_chunks)
        
        # Should have fewer chunks
        self.assertLess(len(optimized), len(small_chunks))
    
    def test_respects_max_size(self):
        """Combined chunks should not exceed max_size."""
        strategy = SizeOptimizingStrategy(min_size=10, max_size=50)
        chunks = ["Short", "A bit longer", "Even longer chunk here"]
        
        optimized = strategy.apply(chunks)
        
        for chunk in optimized:
            self.assertLessEqual(len(chunk), 50)
    
    def test_empty_chunks_filtered(self):
        """Empty chunks should be filtered out."""
        chunks_with_empty = CHUNKING_TEST_CASES['empty_chunks']
        
        strategy = SizeOptimizingStrategy(min_size=5, max_size=100)
        optimized = strategy.apply(chunks_with_empty)
        
        # No empty chunks in result
        self.assertTrue(all(chunk.strip() for chunk in optimized))
    
    def test_single_chunk_unchanged(self):
        """Single chunk should pass through."""
        strategy = SizeOptimizingStrategy(min_size=10, max_size=100)
        chunks = ["Single chunk here"]
        
        optimized = strategy.apply(chunks)
        
        self.assertEqual(len(optimized), 1)
    

class TestTextChunker(unittest.TestCase):
    """Test TextChunker orchestration of strategies."""
    
    def test_no_strategies_returns_as_is(self):
        """Chunker with no strategies should return text unchanged."""
        chunker = TextChunker(language='ro')
        result = chunker.chunk_text(ROMANIAN_SIMPLE)
        
        self.assertEqual(result, [ROMANIAN_SIMPLE])
    
    def test_single_strategy_applied(self):
        """Single strategy should be applied."""
        chunker = TextChunker(language='ro')
        chunker.add_strategy(SentenceSplitStrategy(language='ro'))
        
        result = chunker.chunk_text(ROMANIAN_MULTI_PARAGRAPH)
        
        self.assertGreater(len(result), 1)
    
    def test_multiple_strategies_chained(self):
        """Multiple strategies should be applied in sequence."""
        chunker = TextChunker(language='ro')
        chunker.add_strategy(StringSplitStrategy(delimiters='\n\n'))
        chunker.add_strategy(SentenceSplitStrategy(language='ro'))
        
        result = chunker.chunk_text(ROMANIAN_MULTI_PARAGRAPH)
        
        # Should have more chunks than just paragraph split
        self.assertGreater(len(result), 0)
    
    def test_default_strategies_initialized(self):
        """Should initialize with default strategies when requested."""
        chunker = TextChunker(use_default_strategies=True, language='ro')
        
        self.assertGreater(len(chunker.strategies), 0)
    
    def test_language_parameter_stored(self):
        """Language parameter should be stored."""
        chunker_ro = TextChunker(language='ro')
        chunker_en = TextChunker(language='en')
        
        self.assertEqual(chunker_ro.language, 'ro')
        self.assertEqual(chunker_en.language, 'en')
    
    def test_empty_text_returns_empty(self):
        """Empty text should return empty list."""
        chunker = TextChunker(language='ro')
        chunker.add_strategy(SentenceSplitStrategy(language='ro'))
        
        result = chunker.chunk_text(EMPTY_TEXT)
        
        self.assertEqual(result, [])
    
    def test_add_strategy_returns_self(self):
        """add_strategy should return self for chaining."""
        chunker = TextChunker(language='ro')
        result = chunker.add_strategy(SentenceSplitStrategy(language='ro'))
        
        self.assertIs(result, chunker)


class TestChunkTextWithSeparators(unittest.TestCase):
    """Test that chunking can recover the original text between the chunks."""
    
    MULTI_PARAGRAPH = (
        "Primul paragraf are doua propozitii. Iata a doua.\n\n"
        "Al doilea paragraf e scurt.\n\n\n"
        "Al treilea: cu trei linii\nsi un rand nou.\nUltima linie."
    )
    
    def make_paragraph_chunker(self):
        """Chunker that splits on blank lines into small chunks."""
        chunker = TextChunker(language='ro')
        chunker.add_strategy(StringSplitStrategy(min_size=5, max_size=60, delimiters='\n\n'))
        chunker.add_strategy(SizeOptimizingStrategy(min_size=5, max_size=60))
        return chunker
    
    def test_original_separators_are_recovered(self):
        """Blank lines of different lengths between chunks are kept as they were."""
        chunks, separators = self.make_paragraph_chunker().chunk_text_with_separators(self.MULTI_PARAGRAPH)
        
        self.assertEqual(len(chunks), 3)
        self.assertEqual(separators, ["\n\n", "\n\n\n"])
    
    def test_chunks_keep_their_inner_layout(self):
        """Line breaks inside a chunk are not normalized."""
        chunks, _ = self.make_paragraph_chunker().chunk_text_with_separators(self.MULTI_PARAGRAPH)
        
        self.assertEqual(chunks[2], "Al treilea: cu trei linii\nsi un rand nou.\nUltima linie.")
    
    def test_joining_chunks_and_separators_gives_back_the_text(self):
        """Chunks plus separators rebuild the original text exactly."""
        chunks, separators = self.make_paragraph_chunker().chunk_text_with_separators(self.MULTI_PARAGRAPH)
        
        rebuilt = "".join(chunk + sep for chunk, sep in zip(chunks, separators + [""]))
        self.assertEqual(rebuilt, self.MULTI_PARAGRAPH)
    
    def test_single_chunk_keeps_original_layout(self):
        """A text that stays in one chunk keeps its blank lines (e.g. poem stanzas)."""
        text = "Prima strofa,\nal doilea rand.\n\nA doua strofa,\nal doilea rand."
        chunker = TextChunker(language='ro')
        chunker.add_strategy(SentenceSplitStrategy(language='ro'))
        chunker.add_strategy(SizeOptimizingStrategy())
        
        chunks, separators = chunker.chunk_text_with_separators(text)
        
        self.assertEqual(chunks, [text])
        self.assertEqual(separators, [])
    
    def test_single_rewritten_chunk_uses_strategy_output(self):
        """A rewriting strategy's single chunk is not replaced with the original text."""
        class ShoutingStrategy(StringSplitStrategy):
            def apply(self, chunks):
                return [chunk.upper() for chunk in chunks]
        
        chunker = TextChunker(language='ro')
        chunker.add_strategy(ShoutingStrategy())
        
        chunks, separators = chunker.chunk_text_with_separators("one two")
        
        self.assertEqual(chunks, ["ONE TWO"])
        self.assertEqual(separators, [])
    
    def test_sentence_chunks_keep_single_space_separators(self):
        """Chunks that were split inside a paragraph are joined with the original space."""
        text = "Prima propozitie este aici. A doua propozitie vine dupa. A treia incheie textul."
        chunker = TextChunker(language='ro')
        chunker.add_strategy(SentenceSplitStrategy(min_size=5, max_size=40, language='ro'))
        
        chunks, separators = chunker.chunk_text_with_separators(text)
        
        self.assertGreater(len(chunks), 1)
        self.assertEqual(set(separators), {" "})
    
    def test_empty_text(self):
        """Empty text gives no chunks and no separators."""
        self.assertEqual(TextChunker(language='ro').chunk_text_with_separators(""), ([], []))
        self.assertEqual(TextChunker(language='ro').chunk_text_with_separators("   \n "), ([], []))
    
    def test_fallback_separator_when_chunks_cannot_be_matched(self):
        """If a strategy rewrites the text, the configured fallback separator is used."""
        class ShoutingStrategy(StringSplitStrategy):
            def apply(self, chunks):
                return [part.upper() for chunk in chunks for part in chunk.split("\n\n")]
        
        chunker = TextChunker(language='ro')
        chunker.add_strategy(ShoutingStrategy())
        chunker.fallback_separator = "<fallback>"
        
        chunks, separators = chunker.chunk_text_with_separators("one\n\ntwo\n\nthree")
        
        self.assertEqual(chunks, ["ONE", "TWO", "THREE"])
        self.assertEqual(separators, ["<fallback>", "<fallback>"])
    
    def test_fallback_separator_when_a_strategy_drops_text(self):
        """Dropped text means the chunks do not cover the input, so the fallback is used."""
        class DroppingStrategy(StringSplitStrategy):
            def apply(self, chunks):
                return [part for chunk in chunks for part in chunk.split("\n\n")][:2]
        
        chunker = TextChunker(language='ro')
        chunker.add_strategy(DroppingStrategy())
        
        chunks, separators = chunker.chunk_text_with_separators("one\n\ntwo\n\nthree")
        
        self.assertEqual(chunks, ["one", "two"])
        self.assertEqual(separators, [chunker.fallback_separator])
    
    def test_fallback_separator_comes_from_config(self):
        """The default fallback separator is read from text_processing_config.json."""
        from src.config.app_config import get_app_config
        
        chunker = TextChunker(language='ro')
        
        self.assertEqual(chunker.fallback_separator, get_app_config().text_config.FALLBACK_CHUNK_SEPARATOR)
    
    def test_locate_chunks_ignores_whitespace_differences(self):
        """Chunks that were merged with different whitespace are still found in the text."""
        spans = TextChunker._locate_chunks("ab  cd\n\nef", ["ab cd", "ef"])
        
        self.assertEqual(spans, [(0, 6), (8, 10)])
    
    def test_locate_chunks_returns_none_for_different_text(self):
        """Chunks with other characters than the text cannot be located."""
        self.assertIsNone(TextChunker._locate_chunks("abc def", ["abc", "xyz"]))


class TestChunkerEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_very_long_text(self):
        """Should handle very long text without errors."""
        chunker = TextChunker(language='ro')
        chunker.add_strategy(SentenceSplitStrategy(language='ro'))
        chunker.add_strategy(SizeOptimizingStrategy(min_size=500, max_size=1000))
        
        # Should not raise exception
        result = chunker.chunk_text(VERY_LONG_TEXT)
        self.assertGreater(len(result), 0)
    

class TestChunkStrategyBaseClass(unittest.TestCase):
    """Test ChunkStrategy base class functionality."""
    
    def test_merge_small_chunks_combines_small(self):
        """_merge_small_chunks should combine chunks below min_size."""
        strategy = SentenceSplitStrategy(language='ro')
        chunks = ["Small", "Also small", "Tiny"]
        
        merged = strategy._merge_small_chunks(chunks, min_size=20, max_size=100)
        
        # Should have fewer chunks than input
        self.assertLess(len(merged), len(chunks))
    
    def test_merge_small_chunks_respects_max_size(self):
        """_merge_small_chunks should respect max_size."""
        strategy = SentenceSplitStrategy(language='ro')
        chunks = ["A" * 30, "B" * 30, "C" * 30]
        
        merged = strategy._merge_small_chunks(chunks, min_size=10, max_size=50)
        
        for chunk in merged:
            self.assertLessEqual(len(chunk), 50)
    
    def test_merge_small_chunks_filters_empty_strings(self):
        """_merge_small_chunks should filter out empty strings."""
        strategy = SentenceSplitStrategy(language='ro')
        chunks = ["", "Not empty", "", "Also not empty", ""]
        
        merged = strategy._merge_small_chunks(chunks, min_size=5, max_size=100)
        
        # No empty chunks in result
        self.assertTrue(all(chunk.strip() for chunk in merged))


if __name__ == '__main__':
    unittest.main()
