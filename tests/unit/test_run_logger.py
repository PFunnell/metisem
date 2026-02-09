"""Unit tests for metisem/core/run_logger.py module.

Tests run logging context manager, parameter serialization, and status tracking.
"""

import json
import time
import pytest
from pathlib import Path

from metisem.core.run_logger import RunLogger


class TestRunLoggerInit:
    """Tests for RunLogger initialization."""

    def test_initializes_with_vault_and_tool(self, tmp_path):
        """Should initialize logger with vault path and tool name."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")

        assert logger.tool_name == "linker"
        assert str(vault_path.resolve()) in logger.vault_path
        assert logger.run_id is not None
        assert len(logger.run_id) > 0

    def test_generates_unique_run_ids(self, tmp_path):
        """Should generate unique run IDs for each logger instance."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger1 = RunLogger(str(vault_path), "linker")
        logger2 = RunLogger(str(vault_path), "linker")

        assert logger1.run_id != logger2.run_id

    def test_stores_start_time(self, tmp_path):
        """Should record start time on initialization."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        before = time.time()
        logger = RunLogger(str(vault_path), "linker")
        after = time.time()

        assert logger.start_time >= before
        assert logger.start_time <= after

    def test_initializes_metrics_dict(self, tmp_path):
        """Should initialize metrics with basic fields."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")

        assert 'run_id' in logger.metrics
        assert 'vault_path' in logger.metrics
        assert 'tool_name' in logger.metrics
        assert 'timestamp' in logger.metrics
        assert logger.metrics['status'] == 'in_progress'


class TestSetOperation:
    """Tests for set_operation method."""

    def test_sets_operation(self, tmp_path):
        """Should store operation type."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")
        logger.set_operation("apply-links")

        assert logger.metrics['operation'] == "apply-links"


class TestSetParameters:
    """Tests for set_parameters method."""

    def test_serializes_parameters_to_json(self, tmp_path):
        """Should serialize parameters dictionary to JSON string."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")

        params = {
            "similarity": 0.6,
            "max_links": 9,
            "model": "all-MiniLM-L6-v2",
        }
        logger.set_parameters(params)

        # Should be stored as JSON string
        assert 'parameters' in logger.metrics
        assert isinstance(logger.metrics['parameters'], str)

        # Should be valid JSON
        deserialized = json.loads(logger.metrics['parameters'])
        assert deserialized == params

    def test_handles_nested_parameters(self, tmp_path):
        """Should handle nested dictionary parameters."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")

        params = {
            "weights": {"title": 0.2, "content": 0.5, "summary": 0.3},
            "thresholds": [0.5, 0.6, 0.7],
        }
        logger.set_parameters(params)

        deserialized = json.loads(logger.metrics['parameters'])
        assert deserialized == params


class TestSetFileStats:
    """Tests for set_file_stats method."""

    def test_sets_file_statistics(self, tmp_path):
        """Should store file statistics."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")
        logger.set_file_stats(total=100, modified=10, new=5, unchanged=85, deleted=0)

        assert logger.metrics['files_total'] == 100
        assert logger.metrics['files_modified'] == 10
        assert logger.metrics['files_new'] == 5
        assert logger.metrics['files_unchanged'] == 85
        assert logger.metrics['files_deleted'] == 0

    def test_calculates_cache_hit_ratio(self, tmp_path):
        """Should calculate cache hit ratio from stats."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")
        logger.set_file_stats(total=100, unchanged=85)

        assert logger.metrics['cache_hit_ratio'] == 0.85

    def test_handles_zero_total_files(self, tmp_path):
        """Should handle zero total files without division error."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")
        logger.set_file_stats(total=0)

        assert logger.metrics['cache_hit_ratio'] == 0.0


class TestSetLinkStats:
    """Tests for set_link_stats method."""

    def test_sets_link_statistics(self, tmp_path):
        """Should store link statistics."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")
        logger.set_link_stats(added=50, removed=10)

        assert logger.metrics['links_added'] == 50
        assert logger.metrics['links_removed'] == 10


class TestSetTagStats:
    """Tests for set_tag_stats method."""

    def test_sets_tag_statistics(self, tmp_path):
        """Should store tag statistics."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "tagger")
        logger.set_tag_stats(applied=20, removed=5)

        assert logger.metrics['tags_applied'] == 20
        assert logger.metrics['tags_removed'] == 5


class TestSetSummaryStats:
    """Tests for set_summary_stats method."""

    def test_sets_summary_statistics(self, tmp_path):
        """Should store summary statistics."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "summariser")
        logger.set_summary_stats(added=30, removed=2)

        assert logger.metrics['summaries_added'] == 30
        assert logger.metrics['summaries_removed'] == 2


class TestSetModelInfo:
    """Tests for set_model_info method."""

    def test_sets_model_information(self, tmp_path):
        """Should store model name and embedding dimension."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")
        logger.set_model_info("all-MiniLM-L6-v2", embedding_dim=384)

        assert logger.metrics['model_name'] == "all-MiniLM-L6-v2"
        assert logger.metrics['embedding_dim'] == 384

    def test_handles_optional_embedding_dim(self, tmp_path):
        """Should handle None embedding dimension."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")
        logger.set_model_info("all-MiniLM-L6-v2")

        assert logger.metrics['model_name'] == "all-MiniLM-L6-v2"
        assert 'embedding_dim' not in logger.metrics


class TestSetEmbeddingTime:
    """Tests for set_embedding_time method."""

    def test_sets_embedding_time(self, tmp_path):
        """Should store embedding generation time."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")
        logger.set_embedding_time(12.5)

        assert logger.metrics['embedding_time_seconds'] == 12.5


