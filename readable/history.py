"""Reading history tracker for Readable app."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from threading import Lock
from .logger import get_logger

logger = get_logger("readable.history")


class ReadingHistory:
    """Track reading sessions for replay."""

    def __init__(self, history_dir: Optional[Path] = None):
        self.history_dir = history_dir or Path.home() / ".readable"
        self.history_dir.mkdir(parents=True, exist_ok=True)

        self.history_file = self.history_dir / "history.json"
        self._lock = Lock()
        self.sessions = self._load_history()
        logger.info(f"History loaded: {len(self.sessions)} sessions")

    def _load_history(self) -> list:
        """Load reading history from disk."""
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text())
            except Exception as e:
                logger.error(f"Failed to load history: {e}")
                return []
        return []

    def _save_history(self):
        """Save reading history to disk. Must be called with self._lock held."""
        try:
            # Keep only last 50 sessions
            self.sessions = self.sessions[-50:]
            self.history_file.write_text(json.dumps(self.sessions, indent=2))
            logger.debug("History saved")
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def add_session(
        self,
        text: str,
        chunks: List[str],
        voice: str,
        speed: float,
        chunk_count: int
    ):
        """Record a new reading session."""
        with self._lock:
            session = {
                "timestamp": datetime.now().isoformat(),
                "preview": text[:100] + "..." if len(text) > 100 else text,
                "full_text": text,  # Store full text for replay
                "chunks": chunks,  # Store all chunks
                "voice": voice,
                "speed": speed,
                "chunk_count": chunk_count,
                "text_length": len(text),
                "duration_estimate": len(text) / 11.8  # ~11.8 chars/second
            }

            self.sessions.append(session)
            self._save_history()
            logger.info(f"Session added: {session['preview'][:50]}")

    def get_recent(self, limit: int = 10) -> list:
        """Get most recent sessions."""
        with self._lock:
            return list(reversed(self.sessions[-limit:]))

    def get_session(self, index: int) -> Optional[dict]:
        """Get a specific session by index (from most recent)."""
        recent = self.get_recent(50)
        if 0 <= index < len(recent):
            return recent[index]
        return None

    def clear(self):
        """Clear all history."""
        with self._lock:
            self.sessions = []
            self._save_history()
            logger.info("History cleared")

    def format_session_preview(self, session: dict, max_length: int = 50) -> str:
        """Format a session for menu display."""
        preview = session["preview"][:max_length]

        # Time ago
        try:
            timestamp = datetime.fromisoformat(session["timestamp"])
            now = datetime.now()
            delta = now - timestamp

            if delta.days > 0:
                time_ago = f"{delta.days}d ago"
            elif delta.seconds >= 3600:
                time_ago = f"{delta.seconds // 3600}h ago"
            elif delta.seconds >= 60:
                time_ago = f"{delta.seconds // 60}m ago"
            else:
                time_ago = "just now"
        except:
            time_ago = "recently"

        # Duration estimate
        duration_min = int(session["duration_estimate"] / 60)

        return f"{preview} ({duration_min}m, {time_ago})"
