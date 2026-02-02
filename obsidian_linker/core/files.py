"""File discovery and hashing utilities.

This module provides unified utilities for finding markdown files and computing
content hashes for cache invalidation.
"""

import hashlib
from pathlib import Path
from typing import List, Tuple, Optional


def find_markdown_files(vault_path: str) -> List[Path]:
    """Find all markdown files in the vault directory recursively.

    Args:
        vault_path: Path to the Obsidian vault

    Returns:
        List of Path objects for all .md files found
    """
    vault = Path(vault_path)
    return list(vault.rglob('*.md'))


def read_file_text_and_hash(path: Path) -> Tuple[Optional[str], Optional[str]]:
    """Read file content and compute SHA256 hash.

    Args:
        path: Path to the file

    Returns:
        Tuple of (content, hash) or (None, None) on error
    """
    try:
        content = path.read_text(encoding='utf-8')
        hasher = hashlib.sha256()
        hasher.update(content.encode('utf-8'))
        return content, hasher.hexdigest()
    except Exception:
        return None, None


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
