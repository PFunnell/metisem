"""Unit tests for summariser cache handling (no Ollama calls)."""

from metisem.core.database import CacheDatabase
from summariser_ollama import adopt_existing_summaries, detect_summary_changes


def _vault_db(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    db = CacheDatabase(vault / ".metisem" / "metisem.db")
    db.migrate_summary_schema()
    return vault, db


class TestAdoptExistingSummaries:
    """A vault copied from another machine must not have its summaries regenerated."""

    def test_adopts_file_with_summary_block(self, tmp_path):
        vault, db = _vault_db(tmp_path)
        note = vault / "note.md"
        note.write_text(
            "<!-- AUTO-GENERATED SUMMARY START -->\nExisting summary.\n<!-- AUTO-GENERATED SUMMARY END -->\n\nBody\n",
            encoding="utf-8",
        )

        adopted = adopt_existing_summaries([note], db)

        assert adopted == [note]
        assert detect_summary_changes([note], db).unchanged_files == [note]
        db.close()

    def test_leaves_file_without_summary_for_processing(self, tmp_path):
        vault, db = _vault_db(tmp_path)
        note = vault / "plain.md"
        note.write_text("Body only\n", encoding="utf-8")

        assert adopt_existing_summaries([note], db) == []
        assert detect_summary_changes([note], db).new_files == [note]
        db.close()
