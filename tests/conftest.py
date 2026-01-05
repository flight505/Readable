"""Shared pytest fixtures for Readable TTS tests."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_text():
    """Provide sample text for testing."""
    return "This is a test sentence for TTS processing. It has multiple sentences."


@pytest.fixture
def long_text():
    """Provide long text for chunking tests."""
    sentence = "This is a test sentence with enough words to test chunking. " * 10
    return (sentence + ". ") * 20  # ~1200 characters


@pytest.fixture(scope="session")
def test_output_dir():
    """Ensure test_outputs directory exists."""
    output_dir = Path(__file__).parent.parent / "test_outputs"
    output_dir.mkdir(exist_ok=True)
    return output_dir
