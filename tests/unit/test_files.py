"""Unit tests for metisem/core/files.py module.

Tests file discovery, content hashing, summary extraction, and change detection.
"""

import hashlib
from pathlib import Path
import pytest

from metisem.core.files import (
    find_markdown_files,
    read_file_text_and_hash,
    extract_summary,
    generate_title_from_summary,
    compute_file_hash,
    get_common_vault_path,
    ChangeSet,
    detect_file_changes,
)


class TestFindMarkdownFiles:
    """Tests for find_markdown_files function."""

    def test_finds_all_markdown_files(self, temp_vault):
        """Should discover all .md files in vault recursively."""
        files = find_markdown_files(str(temp_vault))
        filenames = {f.name for f in files}

        # Should find all sample files plus nested file
        expected = {
            "short_note.md",
            "medium_with_frontmatter.md",
            "long_detailed.md",
            "note_with_links.md",
            "note_with_summary.md",
            "empty.md",
            "malformed_frontmatter.md",
            "no_frontmatter.md",
            "unicode_content.md",
            "nested_note.md",  # In subfolder
        }
        assert filenames == expected

    def test_ignores_metisem_directory(self, temp_vault):
        """Should not discover files in .metisem directory."""
        files = find_markdown_files(str(temp_vault))
        file_paths = [str(f) for f in files]

        # None should be in .metisem directory
        assert not any(".metisem" in path for path in file_paths)

    def test_empty_directory(self, tmp_path):
        """Should return empty list for directory with no markdown files."""
        empty_vault = tmp_path / "empty_vault"
        empty_vault.mkdir()

        files = find_markdown_files(str(empty_vault))
        assert files == []

    def test_nested_directories(self, tmp_path):
        """Should find files in deeply nested directories."""
        vault = tmp_path / "vault"
        deep_dir = vault / "level1" / "level2" / "level3"
        deep_dir.mkdir(parents=True)

        (deep_dir / "deep_note.md").write_text("# Deep Note", encoding="utf-8")

        files = find_markdown_files(str(vault))
        assert len(files) == 1
        assert files[0].name == "deep_note.md"


class TestReadFileTextAndHash:
    """Tests for read_file_text_and_hash function."""

    def test_reads_normal_file(self, temp_vault):
        """Should read file content and compute correct hash."""
        file_path = temp_vault / "short_note.md"
        content, file_hash = read_file_text_and_hash(file_path)

        assert content is not None
        assert "Short Note" in content
        assert file_hash is not None
        assert len(file_hash) == 64  # SHA256 hex length

    def test_hash_is_deterministic(self, temp_vault):
        """Same content should produce same hash."""
        file_path = temp_vault / "short_note.md"

        content1, hash1 = read_file_text_and_hash(file_path)
        content2, hash2 = read_file_text_and_hash(file_path)

        assert hash1 == hash2
        assert content1 == content2

    def test_different_content_different_hash(self, tmp_path):
        """Different content should produce different hashes."""
        file1 = tmp_path / "file1.md"
        file2 = tmp_path / "file2.md"

        file1.write_text("Content A", encoding="utf-8")
        file2.write_text("Content B", encoding="utf-8")

        _, hash1 = read_file_text_and_hash(file1)
        _, hash2 = read_file_text_and_hash(file2)

        assert hash1 != hash2

    def test_empty_file(self, temp_vault):
        """Should handle empty files correctly."""
        file_path = temp_vault / "empty.md"
        content, file_hash = read_file_text_and_hash(file_path)

        assert content == ""
        assert file_hash is not None
        # Verify it's the hash of empty string
        expected_hash = hashlib.sha256(b"").hexdigest()
        assert file_hash == expected_hash

    def test_unicode_content(self, temp_vault):
        """Should handle Unicode characters correctly."""
        file_path = temp_vault / "unicode_content.md"
        content, file_hash = read_file_text_and_hash(file_path)

        assert content is not None
        assert "🚀" in content
        assert "café" in content
        assert file_hash is not None

    def test_nonexistent_file(self, tmp_path):
        """Should return None, None for nonexistent file."""
        nonexistent = tmp_path / "does_not_exist.md"
        content, file_hash = read_file_text_and_hash(nonexistent)

        assert content is None
        assert file_hash is None

    def test_use_summary_extracts_summary(self, temp_vault):
        """Should extract summary when use_summary=True."""
        file_path = temp_vault / "note_with_summary.md"
        content, file_hash = read_file_text_and_hash(file_path, use_summary=True)

        assert content is not None
        assert "Summary" in content
        # Should not contain the full content section
        assert "The actual note content" not in content

    def test_use_summary_fallback_to_full_content(self, temp_vault):
        """Should fall back to full content if no summary exists."""
        file_path = temp_vault / "short_note.md"
        content, file_hash = read_file_text_and_hash(file_path, use_summary=True)

        assert content is not None
        assert "Short Note" in content


