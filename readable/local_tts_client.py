"""Local TTS client using Kokoro MLX model."""

import io
import sys
from pathlib import Path
from typing import Optional

from .cache import AudioCache
from .config import Config
from .logger import get_logger

logger = get_logger("readable.local_tts_client")


class LocalTTSClient:
    """TTS client using local Kokoro MLX model."""

    # Default voices available in Kokoro MLX
    AVAILABLE_VOICES = [
        "af_bella", "af_sarah", "am_adam", "am_michael",
        "bf_emma", "bf_isabella", "bm_george", "bm_lewis"
    ]

    def __init__(
        self,
        model_path: str = None,
        default_voice: str = None,
        default_speed: float = None,
        enable_cache: bool = True,
        config: Config = None
    ):
        """
        Initialize local TTS client.

        Args:
            model_path: Path to kokoro-tts-mlx directory
            default_voice: Default voice ID
            default_speed: Default playback speed
            enable_cache: Whether to enable audio caching
            config: Configuration object
        """
        self.config = config or Config()

        self.model_path = model_path or self.config.get(
            "local_model_path",
            "/Users/jesper/Projects/Dev_projects/sonic-workspace/models/kokoro-tts-mlx"
        )
        self.default_voice = default_voice or self.config.default_voice
        self.default_speed = default_speed or self.config.default_speed
        self.cache = AudioCache() if enable_cache else None

        # Lazy-loaded model components
        self._tts = None
        self._model_loaded = False

        logger.info(f"Local TTS client initialized (model path: {self.model_path})")

    def _ensure_model_loaded(self) -> bool:
        """Lazy load the Kokoro MLX model on first use."""
        if self._model_loaded:
            return True

        try:
            # Add kokoro-tts-mlx src to path if needed
            kokoro_src = Path(self.model_path) / "src"
            if kokoro_src.exists() and str(kokoro_src) not in sys.path:
                sys.path.insert(0, str(kokoro_src))
                logger.debug(f"Added {kokoro_src} to Python path")

            # Import and initialize KokoroTTS
            from kokoro import KokoroTTS

            logger.info("Loading Kokoro MLX model (this may take a moment)...")
            self._tts = KokoroTTS()
            self._model_loaded = True
            logger.info("Kokoro MLX model loaded successfully")
            return True

        except ImportError as e:
            logger.error(f"Failed to import KokoroTTS: {e}")
            logger.error(f"Ensure kokoro-tts-mlx is installed at: {self.model_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to load Kokoro MLX model: {e}", exc_info=True)
            return False

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None
    ) -> Optional[bytes]:
        """
        Synthesize text to speech using local MLX model.

        Args:
            text: Text to synthesize
            voice: Voice ID to use
            speed: Playback speed multiplier

        Returns:
            WAV audio bytes, or None if synthesis failed
        """
        if not text.strip():
            logger.warning("Empty text provided to synthesize")
            return None

        voice = voice or self.default_voice
        speed = speed or self.default_speed

        logger.debug(f"Synthesizing {len(text)} chars (voice={voice}, speed={speed})")

        # Check cache first
        if self.cache:
            cached_audio = self.cache.get(text, voice, speed)
            if cached_audio:
                logger.debug(f"Cache HIT: {len(cached_audio)} bytes")
                return cached_audio
            logger.debug("Cache MISS")

        # Ensure model is loaded
        if not self._ensure_model_loaded():
            logger.error("Cannot synthesize: model not loaded")
            return None

        try:
            # Generate audio using local model
            logger.debug(f"Generating audio with local MLX model...")
            result = self._tts.synthesize(text, voice=voice, speed=speed)

            # Convert mx.array to WAV bytes
            audio_bytes = self._convert_to_wav(result.audio, self._tts.sample_rate)

            if audio_bytes is None:
                logger.error("Failed to convert audio to WAV format")
                return None

            logger.debug(f"Generated {len(audio_bytes)} bytes of audio")

            # Save to cache
            if self.cache:
                self.cache.put(text, voice, speed, audio_bytes)
                logger.debug("Saved to cache")

            return audio_bytes

        except Exception as e:
            logger.error(f"Local TTS synthesis error: {e}", exc_info=True)
            return None

    def _convert_to_wav(self, audio_array, sample_rate: int) -> Optional[bytes]:
        """
        Convert mx.array audio to WAV bytes.

        Args:
            audio_array: MLX array containing audio samples
            sample_rate: Audio sample rate (typically 24000 for Kokoro)

        Returns:
            WAV audio bytes, or None if conversion failed
        """
        try:
            import numpy as np
            import soundfile as sf

            # Convert mlx array to numpy
            # The audio_array from Kokoro is typically already float32
            if hasattr(audio_array, 'tolist'):
                # mlx array
                audio_np = np.array(audio_array.tolist(), dtype=np.float32)
            else:
                # Already numpy or similar
                audio_np = np.asarray(audio_array, dtype=np.float32)

            # Ensure audio is in valid range [-1, 1]
            if audio_np.max() > 1.0 or audio_np.min() < -1.0:
                audio_np = np.clip(audio_np, -1.0, 1.0)

            # Write to in-memory WAV buffer
            buffer = io.BytesIO()
            sf.write(buffer, audio_np, sample_rate, format='WAV', subtype='PCM_16')
            buffer.seek(0)

            return buffer.read()

        except ImportError as e:
            logger.error(f"Missing dependency for audio conversion: {e}")
            logger.error("Install with: uv add soundfile numpy")
            return None
        except Exception as e:
            logger.error(f"Failed to convert audio to WAV: {e}", exc_info=True)
            return None

    def get_voices(self) -> list[str]:
        """Get list of available voice IDs."""
        # If model is loaded, try to get voices from it
        if self._model_loaded and self._tts and hasattr(self._tts, 'list_voices'):
            try:
                return self._tts.list_voices()
            except Exception as e:
                logger.warning(f"Failed to get voices from model: {e}")

        # Fall back to known voices
        return self.AVAILABLE_VOICES.copy()

    def is_available(self) -> bool:
        """Check if local TTS is available (model path exists)."""
        model_dir = Path(self.model_path)
        return model_dir.exists() and (model_dir / "src").exists()
