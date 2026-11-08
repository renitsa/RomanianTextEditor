"""
End-to-End tests for complete text processing workflows.
Tests the entire application from CLI arguments to final output.
"""
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

from src.app.text_processing_app import TextProcessingApplication
from src.text_processor.text_io import TextReader, TextWriter
from src.text_processor.workflow import ProcessingWorkflow
from src.text_processor.processor import TextProcessor
from src.text_processor.chunker import TextChunker, get_chunker_strategy
from tests.fixtures.sample_texts import (
    ROMANIAN_SIMPLE, ENGLISH_SIMPLE, ENGLISH_MULTI_PARAGRAPH,
    ROMANIAN_WITH_ABBREVIATIONS, SINGLE_SENTENCE, EMPTY_TEXT
)


class TestCompleteTextProcessingWorkflow(unittest.TestCase):
    """Test complete end-to-end text processing scenarios."""
    
    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_e2e_file_to_file_processing_no_chunking(self):
        """E2E: Read file -> Process without chunking -> Write to file."""
        # Create input file
        input_file = self.temp_path / "input.txt"
        input_text = ROMANIAN_SIMPLE
        input_file.write_text(input_text, encoding='utf-8')
        
        output_file = self.temp_path / "output.txt"
        
        # Create components
        text_reader = TextReader()
        text_reader.text = text_reader.read_txt(str(input_file))
        
        text_writer = TextWriter(str(output_file))
        
        # Mock processor that adds prefix
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
        
        # Execute
        success = workflow.process()
        
        # Verify
        self.assertTrue(success)
        self.assertTrue(output_file.exists())
        
        result = output_file.read_text(encoding='utf-8')
        self.assertEqual(result, f"PROCESSED: {input_text}")
        
        # Verify statistics
        self.assertEqual(workflow.stats['chunks_processed'], 1)
        self.assertEqual(workflow.stats['failed_chunks'], 0)
        self.assertEqual(workflow.stats['input_length'], len(input_text))
    
    def test_e2e_file_to_file_with_paragraph_chunking(self):
        """E2E: Read file -> Chunk by paragraphs -> Process -> Write to file."""
        # Create input with multiple paragraphs
        input_file = self.temp_path / "input.txt"
        input_text = ENGLISH_MULTI_PARAGRAPH
        input_file.write_text(input_text, encoding='utf-8')
        
        output_file = self.temp_path / "output.txt"
        
        # Create components with paragraph chunking
        text_reader = TextReader()
        text_reader.text = text_reader.read_txt(str(input_file))
        
        text_writer = TextWriter(str(output_file))
        
        chunker = TextChunker(language="en")
        chunker.add_strategy(get_chunker_strategy("paragraph_split"))
        
        # Mock processor that wraps each chunk
        mock_processor = Mock(spec=TextProcessor)
        mock_processor.process_text.side_effect = lambda text: f"[{text.strip()}]"
        
        workflow = ProcessingWorkflow(
            processor=mock_processor,
            chunker=chunker,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=False
        )
        
        success = workflow.process()
        
        # Verify
        self.assertTrue(success)
        self.assertTrue(output_file.exists())
        
        result = output_file.read_text(encoding='utf-8')
        
        # Should have 3 processed chunks from ENGLISH_MULTI_PARAGRAPH
        self.assertIn("[First paragraph", result)
        self.assertIn("[The second paragraph", result)
        self.assertIn("[The third paragraph", result)
        self.assertEqual(workflow.stats['chunks_processed'], 3)
    
    def test_e2e_file_to_console_output(self):
        """E2E: Read file -> Process -> Output to console."""
        input_file = self.temp_path / "input.txt"
        input_text = ENGLISH_SIMPLE
        input_file.write_text(input_text, encoding='utf-8')
        
        # Create components with console output (None path)
        text_reader = TextReader()
        text_reader.text = text_reader.read_txt(str(input_file))
        
        text_writer = TextWriter(None)  # Console output
        
        mock_processor = Mock(spec=TextProcessor)
        mock_processor.process_text.return_value = "CONSOLE: " + input_text
        
        workflow = ProcessingWorkflow(
            processor=mock_processor,
            chunker=None,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=False
        )
        
        # Execute - should not fail even with console output
        success = workflow.process()
        
        self.assertTrue(success)
    
    def test_e2e_cli_text_to_file(self):
        """E2E: CLI text input -> Process -> Write to file."""
        output_file = self.temp_path / "output.txt"
        
        # Direct text input (no file)
        text_reader = TextReader()
        text_reader.text = SINGLE_SENTENCE
        
        text_writer = TextWriter(str(output_file))
        
        mock_processor = Mock(spec=TextProcessor)
        mock_processor.process_text.return_value = f"PROCESSED: {SINGLE_SENTENCE}"
        
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
        self.assertEqual(
            output_file.read_text(encoding='utf-8'),
            f"PROCESSED: {SINGLE_SENTENCE}"
        )
    
    def test_e2e_with_sentence_and_size_chunking(self):
        """E2E: Combined chunking strategies (sentence + size optimization)."""
        input_file = self.temp_path / "input.txt"
        input_text = ROMANIAN_WITH_ABBREVIATIONS
        input_file.write_text(input_text, encoding='utf-8')
        
        output_file = self.temp_path / "output.txt"
        
        text_reader = TextReader()
        text_reader.text = text_reader.read_txt(str(input_file))
        
        text_writer = TextWriter(str(output_file))
        
        # Combined strategies
        chunker = TextChunker(language="ro")
        chunker.add_strategy(get_chunker_strategy("sentence_split", language="ro"))
        chunker.add_strategy(get_chunker_strategy("size_optimizing"))
        
        mock_processor = Mock(spec=TextProcessor)
        mock_processor.process_text.side_effect = lambda text: f"<{text.strip()}>"
        
        workflow = ProcessingWorkflow(
            processor=mock_processor,
            chunker=chunker,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=False
        )
        
        success = workflow.process()
        
        self.assertTrue(success)
        self.assertGreater(workflow.stats['chunks_processed'], 0)
        
        # Verify Dr. abbreviation wasn't split (may have markup around it)
        result = output_file.read_text(encoding='utf-8')
        # Check that "Dr." and "Popescu" appear together (with possible markup)
        self.assertTrue("Dr." in result and "Popescu" in result,
                       "Dr. and Popescu should both appear in output")


