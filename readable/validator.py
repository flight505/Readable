"""Input validation for Readable app."""

from typing import Tuple
from .config import Config
from .logger import get_logger

logger = get_logger("readable.validator")


class InputValidator:
    """Validates user input to prevent DoS and ensure data integrity."""

    def __init__(self, config: Config = None):
        """
        Initialize validator with configuration.

        Args:
            config: Configuration object (uses defaults if None)
        """
        self.config = config or Config()

    def validate_text(self, text: str) -> Tuple[bool, str]:
        """
        Validate clipboard text.

        Args:
            text: Text to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if text is valid
            - error_message: Empty string if valid, error description if invalid
        """
        # Check if text is string
        if not isinstance(text, str):
            return False, f"Invalid input type: {type(text).__name__}"

        # Check if empty
        if not text or not text.strip():
            return False, "Text is empty"

        # Check length
        max_length = self.config.max_text_length
        if len(text) > max_length:
            size_mb = len(text) / 1_000_000
            max_mb = max_length / 1_000_000
            return False, f"Text too long ({size_mb:.1f}MB). Maximum: {max_mb:.1f}MB"

        # Check for null bytes (could indicate binary data)
        if '\x00' in text:
            return False, "Text contains invalid binary data"

        logger.debug(f"Text validation passed: {len(text)} chars")
        return True, ""

    def validate_chunks(self, chunks: list) -> Tuple[bool, str]:
        """
        Validate chunked text.

        Args:
            chunks: List of text chunks

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(chunks, list):
            return False, f"Invalid chunks type: {type(chunks).__name__}"

        if not chunks:
            return False, "No chunks generated"

        max_chunks = self.config.max_chunks
        if len(chunks) > max_chunks:
            return False, f"Too many chunks ({len(chunks)}). Maximum: {max_chunks}"

        logger.debug(f"Chunk validation passed: {len(chunks)} chunks")
        return True, ""

    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text for TTS processing.

        Args:
            text: Raw text

        Returns:
            Sanitized text
        """
        # Remove null bytes
        text = text.replace('\x00', '')

        # Apply text cleaning if enabled
        if self.config.get("clean_text", True):
            from .text_cleaner import clean_text_for_tts
            text = clean_text_for_tts(text)

        return text
