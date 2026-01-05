"""Component tests without audio playback."""

from readable.chunker import TextChunker
from readable.tts_client import KokoroTTSClient


def test_chunker():
    """Test text chunking."""
    print("\n=== Testing Text Chunker ===")

    chunker = TextChunker(max_chars=750)

    short_text = "This is a short test."
    chunks = chunker.chunk(short_text)
    print(f"✓ Short text ({len(short_text)} chars) -> {len(chunks)} chunk")

    long_text = " ".join([
        "This is a test sentence." for _ in range(100)
    ])

    chunks = chunker.chunk(long_text)
    print(f"✓ Long text ({len(long_text)} chars) -> {len(chunks)} chunks")

    for i, chunk in enumerate(chunks, 1):
        print(f"  Chunk {i}: {len(chunk)} chars")
        if len(chunk) > 750:
            print(f"  ✗ ERROR: Chunk {i} exceeds max length!")
            return False

    print("✓ All chunks within limit\n")
    return True


def test_tts_client():
    """Test TTS client."""
    print("=== Testing TTS Client ===")

    client = KokoroTTSClient()

    test_cases = [
        "Hello world!",
        "This is a longer test to see how the API handles more text.",
        "The quick brown fox jumps over the lazy dog. " * 10
    ]

    for i, text in enumerate(test_cases, 1):
        print(f"\nTest {i}: {len(text)} chars")
        audio_bytes = client.synthesize(text)

        if audio_bytes:
            print(f"  ✓ Generated {len(audio_bytes):,} bytes")
            if audio_bytes[:4] != b'RIFF':
                print(f"  ✗ Invalid WAV format")
                return False
        else:
            print(f"  ✗ Failed to generate audio")
            return False

    print("\n✓ TTS client working\n")
    return True


def main():
    """Run component tests."""
    print("=" * 60)
    print("READABLE COMPONENT TESTS")
    print("=" * 60)

    success = True

    if not test_chunker():
        success = False

    if not test_tts_client():
        success = False

    print("=" * 60)
    if success:
        print("✓ ALL COMPONENT TESTS PASSED")
        print("\nReady to launch the app! Run:")
        print("  uv run readable")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 60)


if __name__ == "__main__":
    main()
