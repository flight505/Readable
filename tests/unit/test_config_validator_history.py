"""Test suite for critical fixes: Config, Validator, and History thread safety."""

import pytest
import json
import os
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from readable.config import Config
from readable.validator import InputValidator
from readable.history import ReadingHistory


class TestConfig:
    """Test configuration management (Fix 1)."""

    def test_default_config_values(self):
        """Test that default configuration values are loaded."""
        config = Config()

        assert config.tts_url == "http://100.71.118.55:8001"
        assert config.max_text_length == 1_000_000
        assert config.max_chunks == 100
        assert config.max_workers == 4
        assert config.default_voice == "af_bella"
        assert config.default_speed == 1.0

    def test_config_file_loading(self):
        """Test loading configuration from file."""
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"

            # Create custom config
            custom_config = {
                "tts_url": "http://localhost:9999",
                "max_text_length": 500_000,
                "max_workers": 8,
                "default_voice": "am_adam"
            }
            config_file.write_text(json.dumps(custom_config))

            # Load config
            config = Config(config_file=config_file)

            assert config.tts_url == "http://localhost:9999"
            assert config.max_text_length == 500_000
            assert config.max_workers == 8
            assert config.default_voice == "am_adam"
            # Defaults should still apply for unspecified values
            assert config.max_chunks == 100

    def test_env_variable_override(self):
        """Test that environment variables override config file."""
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"

            # Create config file
            file_config = {"tts_url": "http://localhost:8001"}
            config_file.write_text(json.dumps(file_config))

            # Set environment variable
            os.environ["KOKORO_TTS_URL"] = "http://env-override:7777"
            os.environ["READABLE_MAX_WORKERS"] = "12"

            try:
                config = Config(config_file=config_file)

                # Env var should override file
                assert config.tts_url == "http://env-override:7777"
                assert config.max_workers == 12
            finally:
                # Cleanup env vars
                os.environ.pop("KOKORO_TTS_URL", None)
                os.environ.pop("READABLE_MAX_WORKERS", None)

    def test_invalid_config_file_fallback(self):
        """Test that invalid config file falls back to defaults."""
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"

            # Create invalid JSON
            config_file.write_text("{ invalid json }")

            config = Config(config_file=config_file)

            # Should fall back to defaults
            assert config.tts_url == "http://100.71.118.55:8001"
            assert config.max_workers == 4

    def test_config_save(self):
        """Test saving configuration to file."""
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"

            config = Config(config_file=config_file)
            config.data["tts_url"] = "http://saved:8888"
            config.save()

            # Verify file was created
            assert config_file.exists()

            # Load and verify
            saved_data = json.loads(config_file.read_text())
            assert saved_data["tts_url"] == "http://saved:8888"

    def test_create_default_config(self):
        """Test creating default configuration file."""
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"

            config = Config(config_file=config_file)
            config.create_default_config()

            assert config_file.exists()

            # Verify defaults were saved
            saved_data = json.loads(config_file.read_text())
            assert saved_data["tts_url"] == "http://100.71.118.55:8001"
            assert saved_data["max_workers"] == 4


