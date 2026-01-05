"""Custom exceptions for Readable application."""


class ReadableException(Exception):
    """Base exception for Readable application."""
    pass


class ValidationError(ReadableException):
    """Raised when input validation fails."""
    pass


class AudioGenerationError(ReadableException):
    """Raised when TTS audio generation fails."""
    pass


class PlaybackError(ReadableException):
    """Raised when audio playback fails."""
    pass
