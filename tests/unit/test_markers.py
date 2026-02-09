"""Unit tests for metisem/core/markers.py module.

Tests HTML comment marker detection, removal, and replacement functionality.
"""

import pytest

from metisem.core.markers import (
    LINK_SECTION_START,
    LINK_SECTION_END,
    SUMMARY_START,
    SUMMARY_END,
    has_marker_block,
    remove_marker_block,
    replace_marker_block,
    append_marker_block,
    get_marker_pattern,
)


class TestHasMarkerBlock:
    """Tests for has_marker_block function."""

    def test_detects_existing_marker_block(self):
        """Should detect marker block when present."""
        content = """# Title

<!-- AUTO-GENERATED LINKS START -->
- [[note1]]
- [[note2]]
<!-- AUTO-GENERATED LINKS END -->

Content here.
"""
        assert has_marker_block(content, LINK_SECTION_START, LINK_SECTION_END)

    def test_returns_false_when_no_marker_block(self):
        """Should return False when marker block not present."""
        content = "# Title\n\nJust regular content."
        assert not has_marker_block(content, LINK_SECTION_START, LINK_SECTION_END)

    def test_detects_summary_marker_block(self):
        """Should detect summary marker blocks."""
        content = """<!-- AUTO-GENERATED SUMMARY START -->
## Summary
This is a summary.
<!-- AUTO-GENERATED SUMMARY END -->
"""
        assert has_marker_block(content, SUMMARY_START, SUMMARY_END)

    def test_handles_indented_markers(self):
        """Should detect markers with leading whitespace."""
        content = """# Title

    <!-- AUTO-GENERATED LINKS START -->
    - [[note1]]
    <!-- AUTO-GENERATED LINKS END -->
"""
        assert has_marker_block(content, LINK_SECTION_START, LINK_SECTION_END)

    def test_requires_both_markers(self):
        """Should return False if only start or end marker present."""
        content_start_only = "<!-- AUTO-GENERATED LINKS START -->\nContent"
        content_end_only = "Content\n<!-- AUTO-GENERATED LINKS END -->"

        assert not has_marker_block(content_start_only, LINK_SECTION_START, LINK_SECTION_END)
        assert not has_marker_block(content_end_only, LINK_SECTION_START, LINK_SECTION_END)


class TestRemoveMarkerBlock:
    """Tests for remove_marker_block function."""

    def test_removes_marker_block(self):
        """Should remove entire marker block including markers."""
        content = """# Title

<!-- AUTO-GENERATED LINKS START -->
- [[note1]]
- [[note2]]
<!-- AUTO-GENERATED LINKS END -->

Content after.
"""
        result = remove_marker_block(content, LINK_SECTION_START, LINK_SECTION_END)

        assert LINK_SECTION_START not in result
        assert LINK_SECTION_END not in result
        assert "note1" not in result
        assert "note2" not in result
        assert "Content after" in result

    def test_preserves_content_outside_markers(self):
        """Should preserve all content outside marker block."""
        content = """# Title

Content before.

<!-- AUTO-GENERATED LINKS START -->
- [[note1]]
<!-- AUTO-GENERATED LINKS END -->

Content after.
"""
        result = remove_marker_block(content, LINK_SECTION_START, LINK_SECTION_END)

        assert "# Title" in result
        assert "Content before" in result
        assert "Content after" in result

    def test_returns_unchanged_if_no_marker_block(self):
        """Should return content unchanged if no marker block exists."""
        content = "# Title\n\nJust regular content."
        result = remove_marker_block(content, LINK_SECTION_START, LINK_SECTION_END)

        assert result == content

    def test_removes_multiple_marker_blocks(self):
        """Should remove all occurrences of marker block."""
        content = """# Title

<!-- AUTO-GENERATED LINKS START -->
- [[note1]]
<!-- AUTO-GENERATED LINKS END -->

Middle content.

<!-- AUTO-GENERATED LINKS START -->
- [[note2]]
<!-- AUTO-GENERATED LINKS END -->
"""
        result = remove_marker_block(content, LINK_SECTION_START, LINK_SECTION_END)

        assert LINK_SECTION_START not in result
        assert LINK_SECTION_END not in result
        assert "note1" not in result
        assert "note2" not in result

    def test_removes_indented_markers(self):
        """Should remove markers with leading whitespace."""
        content = """# Title

    <!-- AUTO-GENERATED LINKS START -->
    - [[note1]]
    <!-- AUTO-GENERATED LINKS END -->
"""
        result = remove_marker_block(content, LINK_SECTION_START, LINK_SECTION_END)

        assert LINK_SECTION_START not in result
        assert "note1" not in result


