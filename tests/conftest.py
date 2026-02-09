"""Shared pytest fixtures available to all tests.

Provides mock embedding models, temporary databases, and other reusable
test infrastructure.
"""

from pathlib import Path
from typing import Generator
import tempfile
import sqlite3
import numpy as np
import pytest

# Import fixtures from fixtures module
from tests.fixtures.markdown_samples import temp_vault, sample_files_dict


@pytest.fixture
def mock_embedding_model(monkeypatch):
    """Mock Sentence Transformer model returning deterministic embeddings.

    Returns embeddings with correct dimensions (384 for all-MiniLM-L6-v2)
    but deterministic values for predictable test behaviour.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Yields:
        Mock model object with encode method
    """
    class MockModel:
        def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
            self.model_name = model_name
            self.embedding_dim = 384

        def encode(self, texts, show_progress_bar=False, batch_size=32, device='cpu', convert_to_numpy=True):
            """Generate deterministic embeddings based on text content.

            Args:
                texts: List of strings to encode
                show_progress_bar: Ignored (mock)
                batch_size: Ignored (mock)
                device: Ignored (mock)
                convert_to_numpy: Ignored (mock)

            Returns:
                numpy array of shape (len(texts), 384)
            """
            if isinstance(texts, str):
                texts = [texts]

            embeddings = []
            for text in texts:
                # Create deterministic embedding based on text hash only
                # This ensures same text always gets same embedding
                seed = hash(text) % (2**32)
                np.random.seed(seed)
                embedding = np.random.randn(self.embedding_dim).astype(np.float32)
                # Normalise to unit length (cosine similarity ready)
                embedding = embedding / np.linalg.norm(embedding)
                embeddings.append(embedding)

            return np.array(embeddings, dtype=np.float32)

        def get_sentence_embedding_dimension(self):
            """Return embedding dimension.

            Returns:
                Embedding dimension (384)
            """
            return self.embedding_dim

    # Patch SentenceTransformer imports
    def mock_sentence_transformer(*args, **kwargs):
        return MockModel(*args, **kwargs)

    monkeypatch.setattr(
        "sentence_transformers.SentenceTransformer",
        mock_sentence_transformer
    )

    yield MockModel()


@pytest.fixture
def temp_database(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide temporary database path for testing.

    Args:
        tmp_path: Pytest temporary directory

    Yields:
        Path to temporary database file (does not pre-create schema)
    """
    db_path = tmp_path / "test_cache.db"

    yield db_path

    # Cleanup: close any connections and delete database
    # This helps avoid "file in use" errors on Windows
    import gc
    gc.collect()  # Force garbage collection to close connections

    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            pass  # File still in use, will be cleaned by tmp_path


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create temporary .metisem cache directory structure.

    Args:
        tmp_path: Pytest temporary directory

    Returns:
        Path to .metisem directory
    """
    cache_dir = tmp_path / ".metisem"
    cache_dir.mkdir(exist_ok=True)

    # Create subdirectories
    (cache_dir / "embeddings").mkdir(exist_ok=True)
    (cache_dir / "summaries").mkdir(exist_ok=True)

    return cache_dir


@pytest.fixture
def sample_embeddings() -> np.ndarray:
    """Return sample embedding array for testing.

    Returns:
        Numpy array of shape (5, 384) with normalised random embeddings
    """
    np.random.seed(42)
    embeddings = np.random.randn(5, 384).astype(np.float32)
    # Normalise to unit length
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings


@pytest.fixture
def sample_file_hashes() -> dict:
    """Return sample file path to hash mapping for testing.

    Returns:
        Dictionary mapping file paths to SHA256 hashes
    """
    return {
        "note1.md": "a" * 64,  # Mock SHA256 hash
        "note2.md": "b" * 64,
        "note3.md": "c" * 64,
        "note4.md": "d" * 64,
        "note5.md": "e" * 64,
    }
