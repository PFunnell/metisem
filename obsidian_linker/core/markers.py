"""HTML comment markers for auto-generated content blocks.

This module provides constants and utilities for managing auto-generated sections
in markdown files using HTML comment delimiters.
"""

import re
from pathlib import Path
from typing import Optional

# --- Link Section Markers ---
LINK_SECTION_START = "<!-- AUTO-GENERATED LINKS START -->"
LINK_SECTION_END = "<!-- AUTO-GENERATED LINKS END -->"

# --- Summary Section Markers ---
SUMMARY_START = "<!-- AUTO-GENERATED SUMMARY START -->"
SUMMARY_END = "<!-- AUTO-GENERATED SUMMARY END -->"


def has_marker_block(content: str, start_marker: str, end_marker: str) -> bool:
    """Check if content contains a marker block."""
    start_escaped = re.escape(start_marker)
    end_escaped = re.escape(end_marker)
    pattern = re.compile(
        rf"^[ \t]*{start_escaped}[ \t]*$.*?^[ \t]*{end_escaped}[ \t]*$",
        flags=re.MULTILINE | re.DOTALL
    )
    return bool(pattern.search(content))


def remove_marker_block(content: str, start_marker: str, end_marker: str) -> str:
    """Remove a marker block from content. Returns modified content."""
    start_escaped = re.escape(start_marker)
    end_escaped = re.escape(end_marker)
    pattern = re.compile(
        rf"^[ \t]*{start_escaped}[ \t]*$.*?^[ \t]*{end_escaped}[ \t]*$\n?",
        flags=re.MULTILINE | re.DOTALL
    )
    return pattern.sub('', content)


def replace_marker_block(content: str, start_marker: str, end_marker: str, new_block: str) -> str:
    """Replace existing marker block with new content. Returns modified content."""
    start_escaped = re.escape(start_marker)
    end_escaped = re.escape(end_marker)
    pattern = re.compile(
        rf"^[ \t]*{start_escaped}[ \t]*$.*?^[ \t]*{end_escaped}[ \t]*$\n?",
        flags=re.MULTILINE | re.DOTALL
    )
    return pattern.sub(new_block, content)


def append_marker_block(content: str, block: str) -> str:
    """Append a marker block to the end of content. Returns modified content."""
    return content.rstrip() + block


def get_marker_pattern(start_marker: str, end_marker: str) -> re.Pattern:
    """Get compiled regex pattern for a marker block."""
    start_escaped = re.escape(start_marker)
    end_escaped = re.escape(end_marker)
    return re.compile(
        rf"^[ \t]*{start_escaped}[ \t]*$.*?^[ \t]*{end_escaped}[ \t]*$\n?",
        flags=re.MULTILINE | re.DOTALL
    )
