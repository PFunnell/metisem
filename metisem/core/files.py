"""File discovery and hashing utilities.

This module provides unified utilities for finding markdown files and computing
content hashes for cache invalidation.
"""

import hashlib
import re
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass


def find_markdown_files(vault_path: str) -> List[Path]:
    """Find all markdown files in the vault directory recursively.

    Args:
        vault_path: Path to the Obsidian vault

    Returns:
        List of Path objects for all .md files found
    """
    vault = Path(vault_path)
    return list(vault.rglob('*.md'))


def read_file_text_and_hash(path: Path, use_summary: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """Read file content and compute SHA256 hash.

    Args:
        path: Path to the file
        use_summary: If True, extract only summary block; falls back to full content if no summary

    Returns:
        Tuple of (content, hash) or (None, None) on error
    """
    try:
        content = path.read_text(encoding='utf-8')

        # Extract summary if requested
        if use_summary:
            summary = extract_summary(content)
            if summary:
                content = summary

        hasher = hashlib.sha256()
        hasher.update(content.encode('utf-8'))
        return content, hasher.hexdigest()
    except Exception:
        return None, None


def extract_summary(content: str) -> Optional[str]:
    """Extract auto-generated summary block from markdown content.

    Looks for:
    <!-- AUTO-GENERATED SUMMARY START -->
    summary content here
    <!-- AUTO-GENERATED SUMMARY END -->

    Args:
        content: Markdown file content

    Returns:
        Summary text if found, None otherwise
    """
    pattern = r'<!--\s*AUTO-GENERATED SUMMARY START\s*-->\s*(.*?)\s*<!--\s*AUTO-GENERATED SUMMARY END\s*-->'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

    if match:
        summary = match.group(1).strip()
        return summary if summary else None

    return None


def compute_file_hash(path: Path) -> Optional[str]:
    """Compute SHA256 hash of file content.

    Args:
        path: Path to the file

    Returns:
        SHA256 hash as hex string, or None on error
    """
    _, file_hash = read_file_text_and_hash(path)
    return file_hash


def get_common_vault_path(file_paths: List[Path]) -> Path:
    """Find the common parent directory for a list of files.

    Args:
        file_paths: List of file paths

    Returns:
        Path object representing the common parent directory
    """
    import os
    if not file_paths:
        return Path('.')

    common = os.path.commonpath([str(p) for p in file_paths])
    return Path(common)


@dataclass
class ChangeSet:
    """Results of change detection."""
    new_files: List[Path]
    modified_files: List[Path]
    deleted_files: List[Path]
    unchanged_files: List[Path]


def detect_file_changes(
    current_files: List[Path],
    db,  # CacheDatabase instance
    model_name: str
) -> ChangeSet:
    """Detect new, modified, deleted, and unchanged files.

    Uses a two-phase approach:
    1. Fast mtime scan to identify potential changes
    2. Hash verification only for mtime mismatches

    Args:
        current_files: List of current file paths in vault
        db: CacheDatabase instance
        model_name: Name of embedding model

    Returns:
        ChangeSet with categorized file lists
    """
    new_files = []
    modified_files = []
    unchanged_files = []

    # Get all cached paths for this model
    cached_paths_str = set(db.get_all_paths(model_name))
    cached_paths = {Path(p) for p in cached_paths_str}

    # Check each current file
    for file_path in current_files:
        if str(file_path) not in cached_paths_str:
            # Not in cache -> new file
            new_files.append(file_path)
        else:
            # In cache -> check if modified
            try:
                stat = file_path.stat()
                mtime_ns = stat.st_mtime_ns
                cached = db.get_file_metadata(file_path)

                if cached and cached['mtime_ns'] == mtime_ns:
                    # mtime unchanged -> file unchanged
                    unchanged_files.append(file_path)
                else:
                    # mtime changed -> verify with hash
                    current_hash = compute_file_hash(file_path)
                    if current_hash and cached and cached['content_hash'] == current_hash:
                        # Hash same despite mtime change -> unchanged (update mtime in cache)
                        unchanged_files.append(file_path)
                    else:
                        # Hash different -> modified
                        modified_files.append(file_path)
            except (OSError, FileNotFoundError):
                # File exists in current_files but can't stat -> treat as modified
                modified_files.append(file_path)

    # Files in cache but not in current set -> deleted
    current_paths = {file_path for file_path in current_files}
    deleted_files = [p for p in cached_paths if p not in current_paths]

    return ChangeSet(
        new_files=new_files,
        modified_files=modified_files,
        deleted_files=deleted_files,
        unchanged_files=unchanged_files
    )
