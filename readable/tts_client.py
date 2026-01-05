"""Client for Kokoro TTS API."""

import base64
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path
from typing import Optional
from .cache import AudioCache
from .config import Config
from .logger import get_logger

logger = get_logger("readable.tts_client")


class KokoroTTSClient:
    """Client for interacting with Kokoro TTS API with caching."""

    def __init__(
        self,
        base_url: str = None,
        default_voice: str = None,
        default_speed: float = None,
        enable_cache: bool = True,
        config: Config = None
    ):
        # Load configuration
        self.config = config or Config()

        self.base_url = base_url or self.config.tts_url
        self.default_voice = default_voice or self.config.default_voice
        self.default_speed = default_speed or self.config.default_speed
        self.synthesize_url = f"{self.base_url}/tts/synthesize"
        self.voices_url = f"{self.base_url}/tts/voices"
        self.cache = AudioCache() if enable_cache else None

        logger.info(f"TTS client initialized with URL: {self.base_url}")

        # Create session with connection pooling and retry logic
        self.session = self._create_session_with_retries()

    def _create_session_with_retries(self) -> requests.Session:
        """Create HTTP session with retry logic and connection pooling."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,  # Total retries
            backoff_factor=1,  # Wait 1s, 2s, 4s between retries
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP codes
            allowed_methods=["POST", "GET"]
        )

        # Mount adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set user agent
        session.headers.update({"User-Agent": "Readable/0.1.0"})

        logger.debug("HTTP session created with retry logic and connection pooling")
        return session

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None
    ) -> Optional[bytes]:
        """Synthesize text to speech with caching, returns WAV audio bytes."""
        if not text.strip():
            logger.warning("Empty text provided to synthesize")
            return None

        voice = voice or self.default_voice
        speed = speed or self.default_speed

        logger.debug(f"Synthesizing {len(text)} chars (voice={voice}, speed={speed})")

        if self.cache:
            cached_audio = self.cache.get(text, voice, speed)
            if cached_audio:
                logger.debug(f"Cache HIT: {len(cached_audio)} bytes")
                return cached_audio
            logger.debug("Cache MISS")

        try:
            logger.debug(f"Calling TTS API at {self.synthesize_url}")
            response = self.session.post(
                self.synthesize_url,
                json={"text": text, "voice": voice, "speed": speed},
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"TTS API error {response.status_code}: {response.text}")
                return None

            response_json = response.json()
            audio_base64 = response_json.get('audio_data', '')

            if not audio_base64:
                logger.error("No audio data in response")
                return None

            # Validate and decode Base64
            try:
                audio_bytes = base64.b64decode(audio_base64, validate=True)
            except Exception as e:
                logger.error(f"Invalid Base64 audio data: {e}")
                return None

            # Validate WAV format (minimum header size)
            if len(audio_bytes) < 44:
                logger.error(f"Invalid WAV data received (too short: {len(audio_bytes)} bytes)")
                return None

            logger.debug(f"API response: {len(audio_bytes)} bytes")

            if self.cache:
                self.cache.put(text, voice, speed, audio_bytes)
                logger.debug("Saved to cache")

            return audio_bytes

        except requests.Timeout:
            logger.error(f"TTS API timeout after 30s")
            return None
        except requests.ConnectionError as e:
            logger.error(f"TTS API connection error: {e}")
            return None
        except requests.RequestException as e:
            logger.error(f"TTS API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}", exc_info=True)
            return None

    def get_voices(self) -> list[str]:
        """Get list of available voices."""
        try:
            response = self.session.get(self.voices_url, timeout=5)
            if response.status_code == 200:
                return response.json()
            logger.warning(f"Failed to get voices: HTTP {response.status_code}")
            return []
        except Exception as e:
            logger.warning(f"Failed to get voices: {e}")
            return []

    def save_audio(self, audio_bytes: bytes, output_path: Path) -> bool:
        """Save audio bytes to file."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(audio_bytes)
            return True
        except Exception as e:
            logger.error(f"Error saving audio: {e}", exc_info=True)
            return False
