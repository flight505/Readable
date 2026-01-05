"""Protocol definitions for dependency injection and loose coupling."""

from typing import Protocol, Optional


class TTSClient(Protocol):
    """Protocol for text-to-speech synthesis clients."""

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None
    ) -> Optional[bytes]:
        """
        Synthesize text to speech audio.

        Args:
            text: Text to synthesize
            voice: Voice ID to use
            speed: Playback speed multiplier

        Returns:
            WAV audio bytes, or None if synthesis failed
        """
        ...

    def get_voices(self) -> list[str]:
        """Get list of available voice IDs."""
        ...