class TestReplaceMarkerBlock:
    """Tests for replace_marker_block function."""

    def test_replaces_marker_block(self):
        """Should replace existing marker block with new content."""
        content = """# Title

<!-- AUTO-GENERATED LINKS START -->
- [[old1]]
- [[old2]]
<!-- AUTO-GENERATED LINKS END -->

Content after.
"""
        new_block = """<!-- AUTO-GENERATED LINKS START -->
- [[new1]]
- [[new2]]
- [[new3]]
<!-- AUTO-GENERATED LINKS END -->

"""

        result = replace_marker_block(content, LINK_SECTION_START, LINK_SECTION_END, new_block)

        assert "old1" not in result
        assert "old2" not in result
        assert "new1" in result
        assert "new2" in result
        assert "new3" in result
        assert "Content after" in result

    def test_replaces_summary_block(self):
        """Should replace summary marker blocks."""
        content = """<!-- AUTO-GENERATED SUMMARY START -->
Old summary
<!-- AUTO-GENERATED SUMMARY END -->

# Title
"""
        new_block = """<!-- AUTO-GENERATED SUMMARY START -->
New improved summary
<!-- AUTO-GENERATED SUMMARY END -->

"""

        result = replace_marker_block(content, SUMMARY_START, SUMMARY_END, new_block)

        assert "Old summary" not in result
        assert "New improved summary" in result

    def test_returns_unchanged_if_no_marker_block(self):
        """Should return content unchanged if no marker block to replace."""
        content = "# Title\n\nRegular content."
        new_block = "<!-- AUTO-GENERATED LINKS START -->\nNew\n<!-- AUTO-GENERATED LINKS END -->\n"

        result = replace_marker_block(content, LINK_SECTION_START, LINK_SECTION_END, new_block)

        assert result == content

    def test_preserves_surrounding_content(self):
        """Should preserve content before and after replaced block."""
        content = """Before content

<!-- AUTO-GENERATED LINKS START -->
Old
<!-- AUTO-GENERATED LINKS END -->

After content
"""
        new_block = """<!-- AUTO-GENERATED LINKS START -->
New
<!-- AUTO-GENERATED LINKS END -->

"""

        result = replace_marker_block(content, LINK_SECTION_START, LINK_SECTION_END, new_block)

        assert "Before content" in result
        assert "After content" in result
        assert "New" in result
        assert "Old" not in result


class TestAppendMarkerBlock:
    """Tests for append_marker_block function."""

    def test_appends_to_end(self):
        """Should append block to end of content."""
        content = "# Title\n\nExisting content."
        block = "\n\n<!-- AUTO-GENERATED LINKS START -->\n- [[note1]]\n<!-- AUTO-GENERATED LINKS END -->\n"

        result = append_marker_block(content, block)

        assert result.startswith("# Title")
        assert result.endswith("<!-- AUTO-GENERATED LINKS END -->\n")
        assert "note1" in result

    def test_strips_trailing_whitespace_from_content(self):
        """Should strip trailing whitespace before appending."""
        content = "# Title\n\nContent\n\n\n"
        block = "\n\n<!-- MARKER -->\n"

        result = append_marker_block(content, block)

        # Should not have excessive newlines between content and block
        assert "\n\n\n\n\n<!-- MARKER -->" not in result
        assert result == "# Title\n\nContent\n\n<!-- MARKER -->\n"

    def test_handles_empty_content(self):
        """Should handle appending to empty content."""
        content = ""
        block = "<!-- MARKER -->\nContent\n<!-- MARKER END -->\n"

        result = append_marker_block(content, block)

        assert result == block


