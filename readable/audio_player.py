"""Audio playback engine with queue support."""

import pygame
import tempfile
from pathlib import Path
from typing import Optional, Callable
from threading import Thread, Lock
import time
from .logger import get_logger

logger = get_logger("readable.audio_player")


class AudioPlayer:
    """Manages audio playback with queue support for chunked audio."""

    def __init__(self):
        logger.info("Initializing AudioPlayer...")
        pygame.mixer.init()
        self.queue: list[bytes] = []
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
        self._lock = Lock()
        self._temp_dir = Path(tempfile.mkdtemp())
        self._current_file: Optional[Path] = None
        self._playback_thread: Optional[Thread] = None
        self._stop_flag = False
        self.on_queue_complete: Optional[Callable] = None
        self.on_chunk_change: Optional[Callable[[int, int]]] = None
        logger.info(f"AudioPlayer initialized with temp dir: {self._temp_dir}")

    def load_queue(self, audio_chunks: list[bytes]):
        """Load audio chunks into playback queue."""
        logger.info(f"Loading {len(audio_chunks)} chunks into queue")
        total_size = sum(len(chunk) for chunk in audio_chunks)
        logger.info(f"Total queue size: {total_size / 1024 / 1024:.1f} MB")

        # Stop BEFORE acquiring lock to avoid deadlock
        self.stop()

        with self._lock:
            self.queue = audio_chunks
            self.current_index = 0
            self.is_playing = False
            self.is_paused = False

        logger.info("Queue loaded successfully")

    def play(self):
        """Start or resume playback."""
        logger.info("Play requested")

        with self._lock:
            if not self.queue:
                logger.warning("Cannot play - queue is empty")
                return

            if self.is_paused:
                logger.info("Resuming from pause")
                pygame.mixer.music.unpause()
                self.is_paused = False
                self.is_playing = True
                return

            if not self.is_playing:
                logger.info("Starting new playback")
                self.is_playing = True
                self._stop_flag = False
                self._playback_thread = Thread(target=self._playback_loop, daemon=True)
                self._playback_thread.start()
                logger.info("Playback thread started")

    def pause(self):
        """Pause playback."""
        logger.info("Pause requested")
        with self._lock:
            if self.is_playing and not self.is_paused:
                logger.debug("Pausing playback...")
                pygame.mixer.music.pause()
                self.is_paused = True
                logger.info("Playback paused")
            else:
                logger.warning(f"Cannot pause - is_playing={self.is_playing}, is_paused={self.is_paused}")

    def stop(self):
        """Stop playback completely."""
        logger.debug("Stop requested")
        with self._lock:
            self._stop_flag = True
            self.is_playing = False
            self.is_paused = False
            pygame.mixer.music.stop()
        logger.debug("Stop complete")

    def skip(self):
        """Skip to next chunk."""
        with self._lock:
            if self.current_index < len(self.queue) - 1:
                self.current_index += 1
                if self.is_playing:
                    pygame.mixer.music.stop()
                    self._play_current_chunk()
            else:
                self.stop()

    def _playback_loop(self):
        """Main playback loop that processes queue."""
        logger.info(f"Playback loop started - {len(self.queue)} chunks in queue")

        while not self._stop_flag and self.current_index < len(self.queue):
            logger.debug(f"Playing chunk {self.current_index + 1}/{len(self.queue)}")
            self._play_current_chunk()

            logger.debug(f"Waiting for chunk {self.current_index + 1} to finish...")
            # Wait while music is playing OR paused (don't skip when paused!)
            while (pygame.mixer.music.get_busy() or self.is_paused) and not self._stop_flag:
                time.sleep(0.1)

            if self._stop_flag:
                logger.info("Playback stopped by user")
                break

            with self._lock:
                self.current_index += 1

        logger.info("Playback loop ended")

        with self._lock:
            self.is_playing = False
            if self.on_queue_complete and not self._stop_flag:
                logger.info("Queue complete callback")
                self.on_queue_complete()

    def _play_current_chunk(self):
        """Play the current chunk from queue."""
        if self.current_index >= len(self.queue):
            logger.warning(f"Attempted to play chunk {self.current_index} but queue only has {len(self.queue)} chunks")
            return

        audio_bytes = self.queue[self.current_index]
        logger.debug(f"Loading chunk {self.current_index}: {len(audio_bytes)} bytes")

        self._current_file = self._temp_dir / f"chunk_{self.current_index}.wav"
        self._current_file.write_bytes(audio_bytes)
        logger.debug(f"Wrote to temp file: {self._current_file}")

        pygame.mixer.music.load(str(self._current_file))
        pygame.mixer.music.play()
        logger.debug(f"Chunk {self.current_index} started playing")

        if self.on_chunk_change:
            self.on_chunk_change(self.current_index + 1, len(self.queue))

    def get_status(self) -> dict:
        """Get current playback status."""
        with self._lock:
            return {
                "is_playing": self.is_playing,
                "is_paused": self.is_paused,
                "current_chunk": self.current_index + 1 if self.queue else 0,
                "total_chunks": len(self.queue),
                "has_queue": bool(self.queue)
            }

    def cleanup(self):
        """Clean up temporary files."""
        self.stop()
        try:
            import shutil
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        except Exception:
            pass
