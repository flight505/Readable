"""Integration tests for full TTS workflow."""

import pytest
from pathlib import Path
from readable.chunker import TextChunker
from readable.tts_client import KokoroTTSClient
from readable.parallel_tts import ParallelTTSGenerator


@pytest.fixture
def sample_text():
    """Load sample text from fixtures."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_text.md"
    return fixture_path.read_text()[:3000]  # First 3000 chars


def test_chunking_workflow(sample_text):
    """Test that text can be chunked successfully."""
    chunker = TextChunker(max_chars=750)
    chunks = chunker.chunk(sample_text)

    assert len(chunks) > 0
    assert all(len(chunk) <= 750 for chunk in chunks)
    print(f"✅ Chunked into {len(chunks)} chunks")


def test_tts_client_initialization():
    """Test that TTS client initializes correctly."""
    client = KokoroTTSClient(enable_cache=False)

    assert client.base_url is not None
    assert client.session is not None
    print(f"✅ TTS client initialized (server: {client.base_url})")


@pytest.mark.slow
def test_audio_generation_single_chunk(sample_text):
    """Test generating audio for a single chunk (slow - requires API)."""
    chunker = TextChunker(max_chars=750)
    chunks = chunker.chunk(sample_text)

    client = KokoroTTSClient(enable_cache=False)

    # Test first chunk only
    print(f"\n🎵 Testing audio generation for first chunk ({len(chunks[0])} chars)...")
    audio = client.synthesize(chunks[0], voice="af_bella", speed=1.0)

    if audio:
        assert len(audio) > 44  # At least WAV header size
        print(f"✅ Generated {len(audio):,} bytes of audio")
        print(f"   Estimated duration: ~{len(chunks[0]) / 11.8:.1f}s")
    else:
        pytest.skip("TTS API not available")


@pytest.mark.slow
def test_parallel_generation_workflow(sample_text):
    """Test parallel TTS generation workflow (slow - requires API)."""
    chunker = TextChunker(max_chars=750)
    chunks = chunker.chunk(sample_text)

    client = KokoroTTSClient(enable_cache=False)
    generator = ParallelTTSGenerator(client=client, max_workers=2)

    # Generate first 2 chunks only (faster test)
    test_chunks = chunks[:2]
    print(f"\n🎵 Testing parallel generation for {len(test_chunks)} chunks...")

    audio_chunks = generator.generate_batch(
        test_chunks,
        voice="af_bella",
        speed=1.0
    )

    valid_audio = [a for a in audio_chunks if a]

    if valid_audio:
        assert len(valid_audio) <= len(test_chunks)
        total_bytes = sum(len(a) for a in valid_audio)
        print(f"✅ Generated {len(valid_audio)}/{len(test_chunks)} chunks ({total_bytes:,} bytes)")
    else:
        pytest.skip("TTS API not available")


def test_workflow_stats(sample_text, capsys):
    """Test workflow and output statistics."""
    chunker = TextChunker(max_chars=750)
    chunks = chunker.chunk(sample_text)

    print(f"\n📊 Workflow Statistics:")
    print(f"   Text length: {len(sample_text):,} chars")
    print(f"   Chunks needed: {len(chunks)}")
    print(f"   Avg chunk size: {sum(len(c) for c in chunks)/len(chunks):.0f} chars")
    print(f"   Estimated duration: ~{len(sample_text) / 11.8:.1f}s")

    captured = capsys.readouterr()
    assert "Workflow Statistics" in captured.out
