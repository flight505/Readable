# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Readable** is a macOS menu bar TTS (text-to-speech) application that reads clipboard text aloud using the Kokoro TTS API running on a remote ml-server (via Tailscale). It features intelligent caching, parallel processing, and a native macOS interface with SF Symbols.

**Key constraint:** External Kokoro TTS API with 750-800 character limit per request, requires chunking long texts.

## Development Commands

### Running the App
```bash
# Optimized version (recommended)
uv run readable

# Basic version (no optimizations)
uv run readable-basic
```

### Testing
```bash
# Run all tests
uv run pytest

# Run unit tests only (fast)
uv run pytest tests/unit/ -v

# Run integration tests (requires TTS API)
uv run pytest tests/integration/ -v

# Skip slow tests
uv run pytest -m "not slow"

# With coverage report
uv run pytest --cov=readable --cov-report=html
```

**Test Structure:**
- `tests/unit/` - Fast, isolated component tests (35 tests)
- `tests/integration/` - Full workflow tests (15 tests, 2 marked slow)
- `tests/conftest.py` - Shared pytest fixtures
- `tests/fixtures/` - Test data files

### Debugging
```bash
# Check recent logs
tail -f ~/.readable/logs/readable_*.log

# View all errors
grep ERROR ~/.readable/logs/readable_*.log

# View warnings
grep WARNING ~/.readable/logs/readable_*.log
```

### Package Management
```bash
# Install dependencies
uv sync

# All dependencies managed via pyproject.toml
# Uses uv (not pip) for package management
```

## Architecture Overview

### Core Data Flow
```
Clipboard → Chunker → Cache Check → [Cache Hit OR ML-Server API] → Base64 Decode →
→ Audio Queue → Temp Files (pygame) → Playback
```

**Critical Path:**
1. **Clipboard text** → `pyperclip.paste()` in background thread
2. **Chunking** → `chunker.py` splits at sentence boundaries (~750 chars)
3. **Cache lookup** → SHA256(text + voice + speed) → `~/.readable/cache/{hash}.wav`
4. **API call** (if miss) → POST to `http://100.71.118.55:8001/tts/synthesize` → Base64 WAV response
5. **Parallel generation** → `parallel_tts.py` processes chunks with ThreadPoolExecutor (4 workers)
6. **Playback** → `audio_player.py` writes to temp files, uses pygame.mixer.music
7. **History tracking** → `history.py` saves sessions to `~/.readable/history.json`

### Module Responsibilities

**app_optimized.py** (Main Application)
- rumps menu bar interface
- Background threading for clipboard processing
- Menu management (Voice, Speed, Recent, etc.)
- **Critical:** All UI operations must be on main thread (rumps requirement)

**chunker.py** (Text Splitting)
- Splits text at sentence boundaries
- Max 750 chars per chunk (API limit is 800, safety margin)
- Returns list of text chunks

**tts_client.py** (API Client)
- Calls Kokoro TTS API on ml-server
- Handles Base64 decoding of WAV response
- Integrates with cache for lookups/storage
- Timeout: 30 seconds per request

**cache.py** (Audio Caching)
- LRU disk cache with SHA256 hashing
- Location: `~/.cache/readable/`
- Index: `~/.cache/readable/index.json`
- Eviction when > 100 MB (configurable)
- Thread-safe with locks
- Stores: text_preview, voice, speed, size, hits

**parallel_tts.py** (Parallel Processing)
- ThreadPoolExecutor with 4 workers (configurable)
- Processes chunks in parallel
- Returns results in original order (not completion order)
- Uses dependency injection (accepts TTSClient protocol)

**audio_player.py** (Playback Engine)
- Queue-based playback system
- pygame.mixer.music for audio
- Temp files in `/tmp/tmpXXXX/chunk_N.wav`
- Thread-safe with locks
- **Critical pause bug fix:** Wait loop must check `is_paused` flag to prevent skip-on-pause

