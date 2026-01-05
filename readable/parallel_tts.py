"""Parallel TTS generation for multiple chunks."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from .protocols import TTSClient
from .logger import get_logger

logger = get_logger("readable.parallel_tts")


class ParallelTTSGenerator:
    """Generate TTS audio for multiple chunks in parallel."""

    def __init__(self, client: TTSClient, max_workers: int = 4):
        """
        Initialize parallel TTS generator.

        Args:
            client: TTS client implementing TTSClient protocol
            max_workers: Maximum number of parallel workers
        """
        self.client = client
        self.max_workers = max_workers

    def generate_batch(
        self,
        text_chunks: list[str],
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        progress_callback=None
    ) -> list[Optional[bytes]]:
        """Generate audio for multiple chunks in parallel."""
        logger.info(f"Starting parallel generation for {len(text_chunks)} chunks with {self.max_workers} workers")
        logger.debug(f"Voice: {voice}, Speed: {speed}")

        results = [None] * len(text_chunks)

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                logger.debug("ThreadPoolExecutor created, submitting tasks...")

                future_to_index = {
                    executor.submit(
                        self.client.synthesize,
                        chunk,
                        voice,
                        speed
                    ): i
                    for i, chunk in enumerate(text_chunks)
                }

                logger.info(f"Submitted {len(future_to_index)} tasks to executor")

                completed = 0
                total = len(text_chunks)

                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    completed += 1

                    try:
                        audio_bytes = future.result()
                        results[index] = audio_bytes

                        if audio_bytes:
                            logger.debug(f"Chunk {index} completed: {len(audio_bytes)} bytes")
                        else:
                            logger.warning(f"Chunk {index} returned None")

                        if progress_callback:
                            progress_callback(completed, total)

                    except Exception as e:
                        logger.error(f"Error generating chunk {index}: {e}", exc_info=True)
                        results[index] = None

            logger.info(f"Parallel generation complete: {sum(1 for r in results if r)}/{len(results)} successful")

        except Exception as e:
            logger.error(f"Fatal error in parallel generation: {e}", exc_info=True)
            raise

        return results
