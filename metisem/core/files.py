"""File discovery and hashing utilities.

This module provides unified utilities for finding markdown files and computing
content hashes for cache invalidation.
"""

import hashlib
import re
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

from .markers import LINK_SECTION_START, LINK_SECTION_END, SUMMARY_START, SUMMARY_END, remove_marker_block

# Version of the text preparation applied before embedding. Bump it whenever
# embedding_text() changes, so caches built from the old text are not reused.
EMBED_TEXT_VERSION = 2

_FRONT_MATTER = re.compile(r'\A---[ \t]*\n.*?\n---[ \t]*(?:\n|\Z)', re.DOTALL)


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


def strip_generated_content(content: str) -> str:
    """Remove YAML front matter and metisem's generated blocks from note text.

    Generated summary and link blocks are removed wherever they sit; front
    matter is removed from the top of the note, including where a summary block
    was placed above it or a second front matter block follows the first.
    """
    text = remove_marker_block(content, SUMMARY_START, SUMMARY_END)
    text = remove_marker_block(text, LINK_SECTION_START, LINK_SECTION_END)
    while True:
        stripped = text.lstrip()
        match = _FRONT_MATTER.match(stripped)
        if not match:
            break
        text = stripped[match.end():]
    return text.strip()


def embedding_text(content: str, use_summary: bool = False) -> str:
    """Text to embed for a note.

    Content embeddings use the note body only, so generated summaries, links and
    tags don't feed back into similarity. Summary embeddings use the summary
    block, falling back to the note body when there is no summary.
    """
    if use_summary:
        summary = extract_summary(content)
        if summary:
            return summary
    return strip_generated_content(content)


def read_embedding_text_and_hash(path: Path, use_summary: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """Read a note and return (text to embed, SHA256 of that text), or (None, None) on error."""
    try:
        text = embedding_text(path.read_text(encoding='utf-8'), use_summary)
    except Exception:
        return None, None
    return text, hashlib.sha256(text.encode('utf-8')).hexdigest()


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


def generate_title_from_summary(summary: str, max_length: int = 60) -> Optional[str]:
    """Generate a filename-safe title from a summary.

    Extracts the first sentence or key phrase, removes markdown formatting,
    sanitises for filename usage, and limits length.

    Args:
        summary: Summary text to extract title from
        max_length: Maximum length for generated title (default: 60)

    Returns:
        Cleaned title string, or None if summary is empty/invalid
    """
    if not summary or not summary.strip():
        return None

    # Remove markdown headers
    text = re.sub(r'^#+\s+', '', summary, flags=re.MULTILINE)

    # Remove markdown formatting (bold, italic, code)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Italic
    text = re.sub(r'`([^`]+)`', r'\1', text)        # Inline code
    text = re.sub(r'~~([^~]+)~~', r'\1', text)      # Strikethrough

    # Extract first sentence (up to . ! ? or newline)
    sentences = re.split(r'[.!?\n]', text)
    first_sentence = sentences[0].strip() if sentences else text.strip()

    if not first_sentence:
        return None

    # Remove invalid filename characters
    title = re.sub(r'[<>:"/\\|?*]', '', first_sentence)

    # Collapse multiple spaces
    title = re.sub(r'\s+', ' ', title)

    # Trim to max length at word boundary
    if len(title) > max_length:
        title = title[:max_length].rsplit(' ', 1)[0]

    # Remove trailing punctuation
    title = title.rstrip('.,;:-')

    return title.strip() if title.strip() else None


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


def detect_embedding_changes(
    current_files: List[Path],
    db,  # CacheDatabase instance
    cache_key: str,
    use_summary: bool = False
) -> ChangeSet:
    """Detect new, modified, deleted and unchanged files for one embedding cache.

    Like detect_file_changes, but reads the embedding_state table for cache_key
    and compares hashes of the embedded text rather than the whole file, so
    rewriting a note's generated blocks doesn't count as a change. When the
    mtime moved but the text didn't, the stored mtime is refreshed.
    """
    stored = {Path(p) for p in db.get_embedding_paths(cache_key)}
    new_files: List[Path] = []
    modified_files: List[Path] = []
    unchanged_files: List[Path] = []

    for file_path in current_files:
        state = db.get_embedding_state(file_path, cache_key)
        if state is None:
            new_files.append(file_path)
            continue
        try:
            mtime_ns = file_path.stat().st_mtime_ns
        except OSError:
            modified_files.append(file_path)
            continue
        if state['mtime_ns'] == mtime_ns:
            unchanged_files.append(file_path)
            continue
        _, text_hash = read_embedding_text_and_hash(file_path, use_summary)
        if text_hash and text_hash == state['text_hash']:
            db.set_embedding_state(file_path, cache_key, text_hash, mtime_ns, state['embedding_dim'])
            unchanged_files.append(file_path)
        else:
            modified_files.append(file_path)

    current = set(current_files)
    deleted_files = [p for p in stored if p not in current]
    return ChangeSet(
        new_files=new_files,
        modified_files=modified_files,
        deleted_files=deleted_files,
        unchanged_files=unchanged_files
    )
