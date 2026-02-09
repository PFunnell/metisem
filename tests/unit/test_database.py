"""Unit tests for metisem/core/database.py module.

Tests SQLite database operations for cache metadata and run logging.
"""

import time
import numpy as np
import pytest
from pathlib import Path

from metisem.core.database import CacheDatabase


class TestCacheDatabaseInit:
    """Tests for CacheDatabase initialization."""

    def test_creates_database_file(self, temp_database):
        """Should create database file on initialization."""
        db = CacheDatabase(temp_database)
        assert temp_database.exists()

    def test_creates_schema(self, temp_database):
        """Should create all required tables."""
        db = CacheDatabase(temp_database)
        conn = db._get_connection()

        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        expected_tables = {'file_metadata', 'tag_embeddings', 'metadata', 'run_logs'}
        assert expected_tables.issubset(tables)

    def test_creates_indices(self, temp_database):
        """Should create performance indices."""
        db = CacheDatabase(temp_database)
        conn = db._get_connection()

        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indices = {row[0] for row in cursor.fetchall()}

        expected_indices = {'idx_mtime', 'idx_model', 'idx_run_timestamp', 'idx_run_tool', 'idx_run_vault'}
        assert expected_indices.issubset(indices)

    def test_creates_parent_directories(self, tmp_path):
        """Should create parent directories if they don't exist."""
        nested_path = tmp_path / "level1" / "level2" / "test.db"
        db = CacheDatabase(nested_path)

        assert nested_path.exists()


class TestFileMetadata:
    """Tests for file metadata storage and retrieval."""

    def test_set_and_get_file_metadata(self, temp_database):
        """Should store and retrieve file metadata."""
        db = CacheDatabase(temp_database)

        file_path = Path("test.md")
        content_hash = "a" * 64
        mtime_ns = 1234567890000000000
        size_bytes = 1024
        model_name = "test-model"
        embedding_dim = 384

        db.set_file_metadata(file_path, content_hash, mtime_ns, size_bytes, model_name, embedding_dim)

        metadata = db.get_file_metadata(file_path)

        assert metadata is not None
        assert metadata['content_hash'] == content_hash
        assert metadata['mtime_ns'] == mtime_ns
        assert metadata['size_bytes'] == size_bytes
        assert metadata['model_name'] == model_name
        assert metadata['embedding_dim'] == embedding_dim

    def test_get_nonexistent_file_returns_none(self, temp_database):
        """Should return None for files not in database."""
        db = CacheDatabase(temp_database)

        metadata = db.get_file_metadata(Path("nonexistent.md"))

        assert metadata is None

    def test_update_existing_file_metadata(self, temp_database):
        """Should update metadata for existing file."""
        db = CacheDatabase(temp_database)

        file_path = Path("test.md")

        # Set initial metadata
        db.set_file_metadata(file_path, "hash1", 1000, 100, "model1", 384)

        # Update metadata
        db.set_file_metadata(file_path, "hash2", 2000, 200, "model2", 768)

        metadata = db.get_file_metadata(file_path)

        assert metadata['content_hash'] == "hash2"
        assert metadata['mtime_ns'] == 2000
        assert metadata['size_bytes'] == 200
        assert metadata['model_name'] == "model2"
        assert metadata['embedding_dim'] == 768

    def test_stores_updated_at_timestamp(self, temp_database):
        """Should store timestamp when metadata is updated."""
        db = CacheDatabase(temp_database)

        before = int(time.time())
        db.set_file_metadata(Path("test.md"), "hash", 1000, 100, "model", 384)
        after = int(time.time())

        metadata = db.get_file_metadata(Path("test.md"))

        assert metadata['updated_at'] >= before
        assert metadata['updated_at'] <= after


