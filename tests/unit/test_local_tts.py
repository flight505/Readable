"""Tests for local_tts_client module."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from readable.local_tts_client import LocalTTSClient
from readable.config import Config

# Check for optional dependencies
try:
    import numpy as np
    import soundfile
    HAS_AUDIO_DEPS = True
except ImportError:
    HAS_AUDIO_DEPS = False


class TestLocalTTSClientInit:
    """Tests for LocalTTSClient initialization."""

    def test_init_with_defaults(self):
        """Client initializes with default values."""
        with patch.object(Config, '_load', return_value=Config.DEFAULTS.copy()):
            client = LocalTTSClient()
            assert client.default_voice == "af_bella"
            assert client.default_speed == 1.0
            assert client._tts is None
            assert client._model_loaded is False

    def test_init_with_custom_config(self):
        """Client uses custom configuration."""
        config = Mock(spec=Config)
        config.get.return_value = "/custom/path"
        config.default_voice = "am_adam"
        config.default_speed = 1.25

        client = LocalTTSClient(config=config)
        assert client.default_voice == "am_adam"
        assert client.default_speed == 1.25

    def test_init_with_explicit_params(self):
        """Explicit parameters override config."""
        with patch.object(Config, '_load', return_value=Config.DEFAULTS.copy()):
            client = LocalTTSClient(
                model_path="/explicit/path",
                default_voice="bf_emma",
                default_speed=0.75
            )
            assert client.model_path == "/explicit/path"
            assert client.default_voice == "bf_emma"
            assert client.default_speed == 0.75


class TestLocalTTSClientAvailability:
    """Tests for is_available method."""

    def test_is_available_when_path_exists(self, tmp_path):
        """Returns True when model path and src exist."""
        model_path = tmp_path / "kokoro-tts-mlx"
        model_path.mkdir()
        (model_path / "src").mkdir()

        with patch.object(Config, '_load', return_value=Config.DEFAULTS.copy()):
            client = LocalTTSClient(model_path=str(model_path))
            assert client.is_available() is True

    def test_is_not_available_when_path_missing(self, tmp_path):
        """Returns False when model path doesn't exist."""
        model_path = tmp_path / "nonexistent"

        with patch.object(Config, '_load', return_value=Config.DEFAULTS.copy()):
            client = LocalTTSClient(model_path=str(model_path))
            assert client.is_available() is False

    def test_is_not_available_when_src_missing(self, tmp_path):
        """Returns False when src directory doesn't exist."""
        model_path = tmp_path / "kokoro-tts-mlx"
        model_path.mkdir()  # No src subdirectory

        with patch.object(Config, '_load', return_value=Config.DEFAULTS.copy()):
            client = LocalTTSClient(model_path=str(model_path))
            assert client.is_available() is False


class TestLocalTTSClientGetVoices:
    """Tests for get_voices method."""

    def test_get_voices_returns_available_voices(self):
        """Returns list of available voices."""
        with patch.object(Config, '_load', return_value=Config.DEFAULTS.copy()):
            client = LocalTTSClient()
            voices = client.get_voices()
            assert isinstance(voices, list)
            assert "af_bella" in voices
            assert "am_adam" in voices
            assert len(voices) == 8


class TestLocalTTSClientSynthesize:
    """Tests for synthesize method."""

    def test_synthesize_empty_text_returns_none(self):
        """Empty text returns None."""
        with patch.object(Config, '_load', return_value=Config.DEFAULTS.copy()):
            client = LocalTTSClient()
            assert client.synthesize("") is None
            assert client.synthesize("   ") is None

    def test_synthesize_uses_cache_on_hit(self):
        """Cache hit returns cached audio."""
        mock_cache = Mock()
        mock_cache.get.return_value = b"cached_audio_data"

        with patch.object(Config, '_load', return_value=Config.DEFAULTS.copy()):
            client = LocalTTSClient()
            client.cache = mock_cache

            result = client.synthesize("Hello world")
            assert result == b"cached_audio_data"
            mock_cache.get.assert_called_once_with("Hello world", "af_bella", 1.0)

    def test_synthesize_returns_none_when_model_unavailable(self):
        """Returns None when model can't be loaded."""
        with patch.object(Config, '_load', return_value=Config.DEFAULTS.copy()):
            client = LocalTTSClient(model_path="/nonexistent/path")
            client.cache = None  # Disable cache

            result = client.synthesize("Hello world")
            assert result is None

    def test_synthesize_uses_voice_and_speed_params(self):
        """Uses provided voice and speed parameters."""
        mock_cache = Mock()
        mock_cache.get.return_value = b"audio"

        with patch.object(Config, '_load', return_value=Config.DEFAULTS.copy()):
            client = LocalTTSClient()
            client.cache = mock_cache

            client.synthesize("Hello", voice="am_adam", speed=1.5)
            mock_cache.get.assert_called_once_with("Hello", "am_adam", 1.5)


