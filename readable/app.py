"""macOS menu bar application for Readable TTS."""

import rumps
import pyperclip
from .chunker import TextChunker
from .tts_client import KokoroTTSClient
from .audio_player import AudioPlayer


class ReadableApp(rumps.App):
    """Menu bar app for text-to-speech reading."""

    def __init__(self):
        super(ReadableApp, self).__init__("📖", quit_button=None)

        self.chunker = TextChunker(max_chars=750)
        self.tts_client = KokoroTTSClient()
        self.player = AudioPlayer()

        self.player.on_chunk_change = self._update_status
        self.player.on_queue_complete = self._on_playback_complete

        self.menu = [
            rumps.MenuItem("Read Clipboard", callback=self.read_clipboard),
            rumps.separator,
            rumps.MenuItem("Play", callback=self.play),
            rumps.MenuItem("Pause", callback=self.pause),
            rumps.MenuItem("Skip", callback=self.skip),
            rumps.separator,
            rumps.MenuItem("Status: Idle", callback=None),
            rumps.separator,
            rumps.MenuItem("Quit", callback=self.quit_app),
        ]

        self._status_item = self.menu["Status: Idle"]

    def read_clipboard(self, _):
        """Read text from clipboard and prepare for playback."""
        try:
            text = pyperclip.paste()

            if not text or not text.strip():
                rumps.notification(
                    "Readable",
                    "No Text Found",
                    "Clipboard is empty or contains no text"
                )
                return

            self._update_status_text("Processing...")

            chunks = self.chunker.chunk(text)

            rumps.notification(
                "Readable",
                "Processing Text",
                f"Generating speech for {len(chunks)} chunk(s)..."
            )

            audio_chunks = []
            for i, chunk in enumerate(chunks, 1):
                self._update_status_text(f"Generating {i}/{len(chunks)}...")
                audio_bytes = self.tts_client.synthesize(chunk)

                if audio_bytes:
                    audio_chunks.append(audio_bytes)
                else:
                    rumps.alert(f"Failed to generate audio for chunk {i}")
                    self._update_status_text("Error")
                    return

            if audio_chunks:
                self.player.load_queue(audio_chunks)
                self.player.play()

                rumps.notification(
                    "Readable",
                    "Playing",
                    f"{len(audio_chunks)} chunk(s) ready"
                )
            else:
                self._update_status_text("Failed")

        except Exception as e:
            rumps.alert(f"Error: {e}")
            self._update_status_text("Error")

    def play(self, _):
        """Start or resume playback."""
        status = self.player.get_status()
        if not status["has_queue"]:
            rumps.alert("No audio loaded. Use 'Read Clipboard' first.")
            return

        self.player.play()
        self._update_status_text("Playing")

    def pause(self, _):
        """Pause playback."""
        self.player.pause()
        self._update_status_text("Paused")

    def skip(self, _):
        """Skip to next chunk."""
        self.player.skip()

    def quit_app(self, _):
        """Clean up and quit."""
        self.player.cleanup()
        rumps.quit_application()

    def _update_status(self, current: int, total: int):
        """Update status display with chunk progress."""
        self._update_status_text(f"Playing {current}/{total}")

    def _on_playback_complete(self):
        """Handle playback completion."""
        self._update_status_text("Complete")
        rumps.notification("Readable", "Playback Complete", "")

    def _update_status_text(self, text: str):
        """Update status menu item."""
        self._status_item.title = f"Status: {text}"


def main():
    """Entry point for the application."""
    ReadableApp().run()


if __name__ == "__main__":
    main()