class TestInputValidator:
    """Test input validation (Fix 2)."""

    def setup_method(self):
        """Set up test validator."""
        self.validator = InputValidator()

    def test_valid_text(self):
        """Test validation of valid text."""
        text = "This is a valid test string."
        is_valid, error = self.validator.validate_text(text)

        assert is_valid is True
        assert error == ""

    def test_empty_text(self):
        """Test validation rejects empty text."""
        is_valid, error = self.validator.validate_text("")
        assert is_valid is False
        assert "empty" in error.lower()

        is_valid, error = self.validator.validate_text("   ")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_invalid_type(self):
        """Test validation rejects non-string input."""
        is_valid, error = self.validator.validate_text(123)
        assert is_valid is False
        assert "Invalid input type" in error

        is_valid, error = self.validator.validate_text(None)
        assert is_valid is False
        assert "Invalid input type" in error

    def test_text_length_limit(self):
        """Test validation enforces maximum text length."""
        # Create text just under the limit
        max_length = self.validator.config.max_text_length
        valid_text = "a" * (max_length - 1)
        is_valid, error = self.validator.validate_text(valid_text)
        assert is_valid is True

        # Create text over the limit
        invalid_text = "a" * (max_length + 1)
        is_valid, error = self.validator.validate_text(invalid_text)
        assert is_valid is False
        assert "too long" in error.lower()
        assert "MB" in error

    def test_null_byte_rejection(self):
        """Test validation rejects binary data with null bytes."""
        text_with_nulls = "Hello\x00World"
        is_valid, error = self.validator.validate_text(text_with_nulls)

        assert is_valid is False
        assert "binary" in error.lower()

    def test_valid_chunks(self):
        """Test validation of valid chunks."""
        chunks = ["chunk 1", "chunk 2", "chunk 3"]
        is_valid, error = self.validator.validate_chunks(chunks)

        assert is_valid is True
        assert error == ""

    def test_empty_chunks_list(self):
        """Test validation rejects empty chunks list."""
        is_valid, error = self.validator.validate_chunks([])

        assert is_valid is False
        assert "No chunks" in error

    def test_invalid_chunks_type(self):
        """Test validation rejects non-list chunks."""
        is_valid, error = self.validator.validate_chunks("not a list")

        assert is_valid is False
        assert "Invalid chunks type" in error

    def test_chunk_count_limit(self):
        """Test validation enforces maximum chunk count."""
        max_chunks = self.validator.config.max_chunks

        # Valid chunk count
        valid_chunks = ["chunk"] * (max_chunks - 1)
        is_valid, error = self.validator.validate_chunks(valid_chunks)
        assert is_valid is True

        # Exceeds limit
        invalid_chunks = ["chunk"] * (max_chunks + 1)
        is_valid, error = self.validator.validate_chunks(invalid_chunks)
        assert is_valid is False
        assert "Too many chunks" in error
        assert str(max_chunks) in error

    def test_sanitize_text(self):
        """Test text sanitization removes null bytes."""
        dirty_text = "Hello\x00World\x00!"
        clean_text = self.validator.sanitize_text(dirty_text)

        assert "\x00" not in clean_text
        assert clean_text == "HelloWorld!"

    def test_custom_config_limits(self):
        """Test validator respects custom config limits."""
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            custom_config = {
                "max_text_length": 100,
                "max_chunks": 5
            }
            config_file.write_text(json.dumps(custom_config))

            config = Config(config_file=config_file)
            validator = InputValidator(config=config)

            # Text over custom limit should fail
            long_text = "a" * 101
            is_valid, error = validator.validate_text(long_text)
            assert is_valid is False

            # Chunks over custom limit should fail
            many_chunks = ["chunk"] * 6
            is_valid, error = validator.validate_chunks(many_chunks)
            assert is_valid is False