class TestFileMetadataList:
    """Tests for listing cached file paths."""

    def test_get_all_paths_for_model(self, temp_database):
        """Should return all file paths for specific model."""
        db = CacheDatabase(temp_database)

        # Add files for model1
        db.set_file_metadata(Path("file1.md"), "hash1", 1000, 100, "model1", 384)
        db.set_file_metadata(Path("file2.md"), "hash2", 2000, 200, "model1", 384)

        # Add file for model2
        db.set_file_metadata(Path("file3.md"), "hash3", 3000, 300, "model2", 768)

        paths = db.get_all_paths("model1")

        assert len(paths) == 2
        assert "file1.md" in paths
        assert "file2.md" in paths
        assert "file3.md" not in paths

    def test_get_all_paths_empty_model(self, temp_database):
        """Should return empty list for model with no files."""
        db = CacheDatabase(temp_database)

        paths = db.get_all_paths("nonexistent-model")

        assert paths == []


class TestRemoveFile:
    """Tests for removing file metadata."""

    def test_remove_file_from_database(self, temp_database):
        """Should delete file metadata from database."""
        db = CacheDatabase(temp_database)

        file_path = Path("test.md")
        db.set_file_metadata(file_path, "hash", 1000, 100, "model", 384)

        assert db.get_file_metadata(file_path) is not None

        db.remove_file(file_path)

        assert db.get_file_metadata(file_path) is None

    def test_remove_nonexistent_file_no_error(self, temp_database):
        """Should handle removing nonexistent file gracefully."""
        db = CacheDatabase(temp_database)

        # Should not raise error
        db.remove_file(Path("nonexistent.md"))


class TestTagEmbeddings:
    """Tests for tag embedding storage and retrieval."""

    def test_set_and_get_tag_embedding(self, temp_database):
        """Should store and retrieve tag embeddings."""
        db = CacheDatabase(temp_database)

        tag_name = "python"
        tag_description = "Programming language"
        content_hash = "a" * 64
        model_name = "test-model"
        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        db.set_tag_embedding(tag_name, tag_description, content_hash, model_name, embedding)

        cached = db.get_tag_embedding(tag_name, model_name)

        assert cached is not None
        assert cached['content_hash'] == content_hash
        np.testing.assert_array_almost_equal(cached['embedding'], embedding, decimal=6)

    def test_get_nonexistent_tag_returns_none(self, temp_database):
        """Should return None for tags not in database."""
        db = CacheDatabase(temp_database)

        cached = db.get_tag_embedding("nonexistent", "model")

        assert cached is None

    def test_update_existing_tag_embedding(self, temp_database):
        """Should update existing tag embedding."""
        db = CacheDatabase(temp_database)

        tag_name = "python"
        model_name = "test-model"

        old_embedding = np.array([1.0, 2.0], dtype=np.float32)
        new_embedding = np.array([3.0, 4.0], dtype=np.float32)

        db.set_tag_embedding(tag_name, "Old desc", "hash1", model_name, old_embedding)
        db.set_tag_embedding(tag_name, "New desc", "hash2", model_name, new_embedding)

        cached = db.get_tag_embedding(tag_name, model_name)

        assert cached['content_hash'] == "hash2"
        np.testing.assert_array_almost_equal(cached['embedding'], new_embedding, decimal=6)

    def test_different_models_store_separately(self, temp_database):
        """Should store different embeddings for different models."""
        db = CacheDatabase(temp_database)

        tag_name = "python"
        embedding1 = np.array([1.0, 2.0], dtype=np.float32)
        embedding2 = np.array([3.0, 4.0], dtype=np.float32)

        db.set_tag_embedding(tag_name, "Desc", "hash1", "model1", embedding1)
        db.set_tag_embedding(tag_name, "Desc", "hash2", "model2", embedding2)

        cached1 = db.get_tag_embedding(tag_name, "model1")
        cached2 = db.get_tag_embedding(tag_name, "model2")

        np.testing.assert_array_almost_equal(cached1['embedding'], embedding1, decimal=6)
        np.testing.assert_array_almost_equal(cached2['embedding'], embedding2, decimal=6)


