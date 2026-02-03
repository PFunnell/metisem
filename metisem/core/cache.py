"""Unified embedding cache system.

This module provides a consistent caching interface that unifies the .npy format
from main.py and .npz format from tagger.py. Designed for future migration to SQLite.
"""

import os
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from sentence_transformers import SentenceTransformer

from .files import read_file_text_and_hash, get_common_vault_path, detect_file_changes
from .embeddings import encode_texts, get_embedding_dimension
from .database import CacheDatabase

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """Manages embedding cache for a vault and model combination."""

    def __init__(self, vault_path: str, model_name: str, cache_dir: str = ".metisem"):
        """Initialize cache manager.

        Args:
            vault_path: Path to the markdown vault
            model_name: Name of the sentence transformer model
            cache_dir: Directory name for cache storage (relative to vault)
        """
        self.vault_path = Path(vault_path)
        self.model_name = model_name
        self.cache_dir = self.vault_path / cache_dir
        self.cache_file = self._get_cache_path()
        self._data: Dict[Path, Dict[str, Any]] = {}

        # Initialize SQLite database
        self.db = CacheDatabase(self.cache_dir / "metisem.db")
        self._migrate_if_needed()

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

    def _migrate_if_needed(self) -> None:
        """Auto-migrate legacy .npz cache to SQLite metadata."""
        # Check if we need migration
        db_exists = (self.cache_dir / "metisem.db").exists()
        npz_exists = self.cache_file.exists()

        if db_exists or not npz_exists:
            return  # Already migrated or no legacy cache

        logger.info("Migrating legacy cache to SQLite metadata...")
        try:
            # Load legacy cache
            data = np.load(self.cache_file, allow_pickle=True)
            if 'paths' in data and 'hashes' in data and 'embs' in data:
                paths = data['paths']
                hashes = data['hashes']
                embs = data['embs']

                # Populate database with metadata from files that still exist
                for path_str, file_hash, emb in zip(paths, hashes, embs):
                    path = Path(path_str)
                    try:
                        if path.exists():
                            stat = path.stat()
                            self.db.set_file_metadata(
                                path,
                                file_hash,
                                stat.st_mtime_ns,
                                stat.st_size,
                                self.model_name,
                                len(emb)
                            )
                    except (OSError, FileNotFoundError):
                        pass  # Skip files that no longer exist

                # Rename legacy cache as backup
                backup_path = self.cache_file.with_suffix('.npz.migrated')
                self.cache_file.rename(backup_path)
                logger.info(f"Migration complete. Legacy cache backed up to {backup_path.name}")

        except Exception as e:
            logger.warning(f"Migration failed: {e}. Starting fresh cache.")

    def remove_file(self, file_path: Path) -> None:
        """Remove file from cache.

        Args:
            file_path: Path to the file
        """
        if file_path in self._data:
            del self._data[file_path]
        self.db.remove_file(file_path)


def generate_embeddings(
    file_paths: List[Path],
    model: SentenceTransformer,
    model_name: str,
    batch_size: int,
    device: str,
    vault_path: str,
    force: bool = False
) -> Tuple[np.ndarray, List[Path], Dict[str, int]]:
    """Generate embeddings for files using cache with incremental processing.

    Args:
        file_paths: List of file paths to embed
        model: SentenceTransformer model instance
        model_name: Name of the model (for cache)
        batch_size: Batch size for encoding
        device: Device to use ('cpu' or 'cuda')
        vault_path: Path to the vault (for cache location)
        force: If True, ignore cache and regenerate all embeddings

    Returns:
        Tuple of (embeddings array, valid file paths, change stats dict)
    """
    if not file_paths:
        return np.array([]), [], {'new': 0, 'modified': 0, 'unchanged': 0, 'deleted': 0}

    cache = EmbeddingCache(vault_path, model_name)

    # Force mode: clear database and regenerate all
    if force:
        logger.info("Force mode: clearing cache and regenerating all embeddings")
        cache._data = {}
        # Clear all metadata for this model
        for path_str in cache.db.get_all_paths(model_name):
            cache.db.remove_file(Path(path_str))
        changes = None
    else:
        # Incremental mode: detect changes
        cache.load()
        changes = detect_file_changes(file_paths, cache.db, model_name)

        # Log change summary
        logger.info(
            f"Change detection: {len(changes.new_files)} new, "
            f"{len(changes.modified_files)} modified, "
            f"{len(changes.deleted_files)} deleted, "
            f"{len(changes.unchanged_files)} unchanged"
        )

        # Remove deleted files from cache
        for deleted_path in changes.deleted_files:
            cache.remove_file(deleted_path)

    to_embed = []
    file_hashes = {}
    embeddings_map = {}
    embedding_dim = None

    if force:
        # Force mode: embed all files
        for path in file_paths:
            content, file_hash = read_file_text_and_hash(path)
            if file_hash:
                file_hashes[path] = file_hash
                to_embed.append((path, content))
    else:
        # Incremental mode: load unchanged, embed new/modified
        for path in changes.unchanged_files:
            cached = cache.get(path)
            if cached:
                embeddings_map[path] = cached

        for path in changes.new_files + changes.modified_files:
            content, file_hash = read_file_text_and_hash(path)
            if file_hash:
                file_hashes[path] = file_hash
                to_embed.append((path, content))

    # Generate embeddings for files that need it
    if to_embed:
        logger.info(f"Generating embeddings for {len(to_embed)} files...")
        texts = [content for _, content in to_embed]
        embs = encode_texts(texts, model, batch_size, device, show_progress=True)

        if len(embs) > 0:
            embedding_dim = len(embs[0])

        for (path, _), emb in zip(to_embed, embs):
            embeddings_map[path] = {'hash': file_hashes[path], 'embedding': emb}
            cache.set(path, file_hashes[path], emb)

            # Update database metadata
            try:
                stat = path.stat()
                cache.db.set_file_metadata(
                    path,
                    file_hashes[path],
                    stat.st_mtime_ns,
                    stat.st_size,
                    model_name,
                    embedding_dim or len(emb)
                )
            except (OSError, FileNotFoundError):
                pass  # Skip metadata update if file disappeared

    # Save updated cache
    cache.save()

    # Build output arrays in original file order
    final_embeddings = []
    valid_paths = []

    for path in file_paths:
        if path in embeddings_map:
            final_embeddings.append(embeddings_map[path]['embedding'])
            valid_paths.append(path)

    # Build change stats
    if force:
        stats = {'new': len(to_embed), 'modified': 0, 'unchanged': 0, 'deleted': 0}
    else:
        stats = {
            'new': len(changes.new_files),
            'modified': len(changes.modified_files),
            'unchanged': len(changes.unchanged_files),
            'deleted': len(changes.deleted_files)
        }

    return np.array(final_embeddings), valid_paths, stats
