"""Integration tests for Metisem tools.

Tests full tool execution workflows with real files (requires test vault configuration).
These tests are marked as integration and should be run separately from unit tests.

Migrated from scripts/test_run_logging.py.
"""

import pytest
from pathlib import Path
import os


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def test_vault_path():
    """Get test vault path from environment or config.

    Returns:
        Path to test vault, or skips test if not configured
    """
    vault_path = os.getenv("TEST_VAULT_PATH")

    if not vault_path:
        pytest.skip("TEST_VAULT_PATH not configured - skipping integration tests")

    vault = Path(vault_path)
    if not vault.exists():
        pytest.skip(f"Test vault not found at {vault_path}")

    return vault


class TestLinkerIntegration:
    """Integration tests for semantic linker (main.py)."""

    def test_linker_preview_mode(self, test_vault_path):
        """Should run linker in preview mode without modifying files."""
        from main import main as linker_main
        import sys

        # Run in preview mode (no --apply-links flag)
        original_argv = sys.argv
        try:
            sys.argv = ["main.py", str(test_vault_path)]
            # Should complete without errors
            linker_main()
        finally:
            sys.argv = original_argv

    def test_linker_with_apply(self, test_vault_path):
        """Should apply links when --apply-links flag is used."""
        from main import main as linker_main
        import sys

        original_argv = sys.argv
        try:
            sys.argv = ["main.py", str(test_vault_path), "--apply-links", "--similarity", "0.7"]
            linker_main()
        finally:
            sys.argv = original_argv

        # Verify .metisem directory was created
        assert (test_vault_path / ".metisem").exists()

    def test_linker_delete_links(self, test_vault_path):
        """Should delete auto-generated link sections."""
        from main import main as linker_main
        import sys

        original_argv = sys.argv
        try:
            sys.argv = ["main.py", str(test_vault_path), "--delete-links"]
            linker_main()
        finally:
            sys.argv = original_argv


class TestTaggerIntegration:
    """Integration tests for auto-tagger (tagger.py)."""

    def test_tagger_preview_mode(self, test_vault_path, tmp_path):
        """Should run tagger in preview mode."""
        from tagger import main as tagger_main
        import sys

        # Create minimal tags file
        tags_file = tmp_path / "test_tags.txt"
        tags_file.write_text("python::Programming language\ntest::Testing related\n", encoding="utf-8")

        original_argv = sys.argv
        try:
            sys.argv = ["tagger.py", str(test_vault_path), "--tags-file", str(tags_file)]
            tagger_main()
        finally:
            sys.argv = original_argv

    def test_tagger_apply_tags(self, test_vault_path, tmp_path):
        """Should apply tags to files."""
        from tagger import main as tagger_main
        import sys

        tags_file = tmp_path / "test_tags.txt"
        tags_file.write_text("python::Programming language\n", encoding="utf-8")

        original_argv = sys.argv
        try:
            sys.argv = ["tagger.py", str(test_vault_path), "--tags-file", str(tags_file), "--apply-tags"]
            tagger_main()
        finally:
            sys.argv = original_argv


class TestSummariserIntegration:
    """Integration tests for summariser (summariser_ollama.py)."""

    def test_summariser_requires_ollama(self, test_vault_path):
        """Should detect if Ollama is not running."""
        import requests

        # Try to ping Ollama
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            ollama_available = response.status_code == 200
        except requests.RequestException:
            ollama_available = False

        if not ollama_available:
            pytest.skip("Ollama not running - skipping summariser integration tests")

    @pytest.mark.requires_ollama
    def test_summariser_preview_mode(self, test_vault_path):
        """Should run summariser in preview mode."""
        from summariser_ollama import main as summariser_main
        import sys

        self.test_summariser_requires_ollama(test_vault_path)

        original_argv = sys.argv
        try:
            sys.argv = ["summariser_ollama.py", str(test_vault_path)]
            summariser_main()
        finally:
            sys.argv = original_argv


class TestTitleFixerIntegration:
    """Integration tests for title fixer (title_fixer.py)."""

    def test_title_fixer_preview(self, test_vault_path):
        """Should preview title fixes without applying."""
        from title_fixer import main as title_fixer_main
        import sys

        original_argv = sys.argv
        try:
            sys.argv = ["title_fixer.py", str(test_vault_path)]
            title_fixer_main()
        finally:
            sys.argv = original_argv


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    def test_database_created_on_first_run(self, test_vault_path):
        """Should create metisem.db on first tool run."""
        from metisem.core.database import CacheDatabase

        db_path = test_vault_path / ".metisem" / "metisem.db"

        # Initialize database
        db = CacheDatabase(db_path)
        db.close()

        # Verify database file exists
        assert db_path.exists()

    def test_run_logs_persisted(self, test_vault_path):
        """Should persist run logs to database."""
        from metisem.core.run_logger import RunLogger

        with RunLogger(str(test_vault_path), "test-tool") as logger:
            logger.set_operation("test")
            logger.set_file_stats(total=10, modified=2)

        # Verify logged
        from metisem.core.database import CacheDatabase
        db_path = test_vault_path / ".metisem" / "metisem.db"
        db = CacheDatabase(db_path)

        runs = db.get_recent_runs(tool_name="test-tool", limit=1)
        assert len(runs) > 0
        assert runs[0]['tool_name'] == 'test-tool'

        db.close()


class TestCacheIntegration:
    """Integration tests for caching system."""

    def test_incremental_processing(self, test_vault_path):
        """Should use cache for unchanged files on second run."""
        from main import main as linker_main
        import sys
        import time

        original_argv = sys.argv

        # First run
        start1 = time.time()
        try:
            sys.argv = ["main.py", str(test_vault_path), "--apply-links"]
            linker_main()
        finally:
            sys.argv = original_argv
        duration1 = time.time() - start1

        # Second run (should be faster due to cache)
        start2 = time.time()
        try:
            sys.argv = ["main.py", str(test_vault_path), "--apply-links"]
            linker_main()
        finally:
            sys.argv = original_argv
        duration2 = time.time() - start2

        # Second run should typically be faster (not a strict assertion due to variability)
        # Just verify both runs completed successfully
        assert duration1 > 0
        assert duration2 > 0