class TestGenericMetadata:
    """Tests for generic key-value metadata storage."""

    def test_set_and_get_metadata(self, temp_database):
        """Should store and retrieve metadata values."""
        db = CacheDatabase(temp_database)

        db.set_metadata("version", "1.0.0")
        value = db.get_metadata("version")

        assert value == "1.0.0"

    def test_get_nonexistent_metadata_returns_none(self, temp_database):
        """Should return None for nonexistent keys."""
        db = CacheDatabase(temp_database)

        value = db.get_metadata("nonexistent")

        assert value is None

    def test_update_existing_metadata(self, temp_database):
        """Should update existing metadata values."""
        db = CacheDatabase(temp_database)

        db.set_metadata("version", "1.0.0")
        db.set_metadata("version", "2.0.0")

        value = db.get_metadata("version")

        assert value == "2.0.0"


class TestRunLogs:
    """Tests for run logging functionality."""

    def test_log_run(self, temp_database):
        """Should log tool execution run."""
        db = CacheDatabase(temp_database)

        run_data = {
            'run_id': 'test-run-001',
            'timestamp': int(time.time()),
            'tool_name': 'linker',
            'operation': 'apply-links',
            'vault_path': '/test/vault',
            'files_total': 100,
            'files_modified': 10,
            'files_new': 5,
            'files_unchanged': 85,
            'files_deleted': 0,
            'links_added': 50,
            'links_removed': 10,
            'tags_applied': None,
            'tags_removed': None,
            'summaries_added': None,
            'summaries_removed': None,
            'parameters': '{"similarity": 0.6}',
            'duration_seconds': 12.5,
            'embedding_time_seconds': 8.2,
            'cache_hit_ratio': 0.85,
            'status': 'success',
            'error_count': 0,
            'error_message': None,
            'model_name': 'all-MiniLM-L6-v2',
            'embedding_dim': 384,
        }

        db.log_run(run_data)

        # Verify logged
        runs = db.get_recent_runs(limit=1)
        assert len(runs) == 1
        assert runs[0]['run_id'] == 'test-run-001'
        assert runs[0]['tool_name'] == 'linker'

    def test_get_recent_runs(self, temp_database):
        """Should retrieve recent runs in reverse chronological order."""
        db = CacheDatabase(temp_database)

        # Log multiple runs
        for i in range(5):
            run_data = {
                'run_id': f'run-{i}',
                'timestamp': int(time.time()) + i,  # Increasing timestamps
                'tool_name': 'linker',
                'operation': 'apply',
                'vault_path': '/vault',
                'status': 'success',
            }
            db.log_run(run_data)

        runs = db.get_recent_runs(limit=3)

        assert len(runs) == 3
        # Most recent first
        assert runs[0]['run_id'] == 'run-4'
        assert runs[1]['run_id'] == 'run-3'
        assert runs[2]['run_id'] == 'run-2'

    def test_get_recent_runs_filter_by_vault(self, temp_database):
        """Should filter runs by vault path."""
        db = CacheDatabase(temp_database)

        # Log runs for different vaults
        for vault in ['vault1', 'vault2']:
            for i in range(3):
                run_data = {
                    'run_id': f'{vault}-run-{i}',
                    'timestamp': int(time.time()),
                    'tool_name': 'linker',
                    'operation': 'apply',
                    'vault_path': f'/test/{vault}',
                    'status': 'success',
                }
                db.log_run(run_data)

        runs = db.get_recent_runs(vault_path='/test/vault1')

        assert len(runs) == 3
        assert all('vault1' in run['run_id'] for run in runs)

    def test_get_recent_runs_filter_by_tool(self, temp_database):
        """Should filter runs by tool name."""
        db = CacheDatabase(temp_database)

        # Log runs for different tools
        for tool in ['linker', 'tagger', 'summariser']:
            run_data = {
                'run_id': f'{tool}-run',
                'timestamp': int(time.time()),
                'tool_name': tool,
                'operation': 'apply',
                'vault_path': '/vault',
                'status': 'success',
            }
            db.log_run(run_data)

        runs = db.get_recent_runs(tool_name='tagger')

        assert len(runs) == 1
        assert runs[0]['tool_name'] == 'tagger'


