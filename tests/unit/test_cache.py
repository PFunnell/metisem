"""Unit tests for metisem/core/cache.py module.

Tests embedding cache save/load, invalidation, and migration functionality.
"""

import numpy as np
import pytest
from pathlib import Path

from metisem.core.cache import EmbeddingCache


class TestEmbeddingCacheInit:
    """Tests for EmbeddingCache initialization."""

    def test_initializes_with_vault_and_model(self, tmp_path):
        """Should initialize cache with vault path and model name."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")

        assert cache.vault_path == vault_path
        assert cache.model_name == "test-model"
        assert cache.cache_dir == vault_path / ".metisem"

    def test_creates_cache_path_from_vault_and_model(self, tmp_path):
        """Should generate cache file path based on vault and model names."""
        vault_path = tmp_path / "test_vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "sentence-transformers/all-MiniLM-L6-v2")

        # Model slashes should be replaced with underscores
        assert "test_vault" in str(cache.cache_file)
        assert "sentence-transformers_all-MiniLM-L6-v2" in str(cache.cache_file)
        assert cache.cache_file.suffix == ".npz"

    def test_custom_cache_directory(self, tmp_path):
        """Should allow custom cache directory name."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model", cache_dir=".custom_cache")

        assert cache.cache_dir == vault_path / ".custom_cache"


class TestEmbeddingCacheGetSet:
    """Tests for cache get/set operations."""

    def test_set_and_get_embedding(self, tmp_path):
        """Should store and retrieve embedding."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")

        file_path = Path("test.md")
        file_hash = "a" * 64
        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        cache.set(file_path, file_hash, embedding)
        cached = cache.get(file_path)

        assert cached is not None
        assert cached['hash'] == file_hash
        np.testing.assert_array_equal(cached['embedding'], embedding)

    def test_get_nonexistent_returns_none(self, tmp_path):
        """Should return None for files not in cache."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")

        cached = cache.get(Path("nonexistent.md"))

        assert cached is None

    def test_overwrite_existing_cache_entry(self, tmp_path):
        """Should overwrite existing cache entry when set again."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")

        file_path = Path("test.md")
        old_embedding = np.array([1.0, 2.0], dtype=np.float32)
        new_embedding = np.array([3.0, 4.0], dtype=np.float32)

        cache.set(file_path, "hash1", old_embedding)
        cache.set(file_path, "hash2", new_embedding)

        cached = cache.get(file_path)

        assert cached['hash'] == "hash2"
        np.testing.assert_array_equal(cached['embedding'], new_embedding)


class TestEmbeddingCacheSaveLoad:
    """Tests for cache save/load operations."""

    def test_save_and_load_cache(self, tmp_path, sample_embeddings, sample_file_hashes):
        """Should save cache to disk and load it back."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        # Create cache and add entries
        cache = EmbeddingCache(str(vault_path), "test-model")

        for i, (filename, file_hash) in enumerate(sample_file_hashes.items()):
            cache.set(Path(filename), file_hash, sample_embeddings[i])

        # Save cache
        cache.save()

        # Create new cache instance and load
        cache2 = EmbeddingCache(str(vault_path), "test-model")
        cache2.load()

        # Verify all entries loaded correctly
        for filename, file_hash in sample_file_hashes.items():
            cached = cache2.get(Path(filename))
            assert cached is not None
            assert cached['hash'] == file_hash

    def test_load_nonexistent_cache_returns_empty(self, tmp_path):
        """Should handle loading nonexistent cache file gracefully."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")
        cache.load()

        # Should have empty data
        assert len(cache._data) == 0

    def test_save_creates_cache_directory(self, tmp_path):
        """Should create cache directory if it doesn't exist."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")

        # Cache directory exists (created during __init__ for database)
        # But cache.npz file shouldn't exist yet
        assert not cache.cache_file.exists()

        # Add entry and save
        cache.set(Path("test.md"), "hash", np.array([1.0, 2.0], dtype=np.float32))
        cache.save()

        # Cache file should now exist
        assert cache.cache_dir.exists()
        assert cache.cache_file.exists()

    def test_save_empty_cache_no_op(self, tmp_path):
        """Should not create cache file when saving empty cache."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")
        cache.save()

        # Cache file should not be created
        assert not cache.cache_file.exists()

    def test_preserves_embedding_precision(self, tmp_path):
        """Should preserve float32 precision during save/load."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")

        embedding = np.array([0.123456789, -0.987654321], dtype=np.float32)
        cache.set(Path("test.md"), "hash", embedding)
        cache.save()

        cache2 = EmbeddingCache(str(vault_path), "test-model")
        cache2.load()

        loaded = cache2.get(Path("test.md"))
        np.testing.assert_array_almost_equal(loaded['embedding'], embedding, decimal=6)


