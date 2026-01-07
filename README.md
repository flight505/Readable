# Readable

A **highly optimized** macOS menu bar app for reading text aloud using the Kokoro TTS API.

## Features

- 📋 **Clipboard Integration** - Copy text and click to read
- 🎵 **Smart Chunking** - Splits long texts at sentence boundaries
- ⏯️ **Playback Controls** - Play, pause, skip through chunks
- 🔥 **4x faster** with intelligent audio caching
- 🚄 **2.6x faster** with parallel chunk processing
- 📖 **Recent Readings** - Instant replay from history
- 🎙️ **8 Voices** - US/UK accents, male/female
- ⚡ **Variable Speed** - 0.75x to 1.5x playback
- 🎯 **Native macOS** - SF Symbols, dark/light mode

## Installation

```bash
# Clone and install
git clone https://github.com/flight505/Readable.git
cd Readable
uv sync

# Run once to test
uv run readable
```

## Auto-Start at Login

### Option 1: LaunchAgent (Recommended)

Automatically starts on login and restarts if it crashes:

```bash
# Install the LaunchAgent
cp com.readable.tts.plist ~/Library/LaunchAgents/

# Load and start
launchctl load ~/Library/LaunchAgents/com.readable.tts.plist
```

**Service commands:**
```bash
launchctl list | grep readable          # Check status
launchctl stop com.readable.tts         # Stop
launchctl start com.readable.tts        # Start
launchctl unload ~/Library/LaunchAgents/com.readable.tts.plist  # Disable
```

**View logs:**
```bash
tail -f ~/.readable/logs/launchd.log        # Service output
tail -f ~/.readable/logs/launchd.error.log  # Service errors
```

### Option 2: Login Items (Manual)

1. Run Readable: `uv run readable`
2. System Settings → General → Login Items
3. Add Readable to the list

## Usage

1. **Copy text** to clipboard (⌘C)
2. **Click speaker icon** in menu bar
3. **Select "Read Clipboard"**
4. **Listen!**

### Menu Structure

```
🔊 Readable
├── 􀈕 Read Clipboard (⌘R)
├── 􀐿 Recent ▸
├── ─────────────────────
├── 􀊃 Play (⌘P)
├── 􀊅 Pause (⌘K)
├── 􀊇 Skip (⌘→)
├── ─────────────────────
├── 􀑪 Voice ▸ (8 voices)
├── 􀐱 Speed ▸ (0.75x - 1.5x)
├── ─────────────────────
├── 􀆺 Status: Idle
├── 􀐱 Cache Stats
├── 􀈑 Clear Cache
└── 􀆧 Quit
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| ⌘R | Read Clipboard |
| ⌘P | Play/Resume |
| ⌘K | Pause |
| ⌘→ | Skip to next chunk |

## Configuration

Create `~/.readable/config.json` (optional):

```json
{
  "tts_url": "http://your-tts-server:8001",
  "default_voice": "af_bella",
  "default_speed": 1.0,
  "max_workers": 4,
  "cache_max_size_mb": 100
}
```

**Environment variables** (override config):
- `KOKORO_TTS_URL` - TTS server URL
- `READABLE_MAX_WORKERS` - Parallel workers

## Requirements

- macOS 11.0+ (Big Sur or later)
- Python 3.11+
- Kokoro TTS server access

## Troubleshooting

**View logs:**
```bash
tail -f ~/.readable/logs/readable_*.log     # App logs
grep ERROR ~/.readable/logs/readable_*.log  # Errors only
```

**Common issues:**
- **App not starting** → Check `~/.readable/logs/launchd.error.log`
- **Menu icon not appearing** → Verify macOS 11.0+ for SF Symbols
- **Audio not playing** → Check macOS audio permissions
- **TTS errors** → Verify server at configured URL

**Restart the service:**
```bash
launchctl stop com.readable.tts && launchctl start com.readable.tts
```

## Uninstall

```bash
# Stop and remove LaunchAgent
launchctl stop com.readable.tts
launchctl unload ~/Library/LaunchAgents/com.readable.tts.plist
rm ~/Library/LaunchAgents/com.readable.tts.plist

# Remove app data (optional)
rm -rf ~/.readable/
rm -rf ~/.cache/readable/
```

## Testing

```bash
uv run pytest                    # All tests
uv run pytest tests/unit/ -v     # Unit tests only
uv run pytest -m "not slow"      # Skip slow tests
```

## Architecture

| Module | Responsibility |
|--------|---------------|
| `app_optimized.py` | Menu bar UI, orchestration |
| `tts_client.py` | Kokoro API client with caching |
| `parallel_tts.py` | Multi-threaded TTS generation |
| `audio_player.py` | Queue-based playback (pygame) |
| `chunker.py` | Sentence-boundary text splitting |
| `cache.py` | LRU disk cache with eviction |
| `history.py` | Reading session persistence |
| `config.py` | Configuration management |
| `validator.py` | Input validation, DoS prevention |

See **DEVELOPMENT.md** for detailed architecture and API documentation.
