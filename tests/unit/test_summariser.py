"""Unit tests for the summariser: cache handling and request building (no Ollama calls)."""

from unittest.mock import MagicMock

import summariser_ollama
from metisem.core.database import CacheDatabase
from summariser_ollama import adopt_existing_summaries, build_generate_payload, detect_summary_changes


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


def _show_response(capabilities):
    response = MagicMock(status_code=200)
    response.json.return_value = {"capabilities": capabilities}
    return response


class TestBuildGeneratePayload:
    """The request must fix the context window and keep reasoning out of summaries."""

    def setup_method(self):
        summariser_ollama._thinking_support.clear()

    def test_sets_num_ctx_and_no_unknown_options(self, mocker):
        mocker.patch("summariser_ollama.requests.post", return_value=_show_response(["completion"]))

        payload = build_generate_payload("prompt", "mistral", 128)

        assert payload["options"]["num_ctx"] == summariser_ollama.NUM_CTX
        assert payload["options"]["num_ctx"] >= 16384
        assert "context_window" not in payload["options"]
        assert payload["options"]["num_predict"] == 512

    def test_disables_thinking_for_thinking_models(self, mocker):
        mocker.patch("summariser_ollama.requests.post", return_value=_show_response(["completion", "thinking"]))

        assert build_generate_payload("prompt", "qwen3.6", 128)["think"] is False

    def test_omits_think_for_other_models(self, mocker):
        mocker.patch("summariser_ollama.requests.post", return_value=_show_response(["completion"]))

        assert "think" not in build_generate_payload("prompt", "mistral", 128)

    def test_capability_lookup_failure_omits_think(self, mocker):
        mocker.patch("summariser_ollama.requests.post", side_effect=ConnectionError)

        assert "think" not in build_generate_payload("prompt", "mistral", 128)

    def test_capability_lookup_is_cached(self, mocker):
        post = mocker.patch("summariser_ollama.requests.post", return_value=_show_response(["thinking"]))

        build_generate_payload("a", "qwen3.6", 128)
        build_generate_payload("b", "qwen3.6", 128)

        assert post.call_count == 1
