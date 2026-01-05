"""Verify audio files are created and playable."""

from readable.tts_client import KokoroTTSClient
from readable.audio_player import AudioPlayer
import pygame
from pathlib import Path

print("Verifying audio generation and playback...")
print()

# Generate audio
client = KokoroTTSClient(enable_cache=False)
text = "Testing one two three."
print(f"Generating audio for: '{text}'")

audio_bytes = client.synthesize(text, voice="af_bella", speed=1.0)

if not audio_bytes:
    print("❌ No audio generated!")
    exit(1)

print(f"✅ Generated {len(audio_bytes)} bytes")

# Save to file
test_file = Path("/tmp/test_audio.wav")
test_file.write_bytes(audio_bytes)
print(f"✅ Saved to {test_file}")

# Check file
print(f"✅ File exists: {test_file.exists()}")
print(f"✅ File size: {test_file.stat().st_size} bytes")

# Try to play with pygame directly
print()
print("Testing pygame playback...")
pygame.mixer.init()
pygame.mixer.music.load(str(test_file))
pygame.mixer.music.play()

print("✅ pygame.mixer.music.play() called")
print(f"   Is busy: {pygame.mixer.music.get_busy()}")
print(f"   Volume: {pygame.mixer.music.get_volume()}")

import time
print()
print("Waiting for playback (5 seconds)...")
for i in range(5):
    time.sleep(1)
    busy = pygame.mixer.music.get_busy()
    print(f"   {i+1}s - Still playing: {busy}")

print()
print("✅ Test complete!")
print()
print(f"Manual test: Play the file directly:")
print(f"   afplay {test_file}")
print()
print("This will confirm if the audio file itself is valid.")