class TestHistoryThreadSafety:
    """Test history thread safety (Fix 3)."""

    def test_history_has_lock(self):
        """Test that history has threading lock."""
        with TemporaryDirectory() as tmpdir:
            history = ReadingHistory(history_dir=Path(tmpdir))

            assert hasattr(history, '_lock')
            assert hasattr(history._lock, 'acquire')
            assert hasattr(history._lock, 'release')

    def test_concurrent_add_sessions(self):
        """Test concurrent session additions don't corrupt data."""
        with TemporaryDirectory() as tmpdir:
            history = ReadingHistory(history_dir=Path(tmpdir))
            errors = []
            session_count = 0
            lock = threading.Lock()

            def worker(worker_id: int):
                """Worker that adds sessions to history."""
                nonlocal session_count
                try:
                    for i in range(10):
                        text = f"Worker {worker_id} - Session {i}"
                        chunks = [f"chunk_{j}" for j in range(3)]

                        history.add_session(
                            text=text,
                            chunks=chunks,
                            voice="af_bella",
                            speed=1.0,
                            chunk_count=len(chunks)
                        )

                        with lock:
                            session_count += 1

                        time.sleep(0.001)  # Small delay
                except Exception as e:
                    errors.append(f"Worker {worker_id}: {e}")

            # Run 5 workers concurrently
            workers = []
            for i in range(5):
                t = threading.Thread(target=worker, args=(i,))
                t.start()
                workers.append(t)

            # Wait for completion
            for t in workers:
                t.join()

            # Verify no errors occurred
            assert len(errors) == 0, f"Thread safety errors: {errors}"

            # Verify all sessions were added
            # Note: History keeps only last 50 sessions
            assert session_count == 50  # 5 workers × 10 sessions
            assert len(history.sessions) <= 50

    def test_concurrent_read_write(self):
        """Test concurrent reads and writes don't cause issues."""
        with TemporaryDirectory() as tmpdir:
            history = ReadingHistory(history_dir=Path(tmpdir))
            errors = []

            # Pre-populate with some sessions
            for i in range(10):
                history.add_session(
                    text=f"Initial session {i}",
                    chunks=[f"chunk_{j}" for j in range(3)],
                    voice="af_bella",
                    speed=1.0,
                    chunk_count=3
                )

            def writer(worker_id: int):
                """Worker that writes to history."""
                try:
                    for i in range(5):
                        history.add_session(
                            text=f"Writer {worker_id} - {i}",
                            chunks=[f"chunk_{j}" for j in range(2)],
                            voice="af_bella",
                            speed=1.0,
                            chunk_count=2
                        )
                        time.sleep(0.001)
                except Exception as e:
                    errors.append(f"Writer {worker_id}: {e}")

            def reader(worker_id: int):
                """Worker that reads from history."""
                try:
                    for i in range(10):
                        recent = history.get_recent(limit=5)
                        assert isinstance(recent, list)
                        time.sleep(0.001)
                except Exception as e:
                    errors.append(f"Reader {worker_id}: {e}")

            # Run 3 writers and 3 readers concurrently
            threads = []

            for i in range(3):
                t = threading.Thread(target=writer, args=(i,))
                t.start()
                threads.append(t)

            for i in range(3):
                t = threading.Thread(target=reader, args=(i,))
                t.start()
                threads.append(t)

            # Wait for completion
            for t in threads:
                t.join()

            # Verify no errors
            assert len(errors) == 0, f"Concurrent access errors: {errors}"

    def test_concurrent_clear(self):
        """Test clearing history doesn't cause race conditions."""
        with TemporaryDirectory() as tmpdir:
            history = ReadingHistory(history_dir=Path(tmpdir))
            errors = []

            # Pre-populate
            for i in range(20):
                history.add_session(
                    text=f"Session {i}",
                    chunks=[f"chunk_{j}" for j in range(2)],
                    voice="af_bella",
                    speed=1.0,
                    chunk_count=2
                )

            def clear_worker():
                """Worker that clears history."""
                try:
                    time.sleep(0.005)
                    history.clear()
                except Exception as e:
                    errors.append(f"Clear worker: {e}")

            def read_worker(worker_id: int):
                """Worker that reads history."""
                try:
                    for i in range(20):
                        history.get_recent(limit=10)
                        time.sleep(0.001)
                except Exception as e:
                    errors.append(f"Read worker {worker_id}: {e}")

            # Run clear and multiple readers
            threads = []

            clear_thread = threading.Thread(target=clear_worker)
            clear_thread.start()
            threads.append(clear_thread)

            for i in range(3):
                t = threading.Thread(target=read_worker, args=(i,))
                t.start()
                threads.append(t)

            # Wait for completion
            for t in threads:
                t.join()

            # Verify no errors
            assert len(errors) == 0, f"Clear race condition errors: {errors}"

            # History should be empty after clear
            assert len(history.sessions) == 0

    def test_history_file_persistence(self):
        """Test history file is saved correctly with thread safety."""
        with TemporaryDirectory() as tmpdir:
            history_dir = Path(tmpdir)
            history_file = history_dir / "history.json"

            # Create history and add sessions
            history = ReadingHistory(history_dir=history_dir)
            history.add_session(
                text="Test session",
                chunks=["chunk1", "chunk2"],
                voice="af_bella",
                speed=1.0,
                chunk_count=2
            )

            # Verify file was created
            assert history_file.exists()

            # Verify file content
            saved_data = json.loads(history_file.read_text())
            assert len(saved_data) == 1
            assert saved_data[0]["full_text"] == "Test session"
            assert saved_data[0]["voice"] == "af_bella"


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])