class TestSummaryMetadata:
    """Tests for summary metadata functionality."""

    def test_migrate_summary_schema(self, temp_database):
        """Should add summary columns to file_metadata table."""
        db = CacheDatabase(temp_database)

        # Run migration
        db.migrate_summary_schema()

        # Check columns exist
        conn = db._get_connection()
        cursor = conn.execute("PRAGMA table_info(file_metadata)")
        columns = [row[1] for row in cursor.fetchall()]

        assert 'has_summary' in columns
        assert 'summary_hash' in columns
        assert 'summary_text' in columns

    def test_migrate_summary_schema_idempotent(self, temp_database):
        """Should handle multiple migration calls safely."""
        db = CacheDatabase(temp_database)

        # Run migration twice
        db.migrate_summary_schema()
        db.migrate_summary_schema()

        # Should not error, columns should exist
        conn = db._get_connection()
        cursor = conn.execute("PRAGMA table_info(file_metadata)")
        columns = [row[1] for row in cursor.fetchall()]

        assert 'has_summary' in columns

    def test_set_summary_metadata_updates_existing(self, temp_database):
        """Should update summary metadata for existing file."""
        db = CacheDatabase(temp_database)
        db.migrate_summary_schema()

        file_path = Path("test.md")

        # Set initial file metadata
        db.set_file_metadata(file_path, "content_hash", 1000, 100, "model", 384)

        # Set summary metadata
        db.set_summary_metadata(file_path, "new_content_hash", "summary_hash", "Summary text")

        metadata = db.get_file_metadata(file_path)

        assert metadata['has_summary'] == 1
        assert metadata['summary_hash'] == "summary_hash"
        assert metadata['summary_text'] == "Summary text"
        assert metadata['content_hash'] == "new_content_hash"

    def test_set_summary_metadata_inserts_new(self, temp_database):
        """Should insert new record if file not in database."""
        db = CacheDatabase(temp_database)
        db.migrate_summary_schema()

        file_path = Path("new_file.md")

        # Set summary metadata without prior file metadata
        db.set_summary_metadata(file_path, "content_hash", "summary_hash", "Summary text")

        metadata = db.get_file_metadata(file_path)

        assert metadata is not None
        assert metadata['has_summary'] == 1
        assert metadata['summary_hash'] == "summary_hash"


class TestDatabaseConnection:
    """Tests for database connection management."""

    def test_close_connection(self, temp_database):
        """Should close database connection."""
        db = CacheDatabase(temp_database)

        # Use connection
        db.set_metadata("test", "value")

        # Close connection
        db.close()

        assert db._conn is None

    def test_reconnect_after_close(self, temp_database):
        """Should reconnect after closing."""
        db = CacheDatabase(temp_database)

        db.set_metadata("test", "value")
        db.close()

        # Should reconnect automatically
        value = db.get_metadata("test")

        assert value == "value"


class TestDatabaseEdgeCases:
    """Tests for edge cases and error handling."""

    def test_handles_special_characters_in_paths(self, temp_database):
        """Should handle file paths with special characters."""
        db = CacheDatabase(temp_database)

        special_path = Path("folder/file with spaces & symbols!.md")
        db.set_file_metadata(special_path, "hash", 1000, 100, "model", 384)

        metadata = db.get_file_metadata(special_path)

        assert metadata is not None
        assert metadata['content_hash'] == "hash"

    def test_handles_large_embeddings(self, temp_database):
        """Should handle large embedding vectors."""
        db = CacheDatabase(temp_database)

        large_embedding = np.random.randn(4096).astype(np.float32)
        db.set_tag_embedding("tag", "desc", "hash", "model", large_embedding)

        cached = db.get_tag_embedding("tag", "model")

        assert cached is not None
        assert len(cached['embedding']) == 4096
        np.testing.assert_array_almost_equal(cached['embedding'], large_embedding, decimal=6)

    def test_handles_unicode_in_metadata(self, temp_database):
        """Should handle Unicode characters in metadata."""
        db = CacheDatabase(temp_database)

        unicode_value = "Test with emoji 🚀 and accents café"
        db.set_metadata("unicode_key", unicode_value)

        value = db.get_metadata("unicode_key")

        assert value == unicode_value