**history.py** (Session Tracking)
- Saves reading sessions to `~/.readable/history.json`
- Stores full text + chunks for instant replay
- Max 50 sessions (auto-prune oldest)
- Thread-safe with locks
- Enables "Recent" menu feature

**config.py** (Configuration Management)
- Loads from `~/.readable/config.json` (optional)
- Environment variable overrides
- Defaults for all settings
- Validates and handles errors gracefully

**validator.py** (Input Validation)
- DoS prevention (1M character limit)
- Chunk count limits (100 max)
- Binary data detection
- Sanitizes text input

**sf_symbols.py** (macOS Icons)
- Converts SF Symbol names to NSImage PNG files
- Menu bar icon: `speaker.wave.2` (not book.fill - too heavy)
- Temp storage: `/tmp/readable_icons/`
- Uses logger (not print statements)

**protocols.py** (Type Protocols)
- TTSClient protocol for dependency injection
- Enables testability with mock clients

**exceptions.py** (Custom Exceptions)
- ReadableException (base)
- ValidationError (input validation)
- AudioGenerationError (TTS failures)
- PlaybackError (audio playback issues)

**logger.py** (Logging System)
- Logs to `~/.readable/logs/readable_YYYYMMDD_HHMMSS.log`
- File: DEBUG level, Console: INFO level
- All modules use `get_logger(__name__)`

## Critical Threading Rules

**macOS/rumps enforces main-thread-only UI operations.** Violating this causes freezes/crashes.

### ✅ Safe (from background threads):
- `self._update_status_text()` - Uses `AppHelper.callAfter()` to dispatch to main thread
- `logger.info()` / `logger.error()` - Logging
- File I/O, network requests
- Audio playback operations

### ❌ Never from background threads:
- `rumps.notification()`
- `rumps.alert()`
- Any NSWindow/NSAlert operations
- Direct menu item modification (use `AppHelper.callAfter()` wrapper)

**Pattern:** All clipboard processing happens in `_read_clipboard_background()` daemon thread. UI updates are dispatched to main thread via `PyObjCTools.AppHelper.callAfter()`.

**Key fix:** `_update_status_text()` wraps UI modification in `AppHelper.callAfter(_do_update)` to ensure thread-safe execution on main thread.

## File Storage Locations

```
~/.readable/
├── config.json                # Optional configuration file
├── history.json               # Reading sessions (Recent menu)
└── logs/
    └── readable_*.log         # Per-session logs

~/.cache/readable/
├── {sha256hash}.wav           # Cached audio files
└── index.json                 # Cache metadata

/tmp/tmpXXXX/                  # Auto-deleted on quit
└── chunk_N.wav                # Temp playback files (pygame requirement)

/tmp/readable_icons/           # SF Symbol PNG cache
└── {symbol}_{size}pt_{weight}.png
```

## Recent Improvements & Fixes

### Thread Safety (Fixed)
**Problem:** Race conditions in history and cache operations.
**Fix:** Added `threading.Lock` to `history.py` and `cache.py` for thread-safe operations.

### Dependency Injection (Implemented)
**Improvement:** `ParallelTTSGenerator` now accepts injected `TTSClient` via protocol.
**Benefit:** Full testability with mock clients, better SOLID compliance.

### Method Extraction (Refactored)
**Improvement:** Extracted `_read_clipboard_background()` into 6 focused methods.
**Benefit:** Reduced complexity from 80 lines to 18 lines per method.

### Custom Exception Hierarchy (Implemented)
**Improvement:** Created `ReadableException`, `ValidationError`, `AudioGenerationError`, `PlaybackError`.
**Benefit:** Better error handling and debugging.

### Input Validation (Implemented)
**Security:** DoS prevention with 1M character limit, chunk count limits, binary data detection.

### Configuration Management (Implemented)
**Improvement:** File-based config with environment variable overrides.
**Location:** `~/.readable/config.json`

### Logging Consistency (Fixed)
**Problem:** `sf_symbols.py` used `print()` instead of logger.
**Fix:** Replaced all print statements with appropriate logger calls.

