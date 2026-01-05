"""Test pause and resume functionality."""

from readable.tts_client import KokoroTTSClient
from readable.audio_player import AudioPlayer
import time

print("Testing Pause/Resume Functionality")
print("=" * 60)
print()

# Generate test audio
client = KokoroTTSClient(enable_cache=False)
print("Generating test audio chunks...")

chunks = [
    "First chunk playing now.",
    "Second chunk is this one.",
    "Third chunk comes next.",
]

audio_chunks = []
for i, text in enumerate(chunks):
    print(f"  Chunk {i+1}: {text}")
    audio = client.synthesize(text, voice="af_bella", speed=1.0)
    if audio:
        audio_chunks.append(audio)

print(f"✅ Generated {len(audio_chunks)} audio chunks")
print()

# Test playback with pause
player = AudioPlayer()
player.load_queue(audio_chunks)

print("Test sequence:")
print("  1. Start playback")
print("  2. Wait 2 seconds")
print("  3. PAUSE")
print("  4. Wait 2 seconds (should stay paused)")
print("  5. RESUME")
print("  6. Let it finish")
print()

print("Starting playback...")
player.play()
time.sleep(2)

print("⏸  PAUSING (should stay on current chunk)...")
player.pause()
status = player.get_status()
chunk_before_pause = status['current_chunk']
print(f"   Paused at chunk: {chunk_before_pause}/{status['total_chunks']}")

print("   Waiting 2 seconds while paused...")
time.sleep(2)

status = player.get_status()
chunk_after_pause = status['current_chunk']
print(f"   Still at chunk: {chunk_after_pause}/{status['total_chunks']}")

if chunk_before_pause == chunk_after_pause:
    print("   ✅ PASS: Chunk didn't change (no skip)")
else:
    print(f"   ❌ FAIL: Chunk changed from {chunk_before_pause} to {chunk_after_pause}")

print("▶️  RESUMING...")
player.play()

print("   Letting playback finish...")
time.sleep(5)

print()
print("✅ Pause/Resume test complete!")
print()
print("Manual test:")
print("  1. Launch app: uv run readable")
print("  2. Read some text")
print("  3. Click Pause (⌘K)")
print("  4. Verify it stays paused (doesn't skip)")
print("  5. Click Play (⌘P)")
print("  6. Verify it resumes from same spot")

player.cleanup()
