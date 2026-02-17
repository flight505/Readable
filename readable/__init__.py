"""Readable - Text-to-speech reader using Kokoro TTS API."""

__version__ = "0.1.0"

from .tts_client import KokoroTTSClient
from .local_tts_client import LocalTTSClient
from .text_cleaner import clean_text_for_tts, clean_text_aggressive
from .config import Config

__all__ = [
    "KokoroTTSClient",
    "LocalTTSClient",
    "clean_text_for_tts",
    "clean_text_aggressive",
    "Config",
]
