"""Optimized macOS menu bar application for Readable TTS."""

import rumps
import pyperclip
from threading import Thread
from PyObjCTools import AppHelper
from .chunker import TextChunker
from .tts_client import KokoroTTSClient
from .local_tts_client import LocalTTSClient
from .audio_player import AudioPlayer
from .parallel_tts import ParallelTTSGenerator
from .sf_symbols import SFSymbols, SYMBOLS
from .history import ReadingHistory
from .config import Config
from .validator import InputValidator
from .logger import setup_logger
from .exceptions import ValidationError, AudioGenerationError

logger = setup_logger("readable.app")


class ReadableApp(rumps.App):
    """Optimized menu bar app with parallel processing, caching, and enhanced UI."""

    VOICES = {
        "􀉉 Bella (US Female)": "af_bella",
        "􀉉 Sarah (US Female)": "af_sarah",
        "􀉈 Adam (US Male)": "am_adam",
        "􀉈 Michael (US Male)": "am_michael",
        "􀉉 Emma (UK Female)": "bf_emma",
        "􀉉 Isabella (UK Female)": "bf_isabella",
        "􀉈 George (UK Male)": "bm_george",
        "􀉈 Lewis (UK Male)": "bm_lewis",
    }

    SPEEDS = {
        "􀟰 0.75x (Slower)": 0.75,
        "􀊃 1.0x (Normal)": 1.0,
        "􀞝 1.25x (Faster)": 1.25,
        "􀐱 1.5x (Fast)": 1.5,
    }

    def __init__(self):
        logger.info("Initializing ReadableApp...")

        # Load configuration
        self.config = Config()
        logger.info(f"Configuration loaded: TTS URL={self.config.tts_url}")

        # Use custom menu bar icon if available, otherwise fall back to SF Symbol
        menu_bar_icon = SFSymbols.get_custom_menu_icon()
        if menu_bar_icon:
            logger.info(f"Using custom menu bar icon: {menu_bar_icon}")
        else:
            menu_bar_icon = SFSymbols.create_icon(SYMBOLS["menu_bar"])
            logger.debug(f"Using SF Symbol menu bar icon: {menu_bar_icon}")

        super(ReadableApp, self).__init__(
            name="",  # Empty name - icon only
            icon=menu_bar_icon,  # Path to SF Symbol icon file
            template=True,  # Template mode for dark/light adaptation
            quit_button=None
        )

        logger.info("Initializing components...")
        self.chunker = TextChunker(max_chars=750)

        # Initialize TTS client based on config
        self.use_local_tts = self.config.use_local_tts
        self.tts_client = self._create_tts_client()

        self.parallel_generator = ParallelTTSGenerator(
            client=self.tts_client,
            max_workers=self.config.max_workers
        )
        self.player = AudioPlayer()
        self.history = ReadingHistory()
        self.validator = InputValidator(config=self.config)

        self.current_voice = "af_bella"
        self.current_speed = 1.0

        self.player.on_chunk_change = self._update_status
        self.player.on_queue_complete = self._on_playback_complete

        logger.info("ReadableApp initialized successfully")

        voice_menu = []
        for voice_name, voice_id in self.VOICES.items():
            item = rumps.MenuItem(
                voice_name,
                callback=lambda sender, v=voice_id: self.set_voice(v, sender)
            )
            if voice_id == self.current_voice:
                item.state = True
            voice_menu.append(item)

        speed_menu = []
        for speed_name, speed_val in self.SPEEDS.items():
            item = rumps.MenuItem(
                speed_name,
                callback=lambda sender, s=speed_val: self.set_speed(s, sender)
            )
            if speed_val == self.current_speed:
                item.state = True
            speed_menu.append(item)

        # Recent menu (will be populated dynamically)
        recent_menu = [rumps.MenuItem("(No recent readings)", callback=None)]

        # TTS Mode menu
        tts_mode_menu = [
            rumps.MenuItem(
                "􀆪 Remote (ml-server)",
                callback=lambda sender: self.set_tts_mode(False, sender)
            ),
            rumps.MenuItem(
                "􀟜 Local (MLX)",
                callback=lambda sender: self.set_tts_mode(True, sender)
            ),
        ]
        # Set initial state
        tts_mode_menu[0].state = not self.use_local_tts
        tts_mode_menu[1].state = self.use_local_tts

        # Clean Unicode symbols for menu items
        self.menu = [
            rumps.MenuItem("􀈕 Read Clipboard (⌘R)", callback=self.read_clipboard),
            ["􀐿 Recent", recent_menu],
            rumps.separator,
            rumps.MenuItem("􀊃 Play (⌘P)", callback=self.play),
            rumps.MenuItem("􀊅 Pause (⌘K)", callback=self.pause),
            rumps.MenuItem("􀊇 Skip (⌘→)", callback=self.skip),
            rumps.separator,
            ["􀑪 Voice", voice_menu],
            ["􀐱 Speed", speed_menu],
            ["🖥️ TTS Mode", tts_mode_menu],
            rumps.separator,
            rumps.MenuItem("􀆺 Status: Idle", callback=None),
            rumps.MenuItem("􀐱 Cache Stats", callback=self.show_cache_stats),
            rumps.separator,
            rumps.MenuItem("􀈑 Clear Cache", callback=self.clear_cache),
            rumps.MenuItem("􀆧 Quit", callback=self.quit_app),
        ]

        self._status_item = self.menu["􀆺 Status: Idle"]
        self._recent_menu = self.menu["􀐿 Recent"]
        self._tts_mode_menu = self.menu["🖥️ TTS Mode"]

        # Update recent menu on startup
        self._update_recent_menu()

    def _create_tts_client(self):
        """Create the appropriate TTS client based on configuration."""
        if self.use_local_tts:
            local_client = LocalTTSClient(config=self.config)
            if local_client.is_available():
                logger.info("Using local MLX TTS client")
                return local_client
            else:
                logger.warning(
                    f"Local model not found at {self.config.local_model_path}, "
                    "falling back to remote TTS"
                )
                self.use_local_tts = False

        logger.info("Using remote TTS client")
        return KokoroTTSClient(config=self.config)

    def set_tts_mode(self, use_local: bool, sender):
        """Switch between local and remote TTS mode."""
        if use_local == self.use_local_tts:
            return  # No change

        self.use_local_tts = use_local

        # Recreate TTS client
        self.tts_client = self._create_tts_client()
        self.parallel_generator = ParallelTTSGenerator(
            client=self.tts_client,
            max_workers=self.config.max_workers
        )

        # Update menu checkmarks
        for item in self._tts_mode_menu:
            item.state = False
        sender.state = True

        mode_name = "Local (MLX)" if self.use_local_tts else "Remote (ml-server)"
        self._update_status_text(f"TTS Mode: {mode_name}")
        logger.info(f"Switched to {'local' if use_local else 'remote'} TTS mode")

    def set_voice(self, voice_id: str, sender):
        """Change TTS voice."""
        self.current_voice = voice_id

        for item in self.menu["􀑪 Voice"]:
            item.state = False
        sender.state = True

        voice_name = [k for k, v in self.VOICES.items() if v == voice_id][0]
        self._update_status_text(f"Voice: {voice_name}")

    def set_speed(self, speed: float, sender):
        """Change playback speed."""
        self.current_speed = speed

        for item in self.menu["􀐱 Speed"]:
            item.state = False
        sender.state = True

        self._update_status_text(f"Speed: {speed}x")

    def read_clipboard(self, _):
        """Read text from clipboard with parallel processing."""
        Thread(target=self._read_clipboard_background, daemon=True).start()

    def _read_clipboard_background(self):
        """Background worker for clipboard processing."""
        try:
            logger.info("=== Starting clipboard processing ===")

            text = self._get_clipboard_text()
            chunks = self._validate_and_chunk_text(text)
            audio_chunks = self._generate_audio(chunks)
            self._start_playback(audio_chunks)
            self._save_to_history(text, chunks)

            logger.info("=== Clipboard processing complete ===")

        except ValidationError as e:
            logger.warning(f"Validation failed: {e}")
            self._update_status_text(str(e))
        except AudioGenerationError as e:
            logger.error(f"Audio generation failed: {e}")
            self._update_status_text("Failed to generate audio")
        except Exception as e:
            logger.error(f"Error in background processing: {e}", exc_info=True)
            self._update_status_text("Error")

    def _get_clipboard_text(self) -> str:
        """Get text from clipboard."""
        text = pyperclip.paste()
        logger.info(f"Clipboard text: {len(text)} characters")
        return text

    def _validate_and_chunk_text(self, text: str) -> list[str]:
        """Validate input text and split into chunks."""
        # Validate text
        is_valid, error_msg = self.validator.validate_text(text)
        if not is_valid:
            raise ValidationError(error_msg)

        self._update_status_text("Processing...")

        # Clean text for TTS (removes URLs, normalizes code, etc.)
        text = self.validator.sanitize_text(text)
        logger.info(f"Text cleaned: {len(text)} characters after sanitization")

        # Chunk text
        logger.info("Chunking text...")
        chunks = self.chunker.chunk(text)
        logger.info(f"Created {len(chunks)} chunks")

        # Validate chunks
        is_valid, error_msg = self.validator.validate_chunks(chunks)
        if not is_valid:
            raise ValidationError(error_msg)

        logger.debug(
            f"Chunk sizes: min={min(len(c) for c in chunks)}, "
            f"max={max(len(c) for c in chunks)}, "
            f"avg={sum(len(c) for c in chunks)/len(chunks):.0f}"
        )

        return chunks

    def _generate_audio(self, chunks: list[str]) -> list[bytes]:
        """Generate TTS audio for text chunks."""
        self._update_status_text(f"Processing {len(chunks)} chunk(s)...")

        logger.info(
            f"Starting parallel TTS generation for {len(chunks)} chunks "
            f"(voice={self.current_voice}, speed={self.current_speed})..."
        )

        audio_chunks = self.parallel_generator.generate_batch(
            chunks,
            voice=self.current_voice,
            speed=self.current_speed,
            progress_callback=self._on_generation_progress
        )

        logger.info("TTS generation complete, validating chunks...")
        valid_chunks = [chunk for chunk in audio_chunks if chunk]
        logger.info(f"Valid chunks: {len(valid_chunks)}/{len(audio_chunks)}")

        if not valid_chunks:
            raise AudioGenerationError("No valid audio chunks generated")

        total_size = sum(len(chunk) for chunk in valid_chunks)
        logger.info(
            f"Generated {len(valid_chunks)} chunks "
            f"(total size: {total_size/1024/1024:.1f} MB)"
        )

        return valid_chunks

    def _start_playback(self, audio_chunks: list[bytes]):
        """Load audio queue and start playback."""
        logger.info(f"Loading {len(audio_chunks)} chunks into player...")
        self.player.load_queue(audio_chunks)

        logger.info("Starting playback...")
        self.player.play()

        self._update_status_text(f"Playing {len(audio_chunks)} chunk(s)")

    def _save_to_history(self, text: str, chunks: list[str]):
        """Save reading session to history."""
        logger.info("Saving session to history...")
        self.history.add_session(
            text=text,
            chunks=chunks,
            voice=self.current_voice,
            speed=self.current_speed,
            chunk_count=len(chunks)
        )
        self._update_recent_menu()
        logger.info("Session saved")

    def _on_generation_progress(self, current: int, total: int):
        """Handle TTS generation progress updates."""
        logger.debug(f"Generation progress: {current}/{total}")
        self._update_status_text(f"Generated {current}/{total}")

    def play(self, _):
        """Start or resume playback."""
        status = self.player.get_status()
        if not status["has_queue"]:
            self._update_status_text("No audio loaded")
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

    def show_cache_stats(self, _):
        """Display cache statistics."""
        if not self.tts_client.cache:
            rumps.alert("Cache disabled")
            return

        stats = self.tts_client.cache.get_stats()
        message = (
            f"Entries: {stats['entries']}\n"
            f"Size: {stats['total_size_mb']:.1f} MB\n"
            f"Total Hits: {stats['total_hits']}\n"
            f"Avg Hits/Entry: {stats['hit_rate']:.1f}"
        )
        rumps.alert("Cache Statistics", message=message)

    def clear_cache(self, _):
        """Clear audio cache."""
        if not self.tts_client.cache:
            rumps.alert("Cache disabled")
            return

        response = rumps.alert(
            "Clear Cache",
            "This will delete all cached audio. Continue?",
            ok="Clear",
            cancel="Cancel"
        )

        if response == 1:
            self._update_status_text("Clearing cache...")
            Thread(target=self._clear_cache_background, daemon=True).start()

    def _clear_cache_background(self):
        """Background worker for cache clearing."""
        try:
            logger.info("Starting cache clear operation...")
            self.tts_client.cache.clear()
            logger.info("Cache clear complete")
            self._update_status_text("Cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}", exc_info=True)
            self._update_status_text("Cache clear failed")

    def _update_recent_menu(self):
        """Update the Recent menu with latest history."""
        logger.debug("Updating recent menu...")

        # Clear existing items
        self._recent_menu.clear()

        # Get recent sessions
        recent_sessions = self.history.get_recent(limit=10)

        if not recent_sessions:
            self._recent_menu.add(rumps.MenuItem("(No recent readings)", callback=None))
            return

        # Add each session
        for i, session in enumerate(recent_sessions):
            preview = self.history.format_session_preview(session, max_length=60)
            item = rumps.MenuItem(
                preview,
                callback=lambda sender, idx=i: self.replay_session(idx)
            )
            self._recent_menu.add(item)

        # Add separator and clear option
        self._recent_menu.add(rumps.separator)
        self._recent_menu.add(rumps.MenuItem("􀈑 Clear History", callback=self.clear_history))

        logger.debug(f"Recent menu updated with {len(recent_sessions)} sessions")

    def replay_session(self, session_index: int):
        """Replay a session from history."""
        logger.info(f"Replaying session {session_index}")

        session = self.history.get_session(session_index)
        if not session:
            logger.error(f"Session {session_index} not found")
            self._update_status_text("Session not found")
            return

        # Start replay in background thread
        Thread(target=self._replay_session_background, args=(session,), daemon=True).start()

    def _replay_session_background(self, session: dict):
        """Background worker for replaying a session."""
        try:
            logger.info(f"=== Replaying session: {session['preview'][:50]} ===")

            text = session["full_text"]
            chunks = session["chunks"]
            voice = session["voice"]
            speed = session["speed"]

            self._update_status_text(f"Replaying ({session['chunk_count']} chunks)...")

            logger.info(f"Generating audio for {len(chunks)} chunks (from cache)...")

            # Generate audio (should be instant from cache)
            audio_chunks = self.parallel_generator.generate_batch(
                chunks,
                voice=voice,
                speed=speed,
                progress_callback=lambda c, t: self._update_status_text(f"Loading {c}/{t}")
            )

            valid_chunks = [chunk for chunk in audio_chunks if chunk]
            logger.info(f"Loaded {len(valid_chunks)} chunks from cache")

            if valid_chunks:
                total_size = sum(len(chunk) for chunk in valid_chunks)
                logger.info(f"Loading queue: {total_size/1024/1024:.1f} MB")

                self.player.load_queue(valid_chunks)
                self.player.play()
                self._update_status_text(f"Playing {len(valid_chunks)} chunk(s)")
            else:
                logger.error("No valid chunks for replay")
                self._update_status_text("Replay failed")

            logger.info("=== Replay complete ===")

        except Exception as e:
            logger.error(f"Error replaying session: {e}", exc_info=True)
            self._update_status_text("Replay error")

    def clear_history(self, _):
        """Clear reading history."""
        response = rumps.alert(
            "Clear History",
            "This will delete your reading history (cached audio will remain). Continue?",
            ok="Clear",
            cancel="Cancel"
        )

        if response == 1:
            self.history.clear()
            self._update_recent_menu()
            self._update_status_text("History cleared")

    def quit_app(self, _):
        """Clean up and quit."""
        self.player.cleanup()
        SFSymbols.cleanup()
        rumps.quit_application()

    def _update_status(self, current: int, total: int):
        """Update status display with chunk progress."""
        self._update_status_text(f"Playing {current}/{total}")

    def _on_playback_complete(self):
        """Handle playback completion."""
        self._update_status_text("Complete")

    def _update_status_text(self, text: str):
        """Update status menu item (thread-safe via main thread dispatch)."""
        def _do_update():
            # SF Symbols Unicode for status icons
            icon_map = {
                "Idle": "􀆺",          # moon.zzz.fill
                "Processing": "􀍟",   # gearshape.fill
                "Generated": "􀁣",    # checkmark.circle.fill
                "Playing": "􀊄",      # play.circle.fill
                "Paused": "􀊆",       # pause.circle.fill
                "Complete": "􀁣",     # checkmark.circle.fill
                "Error": "􀀲",        # xmark.circle.fill
                "Failed": "􀀲",       # xmark.circle.fill
                "No": "􀀲",           # xmark.circle.fill (for "No text")
                "Voice": "􀑪",        # waveform
                "Speed": "􀐱",        # gauge
                "Cache": "􀁣",        # checkmark
            }

            # Extract base status (first word)
            base_status = text.split()[0] if text else "Idle"
            icon = icon_map.get(base_status, "􀆺")

            self._status_item.title = f"{icon} Status: {text}"

        # Dispatch to main thread for thread-safe UI update
        AppHelper.callAfter(_do_update)


def main():
    """Entry point for the optimized application."""
    ReadableApp().run()


if __name__ == "__main__":
    main()
