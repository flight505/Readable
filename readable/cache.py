"""Audio cache for TTS results."""

import hashlib
import json
from pathlib import Path
from typing import Optional
from threading import Lock
from .logger import get_logger

logger = get_logger("readable.cache")


class AudioCache:
    """LRU cache for TTS audio with disk persistence."""

    def __init__(self, cache_dir: Optional[Path] = None, max_size_mb: int = 100):
        self.cache_dir = cache_dir or Path.home() / ".cache" / "readable"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = self.cache_dir / "index.json"
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._lock = Lock()

        self.index = self._load_index()

    def _load_index(self) -> dict:
        """Load cache index from disk."""
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text())
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse cache index (corrupted): {e}")
                return {}
            except OSError as e:
                logger.error(f"Failed to read cache index file: {e}")
                return {}
        return {}

    def _save_index(self):
        """Save cache index to disk."""
        try:
            self.index_file.write_text(json.dumps(self.index, indent=2))
        except OSError as e:
            logger.error(f"Failed to write cache index: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error saving cache index: {e}")

    def _get_cache_key(self, text: str, voice: str, speed: float) -> str:
        """Generate cache key from text and parameters."""
        content = f"{text}|{voice}|{speed}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, text: str, voice: str, speed: float) -> Optional[bytes]:
        """Retrieve audio from cache (thread-safe)."""
        cache_key = self._get_cache_key(text, voice, speed)

        with self._lock:
            if cache_key not in self.index:
                return None

            cache_file = self.cache_dir / f"{cache_key}.wav"

            if not cache_file.exists():
                del self.index[cache_key]
                self._save_index()
                return None

            try:
                self.index[cache_key]["hits"] += 1
                self._save_index()
            except Exception as e:
                logger.warning(f"Failed to update hit count: {e}")

        try:
            return cache_file.read_bytes()
        except OSError as e:
            logger.error(f"Failed to read cache file {cache_file}: {e}")
            return None

    def put(self, text: str, voice: str, speed: float, audio_bytes: bytes):
        """Store audio in cache (thread-safe)."""
        cache_key = self._get_cache_key(text, voice, speed)
        cache_file = self.cache_dir / f"{cache_key}.wav"

        with self._lock:
            self._evict_if_needed(len(audio_bytes))

            try:
                cache_file.write_bytes(audio_bytes)

                self.index[cache_key] = {
                    "text_preview": text[:50] + "..." if len(text) > 50 else text,
                    "voice": voice,
                    "speed": speed,
                    "size": len(audio_bytes),
                    "hits": 0
                }

                self._save_index()
            except OSError as e:
                logger.error(f"Failed to write cache file {cache_file}: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error caching audio: {e}")

    def _evict_if_needed(self, new_item_size: int):
        """Evict least-used items if cache is too large (must be called with lock held)."""
        total_size = sum(item["size"] for item in self.index.values())

        if total_size + new_item_size <= self.max_size_bytes:
            return

        sorted_items = sorted(
            self.index.items(),
            key=lambda x: x[1]["hits"]
        )

        evicted_count = 0
        for cache_key, _ in sorted_items:
            cache_file = self.cache_dir / f"{cache_key}.wav"

            try:
                if cache_file.exists():
                    cache_file.unlink()
                del self.index[cache_key]
                evicted_count += 1
            except OSError as e:
                logger.warning(f"Failed to evict cache file {cache_file}: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error during eviction: {e}")

            total_size = sum(item["size"] for item in self.index.values())
            if total_size + new_item_size <= self.max_size_bytes:
                break

        if evicted_count > 0:
            logger.info(f"Evicted {evicted_count} cache entries to free space")
        self._save_index()

    def get_stats(self) -> dict:
        """Get cache statistics (thread-safe)."""
        with self._lock:
            total_size = sum(item["size"] for item in self.index.values())
            total_hits = sum(item["hits"] for item in self.index.values())

            return {
                "entries": len(self.index),
                "total_size_mb": total_size / 1024 / 1024,
                "total_hits": total_hits,
                "hit_rate": total_hits / len(self.index) if self.index else 0
            }

    def clear(self):
        """Clear entire cache (thread-safe)."""
        with self._lock:
            cleared_count = 0
            for cache_key in list(self.index.keys()):
                cache_file = self.cache_dir / f"{cache_key}.wav"
                try:
                    if cache_file.exists():
                        cache_file.unlink()
                        cleared_count += 1
                except OSError as e:
                    logger.warning(f"Failed to delete cache file {cache_file}: {e}")

            self.index = {}
            self._save_index()
            logger.info(f"Cache cleared: {cleared_count} files deleted")
