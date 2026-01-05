"""Quick test with small text to verify audio playback."""

import pyperclip
from readable.chunker import TextChunker
from readable.tts_client import KokoroTTSClient
from readable.parallel_tts import ParallelTTSGenerator
from readable.audio_player import AudioPlayer
import time

print("=" * 60)
print("Quick Audio Playback Test")
print("=" * 60)

# Small test text
text = "Hello! This is a test of the readable text to speech system. It should generate audio and play it back successfully."

print(f"\nTest text: {text}")
print(f"Length: {len(text)} characters")

# Process
chunker = TextChunker(max_chars=750)
chunks = chunker.chunk(text)
print(f"\nChunks: {len(chunks)}")

# Generate audio
print("\nGenerating audio...")
parallel_gen = ParallelTTSGenerator(max_workers=4)
audio_chunks = parallel_gen.generate_batch(
    chunks,
    voice="af_bella",
    speed=1.0
)

valid_chunks = [c for c in audio_chunks if c]
print(f"Valid audio chunks: {len(valid_chunks)}")

if not valid_chunks:
    print("❌ No audio generated!")
    exit(1)

# Play
print("\nStarting playback...")
player = AudioPlayer()
player.load_queue(valid_chunks)
player.play()

print("✅ Playback started!")
print("\nListening for 5 seconds...")
print("(You should hear audio playing now)")

# Wait for playback
time.sleep(5)

print("\n✅ Test complete!")
print("\nIf you heard audio, the fix works!")
print("If not, there may be a pygame audio configuration issue.")

player.cleanup()
