"""Unified embedding generation using Sentence Transformers.

This module provides a consistent interface for generating embeddings for both
documents and text snippets, with caching support.
"""

import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer


def encode_texts(
    texts: List[str],
    model: SentenceTransformer,
    batch_size: int = 32,
    device: str = 'cpu',
    show_progress: bool = True
) -> np.ndarray:
    """Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed
        model: SentenceTransformer model instance
        batch_size: Batch size for encoding
        device: Device to use ('cpu' or 'cuda')
        show_progress: Whether to show progress bar

    Returns:
        numpy array of embeddings, shape (len(texts), embedding_dim)
    """
    if not texts:
        return np.array([])

    return model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        device=device,
        convert_to_numpy=True
    )


def get_embedding_dimension(model: SentenceTransformer) -> int:
    """Get the embedding dimension for a model.

    Args:
        model: SentenceTransformer model instance

    Returns:
        Embedding dimension as integer
    """
    # Get dimension by encoding a dummy text
    dummy = model.encode(["test"], convert_to_numpy=True)
    return dummy.shape[1]