class TestEmbeddingCacheIsValid:
    """Tests for cache validation."""

    def test_is_valid_with_matching_hash(self, tmp_path):
        """Should return True when cached hash matches current hash."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")

        file_path = Path("test.md")
        file_hash = "a" * 64
        embedding = np.array([1.0, 2.0], dtype=np.float32)

        cache.set(file_path, file_hash, embedding)

        assert cache.is_valid(file_path, file_hash)

    def test_is_valid_with_different_hash(self, tmp_path):
        """Should return False when cached hash doesn't match."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")

        file_path = Path("test.md")
        old_hash = "a" * 64
        new_hash = "b" * 64
        embedding = np.array([1.0, 2.0], dtype=np.float32)

        cache.set(file_path, old_hash, embedding)

        assert not cache.is_valid(file_path, new_hash)

    def test_is_valid_for_nonexistent_entry(self, tmp_path):
        """Should return False for files not in cache."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")

        assert not cache.is_valid(Path("nonexistent.md"), "somehash")


class TestEmbeddingCacheRemoveFile:
    """Tests for removing files from cache."""

    def test_remove_file_from_cache(self, tmp_path):
        """Should remove file from cache data."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")

        file_path = Path("test.md")
        cache.set(file_path, "hash", np.array([1.0, 2.0], dtype=np.float32))

        assert cache.get(file_path) is not None

        cache.remove_file(file_path)

        assert cache.get(file_path) is None

    def test_remove_nonexistent_file_no_error(self, tmp_path):
        """Should handle removing nonexistent file gracefully."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")

        # Should not raise error
        cache.remove_file(Path("nonexistent.md"))


class TestEmbeddingCacheLegacyMigration:
    """Tests for legacy .npy format migration."""

    def test_loads_legacy_npz_format(self, tmp_path, sample_embeddings, sample_file_hashes):
        """Should load legacy npz format with paths/hashes/embs keys."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        cache_dir = vault_path / ".metisem"
        cache_dir.mkdir()

        # Create legacy npz file
        paths = np.array(list(sample_file_hashes.keys()))
        hashes = np.array(list(sample_file_hashes.values()))
        embs = sample_embeddings

        cache_file = cache_dir / "embeddings_vault_test-model.npz"
        np.savez(cache_file, paths=paths, hashes=hashes, embs=embs)

        # Load with cache class
        cache = EmbeddingCache(str(vault_path), "test-model")
        cache.load()

        # Verify data loaded correctly
        for filename, file_hash in sample_file_hashes.items():
            cached = cache.get(Path(filename))
            assert cached is not None
            assert cached['hash'] == file_hash

    def test_handles_corrupted_cache_gracefully(self, tmp_path):
        """Should handle corrupted cache file by returning empty cache."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        cache_dir = vault_path / ".metisem"
        cache_dir.mkdir()

        # Create corrupted cache file
        cache_file = cache_dir / "embeddings_vault_test-model.npz"
        cache_file.write_text("corrupted data", encoding="utf-8")

        # Should load empty cache without crashing
        cache = EmbeddingCache(str(vault_path), "test-model")
        cache.load()

        assert len(cache._data) == 0

    def test_handles_missing_cache_directory(self, tmp_path):
        """Should handle missing cache directory gracefully."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        # Don't create .metisem directory
        cache = EmbeddingCache(str(vault_path), "test-model")
        cache.load()

        assert len(cache._data) == 0


