"""Unified embedding cache system.

This module provides a consistent caching interface that unifies the .npy format
from main.py and .npz format from tagger.py. Designed for future migration to SQLite.
"""

import os
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from sentence_transformers import SentenceTransformer

from .files import read_file_text_and_hash, get_common_vault_path
from .embeddings import encode_texts, get_embedding_dimension


class EmbeddingCache:
    """Manages embedding cache for a vault and model combination."""

    def __init__(self, vault_path: str, model_name: str, cache_dir: str = ".obsidian_linker_cache"):
        """Initialize cache manager.

        Args:
            vault_path: Path to the Obsidian vault
            model_name: Name of the sentence transformer model
            cache_dir: Directory name for cache storage (relative to vault)
        """
        self.vault_path = Path(vault_path)
        self.model_name = model_name
        self.cache_dir = self.vault_path / cache_dir
        self.cache_file = self._get_cache_path()
        self._data: Dict[Path, Dict[str, Any]] = {}

    def _get_cache_path(self) -> Path:
        """Generate cache file path based on vault and model."""
        vault_name = self.vault_path.name.replace('/', '_')
        safe_model = self.model_name.replace('/', '_')
        return self.cache_dir / f"embeddings_{vault_name}_{safe_model}.npz"

    def load(self) -> None:
        """Load cache from disk. Silently returns empty dict if cache doesn't exist."""
        if not self.cache_file.exists():
            self._data = {}
            return

        try:
            data = np.load(self.cache_file, allow_pickle=True)
            # npz format from tagger.py
            if 'paths' in data and 'hashes' in data and 'embs' in data:
                self._data = {
                    Path(p): {'hash': h, 'embedding': e}
                    for p, h, e in zip(data['paths'], data['hashes'], data['embs'])
                }
            # .npy format from main.py (structured array)
            elif data.dtype.names:
                self._data = {
                    Path(item['path']): {'hash': item['hash'], 'embedding': item['embedding']}
                    for item in data
                }
            else:
                self._data = {}
        except Exception:
            self._data = {}

    def save(self) -> None:
        """Save cache to disk in npz format."""
        if not self._data:
            return

        self.cache_dir.mkdir(exist_ok=True)

        paths = np.array([str(p) for p in self._data.keys()])
        hashes = np.array([self._data[p]['hash'] for p in self._data.keys()])
        embs = np.stack([self._data[p]['embedding'] for p in self._data.keys()])

        np.savez(self.cache_file, paths=paths, hashes=hashes, embs=embs)

    def get(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Get cached embedding for a file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with 'hash' and 'embedding' keys, or None if not cached
        """
        return self._data.get(file_path)

    def set(self, file_path: Path, file_hash: str, embedding: np.ndarray) -> None:
        """Store embedding in cache.

        Args:
            file_path: Path to the file
            file_hash: SHA256 hash of file content
            embedding: Embedding vector
        """
        self._data[file_path] = {'hash': file_hash, 'embedding': embedding}

    def is_valid(self, file_path: Path, current_hash: str) -> bool:
        """Check if cached embedding is valid for current file content.

        Args:
            file_path: Path to the file
            current_hash: Current SHA256 hash of file content

        Returns:
            True if cache is valid, False otherwise
        """
        cached = self.get(file_path)
        return cached is not None and cached['hash'] == current_hash


def generate_embeddings(
    file_paths: List[Path],
    model: SentenceTransformer,
    model_name: str,
    batch_size: int,
    device: str,
    vault_path: str,
    force: bool = False
) -> Tuple[np.ndarray, List[Path]]:
    """Generate embeddings for files using cache.

    Args:
        file_paths: List of file paths to embed
        model: SentenceTransformer model instance
        model_name: Name of the model (for cache)
        batch_size: Batch size for encoding
        device: Device to use ('cpu' or 'cuda')
        vault_path: Path to the vault (for cache location)
        force: If True, ignore cache and regenerate all embeddings

    Returns:
        Tuple of (embeddings array, valid file paths)
    """
    if not file_paths:
        return np.array([]), []

    cache = EmbeddingCache(vault_path, model_name)
    if not force:
        cache.load()

    to_embed = []
    file_hashes = {}
    embeddings_map = {}

    # Check which files need embedding
    for path in file_paths:
        content, file_hash = read_file_text_and_hash(path)
        if not file_hash:
            continue

        file_hashes[path] = file_hash

        if not force and cache.is_valid(path, file_hash):
            embeddings_map[path] = cache.get(path)
        else:
            to_embed.append((path, content))

    # Generate embeddings for files not in cache
    if to_embed:
        texts = [content for _, content in to_embed]
        embs = encode_texts(texts, model, batch_size, device, show_progress=True)

        for (path, _), emb in zip(to_embed, embs):
            embeddings_map[path] = {'hash': file_hashes[path], 'embedding': emb}
            cache.set(path, file_hashes[path], emb)

    # Save updated cache
    cache.save()

    # Build output arrays in original file order
    final_embeddings = []
    valid_paths = []

    for path in file_paths:
        if path in embeddings_map:
            final_embeddings.append(embeddings_map[path]['embedding'])
            valid_paths.append(path)

    return np.array(final_embeddings), valid_paths