class TestAddError:
    """Tests for add_error method."""

    def test_adds_error_message(self, tmp_path):
        """Should record error message."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")
        logger.add_error("Test error message")

        assert logger.metrics['error_count'] == 1
        assert logger.metrics['error_message'] == "Test error message"

    def test_increments_error_count(self, tmp_path):
        """Should increment error count for multiple errors."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")
        logger.add_error("Error 1")
        logger.add_error("Error 2")
        logger.add_error("Error 3")

        assert logger.metrics['error_count'] == 3

    def test_appends_multiple_error_messages(self, tmp_path):
        """Should append multiple error messages with separator."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")
        logger.add_error("Error 1")
        logger.add_error("Error 2")

        assert "Error 1" in logger.metrics['error_message']
        assert "Error 2" in logger.metrics['error_message']
        assert ";" in logger.metrics['error_message']


class TestComplete:
    """Tests for complete method."""

    def test_calculates_duration(self, tmp_path):
        """Should calculate run duration."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")
        start = logger.start_time

        time.sleep(0.01)  # Small delay

        logger.complete()

        assert logger.metrics['duration_seconds'] > 0
        assert logger.metrics['duration_seconds'] < 1.0  # Should be very short

    def test_sets_success_status(self, tmp_path):
        """Should set status to success by default."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")
        logger.complete()

        assert logger.metrics['status'] == 'success'

    def test_sets_custom_status(self, tmp_path):
        """Should accept custom status parameter."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")
        logger.complete(status='partial')

        assert logger.metrics['status'] == 'partial'

    def test_persists_to_database(self, tmp_path):
        """Should log run to database."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        logger = RunLogger(str(vault_path), "linker")
        logger.set_operation("apply")
        logger.complete()

        # Verify logged to database
        runs = logger.db.get_recent_runs(limit=1)
        assert len(runs) == 1
        assert runs[0]['tool_name'] == 'linker'


class TestContextManager:
    """Tests for context manager functionality."""

    def test_context_manager_normal_completion(self, tmp_path):
        """Should complete successfully when no exception."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        with RunLogger(str(vault_path), "linker") as logger:
            logger.set_operation("test")

        # Should have completed with success status
        runs = logger.db.get_recent_runs(limit=1)
        assert runs[0]['status'] == 'success'

    def test_context_manager_with_exception(self, tmp_path):
        """Should handle exceptions and set error status."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        with pytest.raises(ValueError):
            with RunLogger(str(vault_path), "linker") as logger:
                logger.set_operation("test")
                raise ValueError("Test error")

        # Should have logged error status
        runs = logger.db.get_recent_runs(limit=1)
        assert runs[0]['status'] == 'error'
        assert 'ValueError' in runs[0]['error_message']

    def test_context_manager_partial_status(self, tmp_path):
        """Should set partial status when errors recorded but no exception."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        with RunLogger(str(vault_path), "linker") as logger:
            logger.set_operation("test")
            logger.add_error("Non-fatal error")

        # Should have partial status
        runs = logger.db.get_recent_runs(limit=1)
        assert runs[0]['status'] == 'partial'

    def test_context_manager_duration_calculation(self, tmp_path):
        """Should calculate duration in context manager."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        with RunLogger(str(vault_path), "linker") as logger:
            logger.set_operation("test")
            time.sleep(0.01)

        runs = logger.db.get_recent_runs(limit=1)
        assert runs[0]['duration_seconds'] > 0


class TestEndToEndLogging:
    """End-to-end tests for complete logging workflow."""

    def test_full_logging_workflow(self, tmp_path):
        """Should log complete run with all metrics."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        with RunLogger(str(vault_path), "linker") as logger:
            logger.set_operation("apply-links")
            logger.set_parameters({"similarity": 0.6, "max_links": 9})
            logger.set_file_stats(total=100, modified=10, new=5, unchanged=85)
            logger.set_link_stats(added=50, removed=10)
            logger.set_model_info("all-MiniLM-L6-v2", 384)
            logger.set_embedding_time(8.2)

        # Verify all metrics logged
        runs = logger.db.get_recent_runs(limit=1)
        run = runs[0]

        assert run['tool_name'] == 'linker'
        assert run['operation'] == 'apply-links'
        assert run['files_total'] == 100
        assert run['links_added'] == 50
        assert run['model_name'] == 'all-MiniLM-L6-v2'
        assert run['embedding_dim'] == 384
        assert run['cache_hit_ratio'] == 0.85
        assert run['status'] == 'success'

        # Verify parameters JSON
        params = json.loads(run['parameters'])
        assert params['similarity'] == 0.6

    def test_multiple_tool_runs(self, tmp_path):
        """Should log multiple runs independently."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        # Run linker
        with RunLogger(str(vault_path), "linker") as logger:
            logger.set_operation("apply")

        # Run tagger
        with RunLogger(str(vault_path), "tagger") as logger:
            logger.set_operation("apply")

        # Run summariser
        with RunLogger(str(vault_path), "summariser") as logger:
            logger.set_operation("apply")

        # Verify all logged
        from metisem.core.database import CacheDatabase
        db = CacheDatabase(vault_path / ".metisem" / "metisem.db")

        linker_runs = db.get_recent_runs(tool_name="linker")
        tagger_runs = db.get_recent_runs(tool_name="tagger")
        summariser_runs = db.get_recent_runs(tool_name="summariser")

        assert len(linker_runs) == 1
        assert len(tagger_runs) == 1
        assert len(summariser_runs) == 1
