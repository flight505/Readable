"""Tests for refactored code - Dependency Injection and Method Extraction."""

import pytest
from typing import Optional
from readable.parallel_tts import ParallelTTSGenerator
from readable.exceptions import ValidationError, AudioGenerationError


class MockTTSClient:
    """Mock TTS client for testing ParallelTTSGenerator."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.synthesize_calls = []

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None
    ) -> Optional[bytes]:
        """Mock synthesize method."""
        self.synthesize_calls.append({
            'text': text,
            'voice': voice,
            'speed': speed
        })

        if self.should_fail:
            return None

        # Return mock WAV data (44 byte header + some data)
        return b'RIFF' + b'\x00' * 40 + text.encode()[:100]

    def get_voices(self) -> list[str]:
        """Mock get_voices method."""
        return ["af_bella", "am_adam"]


class TestParallelTTSGeneratorDependencyInjection:
    """Test that ParallelTTSGenerator properly uses injected client."""

    def test_accepts_injected_client(self):
        """Test that generator accepts and uses injected client."""
        mock_client = MockTTSClient()
        generator = ParallelTTSGenerator(client=mock_client, max_workers=2)

        assert generator.client is mock_client

    def test_uses_injected_client_for_synthesis(self):
        """Test that generator calls injected client's synthesize method."""
        mock_client = MockTTSClient()
        generator = ParallelTTSGenerator(client=mock_client, max_workers=2)

        chunks = ["Hello world", "Test chunk"]
        results = generator.generate_batch(chunks, voice="af_bella", speed=1.0)

        # Verify client was called for each chunk
        assert len(mock_client.synthesize_calls) == 2
        assert mock_client.synthesize_calls[0]['text'] == "Hello world"
        assert mock_client.synthesize_calls[1]['text'] == "Test chunk"

        # Verify all chunks succeeded
        assert len(results) == 2
        assert all(r is not None for r in results)

    def test_handles_client_failures(self):
        """Test that generator handles client failures gracefully."""
        failing_client = MockTTSClient(should_fail=True)
        generator = ParallelTTSGenerator(client=failing_client, max_workers=2)

        chunks = ["Test 1", "Test 2"]
        results = generator.generate_batch(chunks)

        # All results should be None due to failures
        assert len(results) == 2
        assert all(r is None for r in results)

    def test_parallel_execution_with_mock(self):
        """Test that parallel execution works with mock client."""
        mock_client = MockTTSClient()
        generator = ParallelTTSGenerator(client=mock_client, max_workers=4)

        # Generate 10 chunks in parallel
        chunks = [f"Chunk {i}" for i in range(10)]
        results = generator.generate_batch(chunks)

        # Verify all succeeded
        assert len(results) == 10
        assert all(r is not None for r in results)

        # Verify all chunks were processed
        assert len(mock_client.synthesize_calls) == 10

    def test_progress_callback_with_mock(self):
        """Test that progress callback works with injected client."""
        mock_client = MockTTSClient()
        generator = ParallelTTSGenerator(client=mock_client, max_workers=2)

        progress_updates = []

        def track_progress(current, total):
            progress_updates.append((current, total))

        chunks = ["A", "B", "C"]
        generator.generate_batch(chunks, progress_callback=track_progress)

        # Should have 3 progress updates
        assert len(progress_updates) == 3
        assert all(total == 3 for _, total in progress_updates)


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_validation_error_is_readable_exception(self):
        """Test that ValidationError inherits from ReadableException."""
        from readable.exceptions import ReadableException

        error = ValidationError("Test error")
        assert isinstance(error, ReadableException)
        assert isinstance(error, Exception)

    def test_audio_generation_error_is_readable_exception(self):
        """Test that AudioGenerationError inherits from ReadableException."""
        from readable.exceptions import ReadableException

        error = AudioGenerationError("Test error")
        assert isinstance(error, ReadableException)

    def test_exception_messages(self):
        """Test that exception messages are preserved."""
        validation_error = ValidationError("Invalid input")
        assert str(validation_error) == "Invalid input"

        audio_error = AudioGenerationError("Generation failed")
        assert str(audio_error) == "Generation failed"


class TestMethodExtraction:
    """Test extracted methods for better testability."""

    def test_extracted_methods_exist(self):
        """Verify that extracted methods exist on ReadableApp."""
        from readable.app_optimized import ReadableApp

        app_instance = ReadableApp()

        # Verify extracted methods exist
        assert hasattr(app_instance, '_get_clipboard_text')
        assert hasattr(app_instance, '_validate_and_chunk_text')
        assert hasattr(app_instance, '_generate_audio')
        assert hasattr(app_instance, '_start_playback')
        assert hasattr(app_instance, '_save_to_history')
        assert hasattr(app_instance, '_on_generation_progress')

    def test_validation_error_raised_on_invalid_text(self):
        """Test that ValidationError is raised for invalid text."""
        from readable.app_optimized import ReadableApp

        app_instance = ReadableApp()

        # Empty text should raise ValidationError
        with pytest.raises(ValidationError):
            app_instance._validate_and_chunk_text("")

    def test_validation_error_raised_on_too_many_chunks(self):
        """Test that ValidationError is raised when chunk limit exceeded."""
        from readable.app_optimized import ReadableApp

        app_instance = ReadableApp()

        # Create text that will generate > 100 chunks
        # Each chunk is ~750 chars, need sentences to trigger chunking
        # Create 150 sentences of ~600 chars each = 90,000 chars = ~120 chunks
        sentence = "This is a test sentence with enough words to make it reasonably long. " * 8
        large_text = (sentence + ". ") * 150  # 150 sentences

        with pytest.raises(ValidationError) as exc_info:
            app_instance._validate_and_chunk_text(large_text)

        assert "Too many chunks" in str(exc_info.value)


class TestTTSClientProtocol:
    """Test that KokoroTTSClient implements TTSClient protocol."""

    def test_kokoro_implements_protocol(self):
        """Test that KokoroTTSClient implements TTSClient protocol."""
        from readable.tts_client import KokoroTTSClient
        from readable.protocols import TTSClient

        # Create instance
        client = KokoroTTSClient()

        # Verify it has the required methods
        assert hasattr(client, 'synthesize')
        assert hasattr(client, 'get_voices')

        # Verify method signatures match protocol
        assert callable(client.synthesize)
        assert callable(client.get_voices)

    def test_mock_client_implements_protocol(self):
        """Test that MockTTSClient implements TTSClient protocol."""
        from readable.protocols import TTSClient

        mock = MockTTSClient()

        # Verify protocol methods
        assert hasattr(mock, 'synthesize')
        assert hasattr(mock, 'get_voices')

        # Test method calls
        result = mock.synthesize("test", "af_bella", 1.0)
        assert result is not None

        voices = mock.get_voices()
        assert isinstance(voices, list)


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])
