"""Tests for text chunking functionality."""

import pytest
from pathlib import Path
from readable.chunker import TextChunker


@pytest.fixture
def sample_text_file():
    """Load sample text from fixtures."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_text.md"
    return fixture_path.read_text()


def test_chunker_creates_chunks(sample_text_file):
    """Test that chunker creates appropriate chunks."""
    chunker = TextChunker(max_chars=750)
    chunks = chunker.chunk(sample_text_file)

    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)
    assert all(len(chunk) <= 750 for chunk in chunks)


def test_chunker_preserves_sentences(sample_text_file):
    """Test that chunker tries to keep sentences together."""
    chunker = TextChunker(max_chars=750)
    chunks = chunker.chunk(sample_text_file)

    # Each chunk should end with sentence-ending punctuation or be incomplete
    for chunk in chunks[:-1]:  # All but last chunk
        assert chunk.strip()[-1] in '.!?', f"Chunk doesn't end properly: {chunk[-50:]}"


def test_chunker_handles_short_text():
    """Test chunker with text shorter than max_chars."""
    chunker = TextChunker(max_chars=750)
    short_text = "This is a short sentence."
    chunks = chunker.chunk(short_text)

    assert len(chunks) == 1
    assert chunks[0] == short_text.strip()


def test_chunker_handles_long_sentences():
    """Test chunker splits long sentences at word boundaries."""
    chunker = TextChunker(max_chars=100)
    long_sentence = "This is a very long sentence that will definitely exceed the maximum character limit and should be split at word boundaries to ensure proper processing."

    chunks = chunker.chunk(long_sentence)

    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)
    # Verify chunks don't start/end with spaces
    assert all(chunk.strip() == chunk for chunk in chunks)


def test_chunker_stats(sample_text_file, capsys):
    """Test chunker and output stats (for debugging)."""
    chunker = TextChunker(max_chars=750)
    chunks = chunker.chunk(sample_text_file)

    print(f"\n=== Chunking Statistics ===")
    print(f"Total text length: {len(sample_text_file):,} characters")
    print(f"Total words: {len(sample_text_file.split()):,}")
    print(f"Number of chunks: {len(chunks)}")
    print(f"Average chunk size: {sum(len(c) for c in chunks) / len(chunks):.0f} chars")
    print(f"Estimated reading time: ~{len(sample_text_file.split()) / 150:.0f} minutes")

    # Capture output
    captured = capsys.readouterr()
    assert "Chunking Statistics" in captured.out