@pytest.mark.skipif(not HAS_AUDIO_DEPS, reason="numpy/soundfile not installed")
class TestLocalTTSClientConvertToWav:
    """Tests for _convert_to_wav method."""

    def test_convert_numpy_array_to_wav(self):
        """Converts numpy array to WAV bytes."""
        import numpy as np

        with patch.object(Config, '_load', return_value=Config.DEFAULTS.copy()):
            client = LocalTTSClient()

            # Create a simple audio array
            sample_rate = 24000
            duration = 0.1  # 100ms
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_array = (np.sin(2 * np.pi * 440 * t) * 0.5).astype(np.float32)

            result = client._convert_to_wav(audio_array, sample_rate)

            assert result is not None
            assert len(result) > 44  # WAV header is 44 bytes
            assert result[:4] == b'RIFF'  # WAV magic bytes

    def test_convert_clips_out_of_range_audio(self):
        """Audio outside [-1, 1] is clipped."""
        import numpy as np

        with patch.object(Config, '_load', return_value=Config.DEFAULTS.copy()):
            client = LocalTTSClient()

            # Audio array with values outside valid range
            audio_array = np.array([2.0, -2.0, 0.5], dtype=np.float32)

            result = client._convert_to_wav(audio_array, 24000)

            assert result is not None
            # The conversion should succeed without error

    def test_convert_handles_mlx_like_array(self):
        """Handles arrays with tolist method (like mlx arrays)."""
        import numpy as np

        with patch.object(Config, '_load', return_value=Config.DEFAULTS.copy()):
            client = LocalTTSClient()

            # Create a mock MLX-like array
            class MockMLXArray:
                def tolist(self):
                    return [0.1, 0.2, -0.1, 0.0]

            mock_array = MockMLXArray()
            result = client._convert_to_wav(mock_array, 24000)

            assert result is not None
            assert result[:4] == b'RIFF'


@pytest.mark.skipif(not HAS_AUDIO_DEPS, reason="numpy/soundfile not installed")
class TestLocalTTSClientIntegration:
    """Integration tests for LocalTTSClient with mocked model."""

    def test_full_synthesis_flow_with_mocked_model(self):
        """Test complete synthesis flow with mocked KokoroTTS."""
        import numpy as np

        # Create mock TTS model
        mock_tts = Mock()
        mock_audio = np.sin(np.linspace(0, 1, 2400)).astype(np.float32)
        mock_tts.synthesize.return_value = (mock_audio, 24000)

        with patch.object(Config, '_load', return_value=Config.DEFAULTS.copy()):
            client = LocalTTSClient()
            client._tts = mock_tts
            client._model_loaded = True
            client.cache = None  # Disable cache

            result = client.synthesize("Hello world", voice="af_bella", speed=1.0)

            assert result is not None
            assert len(result) > 44
            mock_tts.synthesize.assert_called_once_with(
                "Hello world",
                voice="af_bella",
                speed=1.0
            )

    def test_synthesis_saves_to_cache(self):
        """Synthesized audio is saved to cache."""
        import numpy as np

        mock_tts = Mock()
        mock_audio = np.sin(np.linspace(0, 1, 2400)).astype(np.float32)
        mock_tts.synthesize.return_value = (mock_audio, 24000)

        mock_cache = Mock()
        mock_cache.get.return_value = None  # Cache miss

        with patch.object(Config, '_load', return_value=Config.DEFAULTS.copy()):
            client = LocalTTSClient()
            client._tts = mock_tts
            client._model_loaded = True
            client.cache = mock_cache

            client.synthesize("Hello", voice="af_bella", speed=1.0)

            mock_cache.put.assert_called_once()
            args = mock_cache.put.call_args[0]
            assert args[0] == "Hello"
            assert args[1] == "af_bella"
            assert args[2] == 1.0
            assert isinstance(args[3], bytes)