class TestEmbeddingCacheMultipleFiles:
    """Tests for caching multiple files."""

    def test_caches_multiple_files(self, tmp_path):
        """Should handle caching embeddings for multiple files."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")

        files = [f"note{i}.md" for i in range(10)]

        for i, filename in enumerate(files):
            file_path = Path(filename)
            file_hash = f"hash{i}" * 8  # 64 char hash
            embedding = np.random.randn(384).astype(np.float32)
            cache.set(file_path, file_hash, embedding)

        # Verify all cached
        for filename in files:
            assert cache.get(Path(filename)) is not None

    def test_round_trip_with_many_files(self, tmp_path):
        """Should correctly save and load cache with many files."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")

        # Add 50 files
        test_data = {}
        for i in range(50):
            file_path = Path(f"note{i}.md")
            file_hash = f"{i:064d}"  # 64 char hash
            embedding = np.random.randn(384).astype(np.float32)
            cache.set(file_path, file_hash, embedding)
            test_data[file_path] = (file_hash, embedding)

        cache.save()

        # Load in new instance
        cache2 = EmbeddingCache(str(vault_path), "test-model")
        cache2.load()

        # Verify all entries
        for file_path, (file_hash, embedding) in test_data.items():
            cached = cache2.get(file_path)
            assert cached is not None
            assert cached['hash'] == file_hash
            np.testing.assert_array_almost_equal(cached['embedding'], embedding, decimal=6)


class TestEmbeddingCacheVaultMove:
    """The embedding cache survives moving the vault to another folder or OS."""

    def test_saves_vault_relative_keys(self, tmp_path):
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        cache = EmbeddingCache(str(vault_path), "test-model")
        cache.set(vault_path / "sub" / "a.md", "h", np.array([1.0], dtype=np.float32))
        cache.save()

        data = np.load(cache.cache_file, allow_pickle=True)

        assert list(data['paths']) == ["sub/a.md"]

    def test_loads_windows_absolute_keys_into_moved_vault(self, tmp_path):
        """Keys written on Windows are found after the vault is copied elsewhere."""
        vault_path = tmp_path / "GPT2025"
        cache_dir = vault_path / ".metisem"
        cache_dir.mkdir(parents=True)
        np.savez(
            cache_dir / "embeddings_GPT2025_test-model.npz",
            paths=np.array([r"D:\Obsidian\GPT2025\sub\a.md"]),
            hashes=np.array(["h"]),
            embs=np.array([[1.0, 2.0]], dtype=np.float32),
        )

        cache = EmbeddingCache(str(vault_path), "test-model")
        cache.load()

        assert cache.get(vault_path / "sub" / "a.md")['hash'] == "h"

    def test_copied_vault_reuses_every_embedding(self, tmp_path, mock_embedding_model):
        """Copying the whole vault (with .metisem/, without preserved mtimes) re-embeds nothing."""
        import shutil
        from metisem.core.cache import generate_embeddings
        from metisem.core.files import find_markdown_files

        original = tmp_path / "machine_a" / "Vault"
        (original / "sub").mkdir(parents=True)
        (original / "a.md").write_text("Alpha note", encoding="utf-8")
        (original / "sub" / "b.md").write_text("Beta note", encoding="utf-8")
        generate_embeddings(find_markdown_files(str(original)), mock_embedding_model, "m", 8, "cpu", str(original))

        moved = tmp_path / "machine_b" / "Vault"
        shutil.copytree(original, moved, copy_function=shutil.copy)  # copy drops mtimes
        shutil.rmtree(original)

        files = find_markdown_files(str(moved))
        embs, valid, stats = generate_embeddings(files, mock_embedding_model, "m", 8, "cpu", str(moved))

        assert stats == {'new': 0, 'modified': 0, 'unchanged': 2, 'deleted': 0}
        assert len(valid) == 2 and embs.shape[0] == 2


class TestEmbeddingCachePathHandling:
    """Tests for path handling in cache."""

    def test_handles_absolute_paths(self, tmp_path):
        """Should handle absolute file paths."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")

        abs_path = vault_path / "test.md"
        cache.set(abs_path, "hash", np.array([1.0, 2.0], dtype=np.float32))

        cached = cache.get(abs_path)
        assert cached is not None

    def test_handles_relative_paths(self, tmp_path):
        """Should handle relative file paths."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")

        rel_path = Path("subfolder/test.md")
        cache.set(rel_path, "hash", np.array([1.0, 2.0], dtype=np.float32))

        cached = cache.get(rel_path)
        assert cached is not None

    def test_path_consistency_after_round_trip(self, tmp_path):
        """Paths should remain consistent after save/load."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        cache = EmbeddingCache(str(vault_path), "test-model")

        original_path = Path("folder/subfolder/test.md")
        cache.set(original_path, "hash", np.array([1.0, 2.0], dtype=np.float32))
        cache.save()

        cache2 = EmbeddingCache(str(vault_path), "test-model")
        cache2.load()

        # Path should be retrievable
        cached = cache2.get(original_path)
        assert cached is not None
