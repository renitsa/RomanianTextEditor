"""
Integration tests for workflow with text I/O and processing.
Tests the interaction between TextReader, TextWriter, ProcessingWorkflow, and TextProcessor.
"""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock
from src.text_processor.workflow import ProcessingWorkflow
from src.text_processor.text_io import TextReader, TextWriter
from src.text_processor.chunker import TextChunker, get_chunker_strategy
from src.text_processor.processor import TextProcessor
from tests.fixtures.sample_texts import (
    ENGLISH_SIMPLE, ENGLISH_MULTI_PARAGRAPH, ROMANIAN_SIMPLE,
    EMPTY_TEXT, SINGLE_SENTENCE
)


class TestWorkflowWithRealComponents(unittest.TestCase):
    """Test ProcessingWorkflow with real TextReader and TextWriter."""
    
    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_workflow_with_file_input_and_output(self):
        """Test complete workflow: file -> process -> file."""
        # Create input file
        input_file = self.temp_path / "input.txt"
        input_text = ENGLISH_SIMPLE
        input_file.write_text(input_text, encoding='utf-8')
        
        # Create output file path
        output_file = self.temp_path / "output.txt"
        
        # Setup components
        text_reader = TextReader()
        text_reader.text = text_reader.read_txt(str(input_file))
        
        text_writer = TextWriter(str(output_file))
        
        # Mock processor that transforms text
        mock_processor = Mock(spec=TextProcessor)
        mock_processor.process_text.return_value = f"PROCESSED: {input_text}"
        
        # Create workflow without chunking
        workflow = ProcessingWorkflow(
            processor=mock_processor,
            chunker=None,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=False
        )
        
        # Execute workflow
        success = workflow.process()
        
        # Verify
        self.assertTrue(success)
        self.assertTrue(output_file.exists())
        output_content = output_file.read_text(encoding='utf-8')
        self.assertEqual(output_content, f"PROCESSED: {input_text}")
    
    def test_workflow_with_chunking(self):
        """Test workflow with chunking enabled."""
        # Create input with multiple paragraphs
        input_file = self.temp_path / "input.txt"
        input_text = ENGLISH_MULTI_PARAGRAPH
        input_file.write_text(input_text, encoding='utf-8')
        
        output_file = self.temp_path / "output.txt"
        
        # Setup components with chunker
        text_reader = TextReader()
        text_reader.text = text_reader.read_txt(str(input_file))
        
        text_writer = TextWriter(str(output_file))
        
        # Create chunker with paragraph split
        chunker = TextChunker(language="en")
        chunker.add_strategy(get_chunker_strategy("paragraph_split"))
        
        # Mock processor
        mock_processor = Mock(spec=TextProcessor)
        mock_processor.process_text.side_effect = lambda text: f"[PROCESSED]{text}"
        
        # Create workflow with chunking
        workflow = ProcessingWorkflow(
            processor=mock_processor,
            chunker=chunker,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=False
        )
        
        # Execute
        success = workflow.process()
        
        # Verify
        self.assertTrue(success)
        self.assertEqual(workflow.stats['chunks_processed'], 3)
        
        # Check output contains processed chunks from ENGLISH_MULTI_PARAGRAPH fixture
        output_content = output_file.read_text(encoding='utf-8')
        self.assertIn("[PROCESSED]First paragraph", output_content)
        self.assertIn("[PROCESSED]The second paragraph", output_content)
        self.assertIn("[PROCESSED]The third paragraph", output_content)
    
    def test_workflow_with_console_output(self):
        """Test workflow writing to console (no output file)."""
        input_file = self.temp_path / "input.txt"
        input_file.write_text(ENGLISH_SIMPLE, encoding='utf-8')
        
        # Setup with console output (None path)
        text_reader = TextReader()
        text_reader.text = text_reader.read_txt(str(input_file))
        
        text_writer = TextWriter(None)  # Console output
        
        mock_processor = Mock(spec=TextProcessor)
        mock_processor.process_text.return_value = "Processed for console."
        
        workflow = ProcessingWorkflow(
            processor=mock_processor,
            chunker=None,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=False
        )
        
        # Execute - should not fail
        success = workflow.process()
        
        self.assertTrue(success)
    
    def test_workflow_with_cli_text_input(self):
        """Test workflow with text from CLI (no input file)."""
        output_file = self.temp_path / "output.txt"
        
        # TextReader with CLI text (no file)
        text_reader = TextReader(None)
        text_reader.text = SINGLE_SENTENCE
        
        text_writer = TextWriter(str(output_file))
        
        mock_processor = Mock(spec=TextProcessor)
        mock_processor.process_text.return_value = f"Processed {SINGLE_SENTENCE}"
        
        workflow = ProcessingWorkflow(
            processor=mock_processor,
            chunker=None,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=False
        )
        
        success = workflow.process()
        
        self.assertTrue(success)
        self.assertTrue(output_file.exists())
        self.assertEqual(output_file.read_text(encoding='utf-8'), f"Processed {SINGLE_SENTENCE}")
    
    def test_workflow_statistics_tracking(self):
        """Test that workflow tracks statistics correctly."""
        input_file = self.temp_path / "input.txt"
        input_text = ENGLISH_SIMPLE
        input_file.write_text(input_text, encoding='utf-8')
        
        text_reader = TextReader()
        text_reader.text = text_reader.read_txt(str(input_file))
        
        text_writer = TextWriter(None)
        
        mock_processor = Mock(spec=TextProcessor)
        mock_processor.process_text.return_value = "Processed output."
        
        workflow = ProcessingWorkflow(
            processor=mock_processor,
            chunker=None,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=False
        )
        
        workflow.process()
        
        # Check statistics
        self.assertEqual(workflow.stats['input_length'], len(input_text))
        self.assertEqual(workflow.stats['output_length'], len("Processed output."))
        self.assertGreaterEqual(workflow.stats['processing_time'], 0)  # Can be 0 for very fast ops
        self.assertEqual(workflow.stats['chunks_processed'], 1)
        self.assertEqual(workflow.stats['total_chunks'], 1)