### Pause/Resume Bug (Fixed)
**Problem:** Pause button caused skip to next chunk instead of pausing.
**Root cause:** `pygame.mixer.music.get_busy()` returns False when paused.
**Fix:** `audio_player.py` - Wait loop checks `(get_busy() or self.is_paused)`.

### Quit Button Bug (Fixed)
**Problem:** App froze when clicking quit while clearing cache.
**Fix:** Cache clearing moved to background thread in `app_optimized.py`.

### UI Thread Safety (Fixed)
**Problem:** App froze when reading clipboard—menu stayed open, entire system unresponsive.
**Root cause:** `_update_status_text()` modified rumps MenuItem from background threads (called from `_read_clipboard_background`, `_playback_loop`, progress callbacks). macOS AppKit doesn't allow UI modifications from non-main threads.
**Fix:** Wrapped UI update in `AppHelper.callAfter(_do_update)` to dispatch to main thread.

### SF Symbols Menu Icon
**Use:** `speaker.wave.2` (audio-appropriate, clean)
**Avoid:** `book.fill` (too heavy/detailed for menu bar)

## Testing Strategy

**Run all tests:**
```bash
uv run pytest
```

**Test Organization:**
- `tests/unit/` - Fast, isolated component tests (4 files, 35 tests)
  - `test_chunking.py` - Text chunking tests
  - `test_components.py` - Basic component tests
  - `test_config_validator_history.py` - Config, validator, history thread safety (22 tests)
  - `test_refactoring.py` - Dependency injection, protocols, exceptions (13 tests)
- `tests/integration/` - Full workflow tests (3 files, 15 tests)
  - `test_integration.py` - Component integration
  - `test_pause_resume.py` - Audio player pause/resume
  - `test_workflow.py` - End-to-end TTS workflow
- `tests/fixtures/` - Test data
  - `sample_text.md` - Sample text for testing

**Test Coverage:** 78% (50 tests passing, 2 slow tests skipped by default)

**Pytest Configuration:** See `pyproject.toml` - markers for unit/integration/slow tests.

## API Constraints

**Kokoro TTS Server:** `http://100.71.118.55:8001` (Tailscale)

**Request:**
```json
POST /tts/synthesize
{
  "text": "...",           // Max ~800 chars (we use 750 safety margin)
  "voice": "af_bella",     // 8 voices available
  "speed": 1.0             // 0.75 - 1.5x
}
```

**Response:**
```json
{
  "audio_data": "UklGR..."  // Base64-encoded WAV (24kHz)
}
```

**Performance:** ~0.5s per chunk API call, ~11.8 chars/second speech rate.

## Documentation

- **DEVELOPMENT.md** - Comprehensive developer guide
  - Architecture overview and component responsibilities
  - Testing strategy and coverage
  - API documentation
  - Troubleshooting guide
  - Development workflow
  - Performance benchmarks
- **CLEANUP_SUMMARY.md** - Project cleanup and organization summary
- **README.md** - User-facing documentation

## Common Gotchas

1. **Menu bar icon not appearing:** Check if rumps template mode is enabled, icon file exists in temp dir.

2. **Audio not playing:** Check pygame.mixer.init(), verify temp files created, check macOS audio permissions.

3. **Cache not working:** Verify `~/.readable/cache/` exists, check index.json validity, ensure hash generation consistent.

4. **Recent menu empty:** History file at `~/.readable/history.json`, requires at least one reading session.

5. **Logs show no errors but app frozen:** Likely deadlock - check for nested lock acquisitions, UI calls from background threads.

## Performance Optimization Notes

- **Caching:** 4x speedup (75% improvement) on cache hits
- **Parallel processing:** 2.6x speedup with 4 workers
- **Combined:** Up to 250x faster for repeated content (Recent menu)
- **Memory:** ~150 MB for 66 chunks (44 KB text) loaded in queue

## macOS Requirements

- macOS 11.0+ (Big Sur or later) for SF Symbols
- Python 3.11+
- Tailscale for ml-server access
