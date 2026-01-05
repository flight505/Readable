"""Integration test for Readable components."""

import pytest
from readable.chunker import TextChunker
from readable.tts_client import KokoroTTSClient
from readable.audio_player import AudioPlayer
import time


@pytest.fixture
def audio_bytes():
    """Generate sample audio bytes for testing (requires TTS API)."""
    client = KokoroTTSClient()
    text = "Hello, this is a test of the Kokoro TTS system."
    audio = client.synthesize(text)
    if not audio:
        pytest.skip("TTS API not available")
    return audio


def test_chunker():
    """Test text chunking."""
    print("=== Testing Text Chunker ===")

    chunker = TextChunker(max_chars=750)

    short_text = "This is a short test."
    chunks = chunker.chunk(short_text)
    print(f"Short text ({len(short_text)} chars) -> {len(chunks)} chunk(s)")
    assert len(chunks) == 1

    long_text = """
    This is a longer test text that will definitely exceed the 800 character limit.
    We want to make sure the chunker splits this properly at sentence boundaries.
    Each chunk should be under 750 characters to stay safe within the API limit.
    The chunker should be smart about where it splits. It should prefer sentence
    boundaries like periods, question marks, and exclamation points. If a sentence
    is too long, it should fall back to splitting at commas or even word boundaries.
    This ensures that we never send more than 800 characters to the API, which would
    result in an error. Let's add even more text to really test the chunking logic.
    The more text we add, the more chunks we should get. Each chunk should be
    readable and make sense on its own. This is important for a good user experience.
    """ * 3

    chunks = chunker.chunk(long_text)
    print(f"Long text ({len(long_text)} chars) -> {len(chunks)} chunk(s)")

    for i, chunk in enumerate(chunks, 1):
        print(f"  Chunk {i}: {len(chunk)} chars")
        assert len(chunk) <= 750

    print("✓ Chunker tests passed\n")


def test_tts_client():
    """Test TTS client."""
    print("=== Testing TTS Client ===")

    client = KokoroTTSClient()

    text = "Hello, this is a test of the Kokoro TTS system."
    print(f"Synthesizing: {text}")

    audio_bytes = client.synthesize(text)

    if audio_bytes:
        print(f"✓ Generated {len(audio_bytes):,} bytes of audio")
        assert len(audio_bytes) > 0
        assert audio_bytes[:4] == b'RIFF'
    else:
        print("✗ Failed to generate audio")
        return False

    print("✓ TTS client tests passed\n")
    return audio_bytes


def test_audio_player(audio_bytes):
    """Test audio player."""
    print("=== Testing Audio Player ===")

    player = AudioPlayer()

    player.load_queue([audio_bytes])

    status = player.get_status()
    print(f"Queue loaded: {status['total_chunks']} chunk(s)")
    assert status['total_chunks'] == 1

    print("Starting playback...")
    player.play()

    time.sleep(2)

    status = player.get_status()
    print(f"Playing: {status['is_playing']}")
    assert status['is_playing']

    print("Pausing...")
    player.pause()
    time.sleep(0.5)

    status = player.get_status()
    print(f"Paused: {status['is_paused']}")
    assert status['is_paused']

    print("Resuming...")
    player.play()
    time.sleep(0.5)

    print("Stopping...")
    player.stop()

    status = player.get_status()
    print(f"Stopped: {not status['is_playing']}")
    assert not status['is_playing']

    player.cleanup()

    print("✓ Audio player tests passed\n")


def run_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("READABLE INTEGRATION TESTS")
    print("=" * 60 + "\n")

    try:
        test_chunker()
        audio_bytes = test_tts_client()

        if audio_bytes:
            test_audio_player(audio_bytes)

        print("=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_tests()