class TestExtractSummary:
    """Tests for extract_summary function."""

    def test_extracts_summary_block(self):
        """Should extract content between AUTO-GENERATED SUMMARY markers."""
        content = """# Title

<!-- AUTO-GENERATED SUMMARY START -->
## Summary
This is the summary text.
<!-- AUTO-GENERATED SUMMARY END -->

Regular content here.
"""
        summary = extract_summary(content)
        assert summary is not None
        assert "Summary" in summary
        assert "This is the summary text" in summary
        assert "Regular content" not in summary

    def test_returns_none_when_no_summary(self):
        """Should return None when no summary block exists."""
        content = "# Title\n\nJust regular content."
        summary = extract_summary(content)
        assert summary is None

    def test_handles_case_insensitive_markers(self):
        """Should handle marker case variations."""
        content = """<!-- auto-generated summary start -->
Summary content
<!-- AUTO-GENERATED SUMMARY END -->"""
        summary = extract_summary(content)
        assert summary is not None
        assert "Summary content" in summary

    def test_handles_whitespace_in_markers(self):
        """Should handle extra whitespace in markers."""
        content = """<!--   AUTO-GENERATED SUMMARY START   -->
Summary content
<!--AUTO-GENERATED SUMMARY END-->"""
        summary = extract_summary(content)
        assert summary is not None

    def test_empty_summary_block_returns_none(self):
        """Should return None for empty summary block."""
        content = """<!-- AUTO-GENERATED SUMMARY START -->


<!-- AUTO-GENERATED SUMMARY END -->"""
        summary = extract_summary(content)
        assert summary is None


class TestGenerateTitleFromSummary:
    """Tests for generate_title_from_summary function."""

    def test_generates_simple_title(self):
        """Should generate title from first sentence."""
        summary = "This is a test summary. More content here."
        title = generate_title_from_summary(summary)
        assert title == "This is a test summary"

    def test_removes_markdown_headers(self):
        """Should remove markdown header markers."""
        summary = "## Summary\nThis is the actual summary content."
        title = generate_title_from_summary(summary)
        assert title == "Summary"

    def test_removes_markdown_formatting(self):
        """Should remove bold, italic, code formatting."""
        summary = "This is **bold** and *italic* and `code`."
        title = generate_title_from_summary(summary)
        assert "**" not in title
        assert "*" not in title
        assert "`" not in title
        assert "bold" in title

    def test_removes_invalid_filename_characters(self):
        """Should remove characters invalid for filenames."""
        summary = "Title with <invalid> characters: /\\|?*"
        title = generate_title_from_summary(summary)
        assert "<" not in title
        assert ">" not in title
        assert "/" not in title
        assert "\\" not in title

    def test_truncates_to_max_length(self):
        """Should truncate title at word boundary."""
        long_summary = "This is a very long summary " * 10
        title = generate_title_from_summary(long_summary, max_length=30)
        assert len(title) <= 30
        assert not title.endswith(" ")  # Should not end with space

    def test_returns_none_for_empty_summary(self):
        """Should return None for empty or whitespace-only summary."""
        assert generate_title_from_summary("") is None
        assert generate_title_from_summary("   ") is None
        assert generate_title_from_summary(None) is None

    def test_collapses_multiple_spaces(self):
        """Should collapse multiple spaces to single space."""
        summary = "Title    with    extra    spaces"
        title = generate_title_from_summary(summary)
        assert "    " not in title
        assert "with extra spaces" in title


class TestComputeFileHash:
    """Tests for compute_file_hash function."""

    def test_computes_hash(self, tmp_path):
        """Should compute SHA256 hash of file."""
        file_path = tmp_path / "test.md"
        content = "Test content"
        file_path.write_text(content, encoding="utf-8")

        file_hash = compute_file_hash(file_path)
        expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        assert file_hash == expected_hash

    def test_returns_none_for_nonexistent_file(self, tmp_path):
        """Should return None for nonexistent file."""
        nonexistent = tmp_path / "does_not_exist.md"
        file_hash = compute_file_hash(nonexistent)
        assert file_hash is None