class TestWorkflowSeparators(unittest.TestCase):
    """Test that the output keeps the separators of the input between chunks."""
    
    def run_workflow(self, text, process, chunker):
        """Run the workflow on text and return what was written."""
        text_reader = TextReader(None)
        text_reader.text = text
        text_writer = TextWriter(None)
        text_writer.write = Mock(return_value=True)
        
        mock_processor = Mock(spec=TextProcessor)
        mock_processor.process_text.side_effect = process
        
        workflow = ProcessingWorkflow(
            processor=mock_processor, chunker=chunker,
            text_reader=text_reader, text_writer=text_writer, verbose=False
        )
        self.assertTrue(workflow.process())
        return text_writer.write.call_args[0][0]
    
    def make_chunker(self):
        """Chunker that splits on blank lines."""
        chunker = TextChunker(language="en")
        chunker.add_strategy(get_chunker_strategy("paragraph_split", min_size=5, max_size=100))
        return chunker
    
    def test_output_uses_the_original_separators(self):
        """Paragraphs separated by one and two blank lines stay that way."""
        text = "First paragraph.\n\nSecond paragraph.\n\n\nThird paragraph."
        
        output = self.run_workflow(text, lambda chunk: f"<{chunk}>", self.make_chunker())
        
        self.assertEqual(output, "<First paragraph.>\n\n<Second paragraph.>\n\n\n<Third paragraph.>")
    
    def test_whitespace_added_by_the_model_is_not_doubled(self):
        """A trailing newline in the model answer does not add to the original separator."""
        text = "First paragraph.\n\nSecond paragraph."
        
        output = self.run_workflow(text, lambda chunk: chunk + "\n", self.make_chunker())
        
        self.assertEqual(output, "First paragraph.\n\nSecond paragraph.\n")
    
    def test_single_chunk_keeps_blank_lines_of_the_input(self):
        """With no chunking the model gets the text as written, blank lines included."""
        text = "Stanza one,\nline two.\n\nStanza two,\nline two."
        seen = []
        
        def record(chunk):
            seen.append(chunk)
            return chunk
        
        self.run_workflow(text, record, None)
        
        self.assertEqual(seen, [text])
    
    def test_join_chunks(self):
        """_join_chunks puts the separators between chunks and nothing after the last."""
        self.assertEqual(ProcessingWorkflow._join_chunks(["a", "b", "c"], ["\n\n", " "]), "a\n\nb c")
        self.assertEqual(ProcessingWorkflow._join_chunks(["only"], []), "only")
        self.assertEqual(ProcessingWorkflow._join_chunks(["a ", "b"], [""]), "ab")