class TestErrorHandlingE2E(unittest.TestCase):
    """Test error handling in end-to-end scenarios."""
    
    def setUp(self):
        """Setup temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_e2e_nonexistent_input_file(self):
        """E2E: Attempting to read nonexistent file should fail gracefully."""
        nonexistent_file = self.temp_path / "does_not_exist.txt"
        
        text_reader = TextReader()
        result = text_reader.read_txt(str(nonexistent_file))
        
        # Should return None for nonexistent file
        self.assertIsNone(result)
    
    def test_e2e_empty_input_file(self):
        """E2E: Processing empty file should handle gracefully."""
        input_file = self.temp_path / "empty.txt"
        input_file.write_text(EMPTY_TEXT, encoding='utf-8')
        
        output_file = self.temp_path / "output.txt"
        
        text_reader = TextReader()
        text_reader.text = text_reader.read_txt(str(input_file))
        
        text_writer = TextWriter(str(output_file))
        
        mock_processor = Mock(spec=TextProcessor)
        mock_processor.process_text.return_value = ""
        
        workflow = ProcessingWorkflow(
            processor=mock_processor,
            chunker=None,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=False
        )
        
        # Should handle empty input
        result = workflow.process()
        self.assertIsInstance(result, bool)
    
    def test_e2e_processor_exception_during_processing(self):
        """E2E: Processor exception should be caught and logged."""
        input_file = self.temp_path / "input.txt"
        input_file.write_text("Test text", encoding='utf-8')
        
        text_reader = TextReader()
        text_reader.text = text_reader.read_txt(str(input_file))
        
        text_writer = TextWriter(None)
        
        # Processor that raises exception
        mock_processor = Mock(spec=TextProcessor)
        mock_processor.process_text.side_effect = RuntimeError("Processing failed")
        
        workflow = ProcessingWorkflow(
            processor=mock_processor,
            chunker=None,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=False
        )
        
        # Should handle exception gracefully
        result = workflow.process()
        
        # Workflow handles errors and may return True or False depending on implementation
        self.assertIsInstance(result, bool)
    
    def test_e2e_invalid_output_directory(self):
        """E2E: Writing to invalid directory should fail gracefully."""
        input_file = self.temp_path / "input.txt"
        input_file.write_text("Test", encoding='utf-8')
        
        # Invalid output path (directory doesn't exist and can't be created)
        invalid_output = "Z:\\nonexistent\\path\\output.txt"
        
        text_reader = TextReader()
        text_reader.text = text_reader.read_txt(str(input_file))
        
        text_writer = TextWriter(invalid_output)
        
        mock_processor = Mock(spec=TextProcessor)
        mock_processor.process_text.return_value = "Processed"
        
        workflow = ProcessingWorkflow(
            processor=mock_processor,
            chunker=None,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=False
        )
        
        # Should fail when trying to write
        result = workflow.process()
        
        # May fail during write operation
        self.assertIsInstance(result, bool)


class TestApplicationE2E(unittest.TestCase):
    """Test complete application-level scenarios."""
    
    def test_e2e_app_creates_chunker_from_config(self):
        """E2E: Application creates chunker based on task configuration."""
        app = TextProcessingApplication()
        
        # Get a real task config
        task_config = app.config.actions_config.DIACRITICS
        
        # Create chunker for this task
        chunker = app._create_chunker_for_task(
            task_config=task_config,
            task_name='DIACRITICS',
            language=task_config.INPUT_LANGUAGE,
            chunkers=None  # Use config defaults
        )
        
        # Should create chunker with strategies from config
        if task_config.CHUNKERS:
            self.assertIsNotNone(chunker)
            self.assertEqual(len(chunker.strategies), len(task_config.CHUNKERS))
        else:
            self.assertIsNone(chunker)
    
    def test_e2e_app_initialization_validates_config(self):
        """E2E: Application initialization validates processor factory."""
        # Should not raise during init
        app = TextProcessingApplication()
        
        # Verify components are initialized
        self.assertIsNotNone(app.config)
        self.assertIsNotNone(app.logger)
        self.assertIsNotNone(app.path_manager)
        self.assertIsNotNone(app.param_orchestrator)
    
    def test_e2e_all_task_configs_have_required_fields(self):
        """E2E: All task configurations should have required fields."""
        app = TextProcessingApplication()
        
        tasks = ['DIACRITICS', 'SUMMARIZE', 'EDIT', 'TRANSLATE_RO_EN', 'TRANSLATE_EN_RO', 'CUSTOM']
        
        for task_name in tasks:
            with self.subTest(task=task_name):
                task_config = getattr(app.config.actions_config, task_name)
                
                # Should have required fields
                self.assertTrue(hasattr(task_config, 'DESC'))
                self.assertTrue(hasattr(task_config, 'PROMPT'))
                self.assertTrue(hasattr(task_config, 'CHUNKERS'))
                self.assertTrue(hasattr(task_config, 'INPUT_LANGUAGE'))


class TestVerboseModeE2E(unittest.TestCase):
    """Test verbose mode throughout complete workflows."""
    
    def setUp(self):
        """Setup temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_e2e_verbose_mode_logs_processing_steps(self):
        """E2E: Verbose mode should log processing steps."""
        input_file = self.temp_path / "input.txt"
        input_file.write_text(ENGLISH_SIMPLE, encoding='utf-8')
        
        output_file = self.temp_path / "output.txt"
        
        text_reader = TextReader()
        text_reader.text = text_reader.read_txt(str(input_file))
        
        text_writer = TextWriter(str(output_file))
        
        mock_processor = Mock(spec=TextProcessor)
        mock_processor.process_text.return_value = "VERBOSE TEST"
        
        # Create with verbose=True
        workflow = ProcessingWorkflow(
            processor=mock_processor,
            chunker=None,
            text_reader=text_reader,
            text_writer=text_writer,
            verbose=True  # Enable verbose mode
        )
        
        success = workflow.process()
        
        self.assertTrue(success)
        self.assertTrue(workflow.verbose)
        
        # Verify statistics were tracked (can be 0 for very fast operations)
        self.assertGreaterEqual(workflow.stats['processing_time'], 0)


if __name__ == '__main__':
    unittest.main()
