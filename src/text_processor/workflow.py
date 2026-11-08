import time
from typing import Optional, Dict, Any, List, Tuple
from src.text_processor.text_io import TextReader, TextWriter
from src.text_processor.chunker import TextChunker
from src.text_processor.processor import TextProcessor
from src.utils.app_logger import get_logger


class ProcessingWorkflow:
    """Class for managing the text processing workflow with improved error handling and flexibility."""
    
    def __init__(self, 
                 processor: TextProcessor, 
                 chunker: Optional[TextChunker],
                 text_reader: TextReader,
                 text_writer: TextWriter,
                 verbose: bool = False):
        
        """Initialize the processing workflow.
        
        Args:
            processor: Text processor instance 
            chunker: TextChunker instance with configured strategies, or None for no chunking
            text_reader: TextReader instance with text already loaded
            text_writer: TextWriter instance configured for output destination
            verbose: Enable verbose logging
        """
        self.processor = processor
        self.chunker = chunker
        self.text_reader = text_reader
        self.text_writer = text_writer
        self.verbose = verbose
        
        # Initialize logger with centralized configuration and verbose mode
        self.logger = get_logger("RomanianTextEditor.TextProcessor", verbose_mode=verbose)
        
        # Workflow statistics
        self.stats = {
            'chunks_processed': 0,
            'total_chunks': 0,
            'processing_time': 0.0,
            'input_length': 0,
            'output_length': 0,
            'failed_chunks': 0
        }
    
    def process(self, **kwargs) -> bool:
        """Process the input text by sending each chunk through the processor.
        
        Args:
            **kwargs: Additional arguments to pass to the processor's process_text method
            
        Returns:
            True if processing succeeded, False otherwise
        """
        start_time = time.time()
        
        try:
            # Read input text
            if self.text_reader.text is None:
                self.logger.error("No text available in TextReader")
                return False
                
            input_text = self.text_reader.text
            self.stats['input_length'] = len(input_text)
            
            self.logger.debug(f"Workflow: Starting workflow, input length: {len(input_text)}")
            self.logger.verbose(f"Workflow: Input text preview: {input_text[:100]}...")
            
            # Chunk the text using TextChunker strategies
            chunked = self._chunk_text(input_text)
            if not chunked:
                return False
            chunks, separators = chunked
            
            # Process chunks with the processor
            processed_content = self._process_chunks(chunks, separators, **kwargs)
            if processed_content is None:
                return False
            
            # Write output
            success = self._write_output(processed_content)
            
            # Update final statistics
            self.stats['processing_time'] = time.time() - start_time
            self.stats['success_rate'] = ((self.stats['chunks_processed'] - self.stats['failed_chunks']) / 
                                        self.stats['chunks_processed'] * 100) if self.stats['chunks_processed'] > 0 else 0
            
            self.logger.debug(f"Workflow: Workflow completed successfully. Stats: {self.stats}")
            return success
            
        except Exception as e:
            self.logger.error(f"Workflow: Unexpected error in processing workflow: {e}")
            return False
    
    def _chunk_text(self, input_text: str) -> Optional[Tuple[List[str], List[str]]]:
        """Divide the text into chunks using TextChunker, or return single chunk if no chunker.
        
        Returns:
            Tuple (chunks, separators) where separators[i] is the text to put between
            the processed chunks i and i + 1, or None if there is nothing to process
        """
        chunk_start = time.time()
        
        # If no chunker configured, treat entire text as single chunk
        if self.chunker is None:
            self.logger.verbose("Workflow: No chunker configured - processing entire text as single chunk")
            self.stats['total_chunks'] = 1
            print("Processing entire text as single chunk (no chunking)")
            return [input_text.strip()], []
        
        self.logger.verbose("Workflow: Starting text chunking with configured strategies")
        
        try:
            # The chunker returns the chunks together with the original text between them
            chunks, separators = self.chunker.chunk_text_with_separators(input_text)
            
            if not chunks:
                self.logger.warning("Workflow: No chunks were created from input text, using fallback")
                # Fallback: treat entire text as one chunk
                chunks, separators = [input_text.strip()], []
            
            if not any(chunk.strip() for chunk in chunks):
                self.logger.error("Workflow: All chunks were empty after filtering")
                return None
            
            self.stats['total_chunks'] = len(chunks)
            chunk_time = time.time() - chunk_start
            
            # Print chunk count info for user (always, not just verbose)
            print(f"Text split into {len(chunks)} chunk{'s' if len(chunks) != 1 else ''}")
            
            if len(chunks) > 1:
                chunk_sizes = [len(chunk) for chunk in chunks]
                avg_size = sum(chunk_sizes) / len(chunk_sizes)
                self.logger.verbose(
                    f"Workflow: Text chunking completed - {len(chunks)} chunks, "
                    f"avg_size={avg_size:.0f}, min={min(chunk_sizes)}, max={max(chunk_sizes)}, "
                    f"duration={chunk_time:.3f}s"
                )
            else:
                self.logger.verbose(
                    f"Workflow: Text chunking completed - {len(chunks)} chunk, "
                    f"size={len(chunks[0])}, duration={chunk_time:.3f}s"
                )
            
            return chunks, separators
            
        except Exception as e:
            self.logger.error(f"Workflow: Error chunking text: {e}")
            self.logger.warning("Workflow: Chunking failed - falling back to single chunk processing")
            return [input_text.strip()], []
    
    def _process_chunks(self, chunks: List[str], separators: List[str], **kwargs) -> Optional[str]:
        """Process each chunk with the processor and join the results.
        
        Args:
            chunks: The chunks to process
            separators: Text to put between the processed chunks; one fewer than the chunks
            **kwargs: Additional arguments for the processor's process_text method
            
        Returns:
            The processed text, or None if every chunk failed
        """
        process_start = time.time()
        self.logger.verbose(f"Workflow: Processing {len(chunks)} chunks")
        
        processed_chunks = []
        
        try:
            for i, chunk in enumerate(chunks, 1):
                chunk_start = time.time()
                preview = chunk[:80].replace('\n', ' ') + "..." if len(chunk) > 80 else chunk.replace('\n', ' ')
                
                # Show progress for all users (not just verbose) with chunk preview
                chunk_preview = chunk[:30].replace('\n', ' ')
                if len(chunk) > 30:
                    chunk_preview += "..."
                print(f"Processing chunk {i}/{len(chunks)}: {chunk_preview}", end='\r')
                
                try:
                    # Process the chunk with the appropriate method
                    processed_chunk = self.processor.process_text(chunk, **kwargs)
                    chunk_time = time.time() - chunk_start
                    
                    # Fallback behavior: If processor fails (returns None), use original chunk
                    # This allows workflow to continue with partial success rather than failing completely
                    if processed_chunk is None:
                        self.logger.warning(f"Workflow: Processor returned None for chunk {i}, using original text as fallback")
                        processed_chunk = chunk  # Use original chunk as fallback
                        self.stats['failed_chunks'] += 1
                    
                    processed_chunks.append(processed_chunk)
                    self.stats['chunks_processed'] += 1
                    
                    output_preview = processed_chunk[:80].replace('\n', ' ') + "..." if len(processed_chunk) > 80 else processed_chunk.replace('\n', ' ')
                    self.logger.verbose(f"Workflow: Processed chunk {i}/{len(chunks)} ({chunk_time:.3f}s)")
                    self.logger.debug(f"Workflow: Chunk {i} result", 
                                    input_preview=preview[:30],
                                    output_preview=output_preview[:30],
                                    duration=f"{chunk_time:.3f}s")
                
                except Exception as chunk_error:
                    chunk_time = time.time() - chunk_start
                    self.logger.error(f"Workflow: Error processing chunk {i}: {chunk_error}",
                                    chunk_preview=preview[:30],
                                    duration=f"{chunk_time:.3f}s")
                    processed_chunks.append(chunk)  # Use original chunk as fallback
                    self.stats['chunks_processed'] += 1
                    self.stats['failed_chunks'] += 1
                    self.logger.verbose(f"Workflow: Failed chunk {i}/{len(chunks)}, using original text")
            
            # Clear the progress line (wider to accommodate chunk preview)
            print(" " * 80, end='\r')
            
            failed = self.stats['failed_chunks']
            if failed == len(chunks):
                error_msg = f"All {len(chunks)} chunks failed to process (check that the model is available). No output written."
                print(f"ERROR: {error_msg}")
                self.logger.error(f"Workflow: {error_msg}")
                return None
            if failed:
                warning_msg = f"{failed} of {len(chunks)} chunks could not be processed and were kept unchanged in the output"
                print(f"WARNING: {warning_msg}")
                self.logger.warning(f"Workflow: {warning_msg}")
            
            # Join processed chunks with the separators that were between them in the input
            processed_content = self._join_chunks(processed_chunks, separators)
            self.stats['output_length'] = len(processed_content)
            
            process_time = time.time() - process_start
            success_rate = ((self.stats['chunks_processed'] - self.stats['failed_chunks']) / 
                          self.stats['chunks_processed'] * 100) if self.stats['chunks_processed'] > 0 else 0
            
            self.logger.verbose(
                f"Workflow: Chunk processing completed - success_rate={success_rate:.1f}%, "
                f"failed={self.stats['failed_chunks']}, duration={process_time:.3f}s"
            )
            
            return processed_content
            
        except Exception as e:
            self.logger.critical(f"Workflow: Critical error processing chunks: {e}")
            return None
    
    @staticmethod
    def _join_chunks(processed_chunks: List[str], separators: List[str]) -> str:
        """Join processed chunks, restoring the text that originally separated them.
        
        Trailing whitespace the model added to a chunk is dropped, because the
        original separator replaces it.
        
        Args:
            processed_chunks: The processed text of each chunk
            separators: Original text between the chunks; one fewer than the chunks
            
        Returns:
            The joined text
        """
        parts: List[str] = []
        for index, piece in enumerate(processed_chunks[:-1]):
            parts.append(piece.rstrip())
            parts.append(separators[index])
        parts.append(processed_chunks[-1])
        return "".join(parts)
    
    def _write_output(self, processed_content: str) -> bool:
        """Write processed content using the configured TextWriter.
        
        The TextWriter instance writes to file or console based on
        how it was configured during initialization.
        
        Args:
            processed_content: The processed text to write
            
        Returns:
            True if write succeeded, False otherwise
        """
        write_start = time.time()
        self.logger.verbose(f"Workflow: Writing output - content_length={len(processed_content)}")
        
        # TextWriter handles the destination (file or console)
        success = self.text_writer.write(processed_content)
        write_time = time.time() - write_start
        
        if success:
            self.logger.verbose(f"Workflow: Output written successfully - duration={write_time:.3f}s")
            self._log_processing_summary()
        else:
            self.logger.error(f"Workflow: Failed to write output - duration={write_time:.3f}s")
        
        return success
    
    def _log_processing_summary(self) -> None:
        """Log a comprehensive processing summary."""
        self.logger.verbose(
            f"Workflow: Processing Summary - total_time={self.stats['processing_time']:.2f}s, "
            f"chunks={self.stats['chunks_processed']}/{self.stats['total_chunks']}, "
            f"failed={self.stats['failed_chunks']}, "
            f"input_len={self.stats['input_length']}, output_len={self.stats['output_length']}"
        )
        
        # For now, show length change percentage for all tasks; can be adjusted per task later
        if self.stats['input_length'] > 0:
            ratio = self.stats['output_length'] / self.stats['input_length']
            change_pct = (ratio - 1) * 100
            if abs(change_pct) > 1:  # Only log if change is > 1%
                if ratio < 1:
                    self.logger.verbose(f"Workflow: Text length reduced by {abs(change_pct):.1f}%")
                else:
                    self.logger.verbose(f"Workflow: Text length increased by {change_pct:.1f}%")
    
    def get_stats(self) -> Dict[str, Any]:
        """Return processing statistics."""
        stats = self.stats.copy()
        if stats['chunks_processed'] > 0:
            stats['success_rate'] = ((stats['chunks_processed'] - stats['failed_chunks']) / 
                                   stats['chunks_processed']) * 100
        else:
            stats['success_rate'] = 0.0
        return stats