class TestWorkflowErrorHandling(unittest.TestCase):
    """Test workflow error handling scenarios."""
    
    def setUp(self):
        """Setup mock components."""
        self.mock_processor = Mock(spec=TextProcessor)
        self.mock_chunker = Mock(spec=TextChunker)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_workflow_handles_empty_text(self):
        """Workflow should handle empty input text."""
        text_reader = TextReader(None)
        text_reader.text = EMPTY_TEXT
        
        text_writer = TextWriter(None)
        
        workflow = ProcessingWorkflow(
            processor=self.mock_processor,
            chunker=None,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=False
        )
        
        # Empty text should still process (might return empty or fail gracefully)
        # The actual behavior depends on implementation
        result = workflow.process()
        
        # Just verify it doesn't crash
        self.assertIsInstance(result, bool)
    
    def test_workflow_handles_none_text(self):
        """Workflow should handle None text in reader."""
        text_reader = TextReader(None)
        # text_reader.text remains None
        
        text_writer = TextWriter(None)
        
        workflow = ProcessingWorkflow(
            processor=self.mock_processor,
            chunker=None,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=False
        )
        
        # Should fail gracefully
        result = workflow.process()
        self.assertFalse(result)
    
    def test_workflow_handles_processor_exception(self):
        """Workflow should handle processor exceptions."""
        text_reader = TextReader(None)
        text_reader.text = SINGLE_SENTENCE
        
        text_writer = TextWriter(None)
        
        # Make processor raise exception
        self.mock_processor.process_text.side_effect = Exception("Processing failed")
        
        workflow = ProcessingWorkflow(
            processor=self.mock_processor,
            chunker=None,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=False
        )
        
        result = workflow.process()
        
        # The only chunk failed, so there is nothing worth writing
        self.assertFalse(result)
        self.assertEqual(workflow.stats['failed_chunks'], 1)
    
    def test_workflow_with_partial_chunk_failures(self):
        """Test workflow behavior when some chunks fail."""
        text_reader = TextReader(None)
        text_reader.text = "Chunk1\n\nChunk2\n\nChunk3"
        
        text_writer = TextWriter(None)
        
        # Create chunker
        chunker = TextChunker(language="en")
        chunker.add_strategy(get_chunker_strategy("paragraph_split", min_size=5, max_size=100))
        
        # Processor fails on second chunk
        self.mock_processor.process_text.side_effect = [
            "Processed1",
            Exception("Failed on chunk 2"),
            "Processed3"
        ]
        
        workflow = ProcessingWorkflow(
            processor=self.mock_processor,
            chunker=chunker,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=False
        )
        
        result = workflow.process()
        
        # Partial failure: the failed chunk is kept unchanged and the run still succeeds
        self.assertTrue(result)
        self.assertEqual(workflow.stats['failed_chunks'], 1)
        self.assertEqual(workflow.stats['chunks_processed'], 3)


class TestWorkflowVerboseMode(unittest.TestCase):
    """Test workflow verbose logging."""
    
    def test_verbose_mode_enabled(self):
        """Test that verbose mode can be enabled."""
        text_reader = TextReader(None)
        text_reader.text = "Test"
        
        text_writer = TextWriter(None)
        
        mock_processor = Mock(spec=TextProcessor)
        mock_processor.process_text.return_value = "Output"
        
        # Create with verbose=True
        workflow = ProcessingWorkflow(
            processor=mock_processor,
            chunker=None,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=True
        )
        
        self.assertTrue(workflow.verbose)
        
        # Process should still work
        result = workflow.process()
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