class TestGetMarkerPattern:
    """Tests for get_marker_pattern function."""

    def test_returns_compiled_pattern(self):
        """Should return compiled regex pattern."""
        import re

        pattern = get_marker_pattern(LINK_SECTION_START, LINK_SECTION_END)

        assert isinstance(pattern, re.Pattern)

    def test_pattern_matches_marker_block(self):
        """Pattern should match valid marker blocks."""
        pattern = get_marker_pattern(LINK_SECTION_START, LINK_SECTION_END)

        content = """<!-- AUTO-GENERATED LINKS START -->
- [[note1]]
<!-- AUTO-GENERATED LINKS END -->
"""
        match = pattern.search(content)
        assert match is not None

    def test_pattern_handles_indentation(self):
        """Pattern should match indented markers."""
        pattern = get_marker_pattern(LINK_SECTION_START, LINK_SECTION_END)

        content = """    <!-- AUTO-GENERATED LINKS START -->
    - [[note1]]
    <!-- AUTO-GENERATED LINKS END -->
"""
        match = pattern.search(content)
        assert match is not None

    def test_pattern_is_multiline(self):
        """Pattern should work across multiple lines."""
        pattern = get_marker_pattern(SUMMARY_START, SUMMARY_END)

        content = """<!-- AUTO-GENERATED SUMMARY START -->
Line 1
Line 2
Line 3
<!-- AUTO-GENERATED SUMMARY END -->
"""
        match = pattern.search(content)
        assert match is not None

    def test_pattern_captures_entire_block(self):
        """Pattern should capture content between markers."""
        pattern = get_marker_pattern(LINK_SECTION_START, LINK_SECTION_END)

        content = """Before
<!-- AUTO-GENERATED LINKS START -->
- [[note1]]
- [[note2]]
<!-- AUTO-GENERATED LINKS END -->
After"""

        # Pattern should match the entire block
        result = pattern.sub("", content)
        assert result == "Before\nAfter"


class TestMarkerConstants:
    """Tests for marker constant definitions."""

    def test_link_markers_defined(self):
        """Link section markers should be defined."""
        assert LINK_SECTION_START == "<!-- AUTO-GENERATED LINKS START -->"
        assert LINK_SECTION_END == "<!-- AUTO-GENERATED LINKS END -->"

    def test_summary_markers_defined(self):
        """Summary markers should be defined."""
        assert SUMMARY_START == "<!-- AUTO-GENERATED SUMMARY START -->"
        assert SUMMARY_END == "<!-- AUTO-GENERATED SUMMARY END -->"

    def test_markers_are_html_comments(self):
        """All markers should be valid HTML comments."""
        markers = [LINK_SECTION_START, LINK_SECTION_END, SUMMARY_START, SUMMARY_END]

        for marker in markers:
            assert marker.startswith("<!--")
            assert marker.endswith("-->")


class TestNestedAndMalformedMarkers:
    """Tests for edge cases with nested or malformed markers."""

    def test_does_not_match_partial_markers(self):
        """Should not match incomplete marker pairs."""
        content = "<!-- AUTO-GENERATED LINKS START -->\nContent without end marker"

        assert not has_marker_block(content, LINK_SECTION_START, LINK_SECTION_END)

    def test_handles_similar_but_different_markers(self):
        """Should not confuse similar marker patterns."""
        content = """<!-- CUSTOM LINKS START -->
- [[note1]]
<!-- CUSTOM LINKS END -->
"""
        # Should not match AUTO-GENERATED markers
        assert not has_marker_block(content, LINK_SECTION_START, LINK_SECTION_END)

    def test_removes_only_matching_markers(self):
        """Should only remove blocks with matching markers."""
        content = """<!-- AUTO-GENERATED LINKS START -->
- [[link1]]
<!-- AUTO-GENERATED LINKS END -->

<!-- AUTO-GENERATED SUMMARY START -->
Summary content
<!-- AUTO-GENERATED SUMMARY END -->
"""
        # Remove only link markers
        result = remove_marker_block(content, LINK_SECTION_START, LINK_SECTION_END)

        assert LINK_SECTION_START not in result
        assert "link1" not in result
        # Summary markers should remain
        assert SUMMARY_START in result
        assert "Summary content" in result