class TestGetCommonVaultPath:
    """Tests for get_common_vault_path function."""

    def test_finds_common_parent(self, tmp_path):
        """Should find common parent directory."""
        vault = tmp_path / "vault"
        file1 = vault / "subdir1" / "file1.md"
        file2 = vault / "subdir2" / "file2.md"

        common = get_common_vault_path([file1, file2])
        assert common == vault

    def test_single_file_returns_parent(self, tmp_path):
        """Should return parent directory for single file."""
        vault = tmp_path / "vault"
        file1 = vault / "file1.md"

        common = get_common_vault_path([file1])
        # Note: os.path.commonpath returns the file path itself for single file
        assert str(common) == str(file1)

    def test_empty_list_returns_current_dir(self):
        """Should return current directory for empty list."""
        common = get_common_vault_path([])
        assert common == Path(".")


class TestDetectFileChanges:
    """Tests for detect_file_changes function."""

    def test_detects_new_files(self, temp_vault, temp_database):
        """Should identify files not in cache as new."""
        from metisem.core.database import CacheDatabase

        db = CacheDatabase(temp_database)
        model_name = "test-model"

        current_files = list(find_markdown_files(str(temp_vault)))
        changes = detect_file_changes(current_files, db, model_name)

        # All files should be new (empty cache)
        assert len(changes.new_files) == len(current_files)
        assert len(changes.modified_files) == 0
        assert len(changes.deleted_files) == 0
        assert len(changes.unchanged_files) == 0

    def test_detects_unchanged_files(self, temp_vault, temp_database):
        """Should identify files with matching mtime as unchanged."""
        from metisem.core.database import CacheDatabase

        db = CacheDatabase(temp_database)
        model_name = "test-model"

        # Get one file and cache it
        file_path = temp_vault / "short_note.md"
        content, file_hash = read_file_text_and_hash(file_path)
        stat = file_path.stat()

        db.set_file_metadata(
            file_path=file_path,
            content_hash=file_hash,
            mtime_ns=stat.st_mtime_ns,
            size_bytes=stat.st_size,
            model_name=model_name,
            embedding_dim=384,
        )

        # Detect changes
        changes = detect_file_changes([file_path], db, model_name)

        # File should be unchanged
        assert len(changes.unchanged_files) == 1
        assert changes.unchanged_files[0] == file_path

    def test_detects_modified_files(self, temp_vault, temp_database):
        """Should identify files with changed content as modified."""
        from metisem.core.database import CacheDatabase

        db = CacheDatabase(temp_database)
        model_name = "test-model"

        file_path = temp_vault / "short_note.md"

        # Cache original state
        content, file_hash = read_file_text_and_hash(file_path)
        stat = file_path.stat()
        db.set_file_metadata(
            file_path=file_path,
            content_hash=file_hash,
            mtime_ns=stat.st_mtime_ns,
            size_bytes=stat.st_size,
            model_name=model_name,
            embedding_dim=384,
        )

        # Modify file
        file_path.write_text("Modified content", encoding="utf-8")

        # Detect changes
        changes = detect_file_changes([file_path], db, model_name)

        # File should be detected as modified
        assert len(changes.modified_files) == 1
        assert changes.modified_files[0] == file_path

    def test_detects_deleted_files(self, temp_vault, temp_database):
        """Should identify cached files not in current set as deleted."""
        from metisem.core.database import CacheDatabase

        db = CacheDatabase(temp_database)
        model_name = "test-model"

        # Cache a file
        file_path = temp_vault / "short_note.md"
        content, file_hash = read_file_text_and_hash(file_path)
        stat = file_path.stat()
        db.set_file_metadata(
            file_path=file_path,
            content_hash=file_hash,
            mtime_ns=stat.st_mtime_ns,
            size_bytes=stat.st_size,
            model_name=model_name,
            embedding_dim=384,
        )

        # Detect changes with empty current file list
        changes = detect_file_changes([], db, model_name)

        # File should be detected as deleted
        assert len(changes.deleted_files) == 1
        assert changes.deleted_files[0] == file_path
