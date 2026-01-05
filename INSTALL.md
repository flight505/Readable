# Installation Guide

## Quick Start

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

Automatically start Readable on login with auto-restart:

```bash
# Install the LaunchAgent
cp com.readable.tts.plist ~/Library/LaunchAgents/

# Start immediately
launchctl load ~/Library/LaunchAgents/com.readable.tts.plist
launchctl start com.readable.tts
```

**To stop:**
```bash
launchctl stop com.readable.tts
launchctl unload ~/Library/LaunchAgents/com.readable.tts.plist
```

**To check status:**
```bash
launchctl list | grep readable
```

**View logs:**
```bash
tail -f ~/.readable/logs/launchd.log
tail -f ~/.readable/logs/launchd.error.log
```

### Option 2: Login Items (Manual)

1. Run Readable manually: `uv run readable`
2. System Settings → General → Login Items
3. Add Readable to the list

## Configuration

Create `~/.readable/config.json`:

```json
{
  "tts_url": "http://your-tts-server:8001",
  "max_text_length": 1000000,
  "max_chunks": 100,
  "max_workers": 4,
  "default_voice": "af_bella",
  "default_speed": 1.0,
  "cache_max_size_mb": 100,
  "history_max_size": 50
}
```

**Environment Variables:**
- `KOKORO_TTS_URL` - Override TTS server URL
- `READABLE_MAX_TEXT_LENGTH` - Override max text length
- `READABLE_MAX_WORKERS` - Override parallel workers

## Troubleshooting

**App not starting:**
```bash
# Check LaunchAgent logs
tail -f ~/.readable/logs/launchd.error.log

# Check app logs
tail -f ~/.readable/logs/readable_*.log

# Verify Python path
which python
ls -la /Users/jesper/Projects/Dev_projects/Tools/Readable/.venv/bin/python
```

**Restart the app:**
```bash
launchctl stop com.readable.tts
launchctl start com.readable.tts
```

**Menu bar icon not appearing:**
- Check macOS Accessibility permissions
- Verify SF Symbols are available (macOS 11.0+)

**Audio not playing:**
- Check macOS audio output settings
- Verify pygame is installed: `uv run python -c "import pygame"`

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
