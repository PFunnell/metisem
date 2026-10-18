"""SQLite database for cache metadata and tag embeddings.

This module provides persistent storage for file metadata (hashes, mtimes) and
tag embeddings, enabling fast incremental processing.
"""

import re
import sqlite3
import time
from pathlib import Path
from typing import Optional, Dict, Any, Iterable, List
import numpy as np

# Absolute path written by an older version or another OS: POSIX root, Windows drive or UNC share
_ABSOLUTE_KEY = re.compile(r'^(/|[A-Za-z]:[\\/]|\\\\)')


def is_absolute_key(key: str) -> bool:
    """Return True if a stored cache key is an absolute path from any OS."""
    return bool(_ABSOLUTE_KEY.match(key))


def vault_key(file_path: Path, vault_root: Path) -> str:
    """Storage key for a file: its path relative to the vault, in POSIX form.

    Accepts paths in the form the tools find them (absolute, or relative under a
    relative vault argument) and paths that are already vault-relative. Absolute
    paths outside the vault are returned unchanged.
    """
    p = Path(file_path)
    root = Path(vault_root)
    if p.is_absolute():
        try:
            return p.relative_to(root.absolute()).as_posix()
        except ValueError:
            return str(p)
    try:
        return p.relative_to(root).as_posix()
    except ValueError:
        return p.as_posix()


def legacy_key_to_relative(key: str, known_roots: Iterable[str], vault_name: str) -> Optional[str]:
    """Convert an absolute cache key from an older cache to a vault-relative POSIX key.

    Works across operating systems, so a cache written on Windows
    (D:\\Vault\\a.md) can be reused after the vault is copied to macOS.

    Args:
        key: Stored absolute path string
        known_roots: Vault root paths the cache may have been written under
        vault_name: Folder name of the vault, used when no root matches

    Returns:
        Vault-relative POSIX path, or None if the key can't be placed in the vault
    """
    norm = key.replace('\\', '/')
    for root in known_roots:
        root_norm = root.replace('\\', '/').rstrip('/')
        if root_norm and norm.lower().startswith(root_norm.lower() + '/'):
            return norm[len(root_norm) + 1:]
    parts = norm.split('/')
    if vault_name in parts[:-1]:
        return '/'.join(parts[parts.index(vault_name) + 1:])
    return None


class CacheDatabase:
    """SQLite store for file metadata and cache management."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS file_metadata (
        file_path TEXT PRIMARY KEY,
        content_hash TEXT NOT NULL,
        mtime_ns INTEGER NOT NULL,
        size_bytes INTEGER NOT NULL,
        model_name TEXT NOT NULL,
        embedding_dim INTEGER NOT NULL,
        updated_at INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_mtime ON file_metadata(mtime_ns);
    CREATE INDEX IF NOT EXISTS idx_model ON file_metadata(model_name);

    CREATE TABLE IF NOT EXISTS tag_embeddings (
        tag_name TEXT NOT NULL,
        tag_description TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        model_name TEXT NOT NULL,
        embedding_blob BLOB NOT NULL,
        updated_at INTEGER NOT NULL,
        PRIMARY KEY (tag_name, model_name)
    );

    CREATE TABLE IF NOT EXISTS metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS run_logs (
        run_id TEXT PRIMARY KEY,
        timestamp INTEGER NOT NULL,
        tool_name TEXT NOT NULL,
        operation TEXT NOT NULL,
        vault_path TEXT NOT NULL,

        files_total INTEGER,
        files_modified INTEGER,
        files_new INTEGER,
        files_unchanged INTEGER,
        files_deleted INTEGER,

        links_added INTEGER,
        links_removed INTEGER,
        tags_applied INTEGER,
        tags_removed INTEGER,
        summaries_added INTEGER,
        summaries_removed INTEGER,

        parameters TEXT,

        duration_seconds REAL,
        embedding_time_seconds REAL,
        cache_hit_ratio REAL,

        status TEXT,
        error_count INTEGER,
        error_message TEXT,

        model_name TEXT,
        embedding_dim INTEGER
    );
    CREATE INDEX IF NOT EXISTS idx_run_timestamp ON run_logs(timestamp);
    CREATE INDEX IF NOT EXISTS idx_run_tool ON run_logs(tool_name);
    CREATE INDEX IF NOT EXISTS idx_run_vault ON run_logs(vault_path);
    """

    def __init__(self, db_path: Path, vault_root: Optional[Path] = None):
        """Initialize database connection.

        File paths are stored relative to the vault root, so the cache survives
        moving the vault to another folder or machine.

        Args:
            db_path: Path to SQLite database file
            vault_root: Vault the cached files belong to (default: the parent of
                the database's folder, i.e. <vault>/.metisem/metisem.db)
        """
        self.db_path = Path(db_path)
        self.vault_root = Path(vault_root) if vault_root is not None else self.db_path.parent.parent
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._initialize_schema()
        self._migrate_path_keys()

    def _key(self, file_path: Path) -> str:
        """Storage key for a file: vault-relative POSIX path, or the path as given if outside the vault."""
        return vault_key(file_path, self.vault_root)

    def _from_key(self, key: str) -> str:
        """Path string for a storage key, in the same form as paths found under vault_root."""
        if is_absolute_key(key):
            return key
        return str(self.vault_root / key)

    def _migrate_path_keys(self) -> None:
        """Convert absolute file_metadata keys from older caches to vault-relative keys.

        Idempotent: runs once per database, recorded in the metadata table.
        """
        if self.get_metadata('path_keys') == 'relative':
            return
        conn = self._get_connection()
        rows = conn.execute("SELECT file_path FROM file_metadata").fetchall()
        for (key,) in rows:
            if not is_absolute_key(key):
                continue
            rel = self.relative_key_for_legacy(key)
            if rel:
                conn.execute("UPDATE OR REPLACE file_metadata SET file_path = ? WHERE file_path = ?", (rel, key))
        conn.commit()
        self.set_metadata('path_keys', 'relative')

    def relative_key_for_legacy(self, key: str) -> Optional[str]:
        """Vault-relative key for an absolute path stored by an older cache, or None.

        Tries the current vault root and every vault path in the run logs, then
        falls back to locating the vault's folder name inside the path.
        """
        conn = self._get_connection()
        roots = [str(self.vault_root.absolute())]
        roots += [row[0] for row in conn.execute("SELECT DISTINCT vault_path FROM run_logs")]
        roots = [r for r in roots if is_absolute_key(r)]
        return legacy_key_to_relative(key, roots, self.vault_root.absolute().name)

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _initialize_schema(self) -> None:
        """Create tables if they don't exist."""
        conn = self._get_connection()
        conn.executescript(self.SCHEMA)
        conn.commit()

    def migrate_summary_schema(self) -> None:
        """Add summary tracking columns if not present.

        Adds has_summary, summary_hash, and summary_text columns to file_metadata
        table for incremental summary processing. Idempotent - safe to call multiple times.
        """
        conn = self._get_connection()

        # Check if migration already applied
        cursor = conn.execute("PRAGMA table_info(file_metadata)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'has_summary' in columns:
            return  # Already migrated

        # Add summary tracking columns
        conn.execute("ALTER TABLE file_metadata ADD COLUMN has_summary INTEGER DEFAULT 0")
        conn.execute("ALTER TABLE file_metadata ADD COLUMN summary_hash TEXT")
        conn.execute("ALTER TABLE file_metadata ADD COLUMN summary_text TEXT")
        conn.commit()

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def get_file_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Retrieve cached metadata for a file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with metadata fields, or None if not cached
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM file_metadata WHERE file_path = ?",
            (self._key(file_path),)
        )
        row = cursor.fetchone()
        if not row:
            return None
        result = dict(row)
        result['file_path'] = self._from_key(result['file_path'])
        return result

    def set_file_metadata(
        self,
        file_path: Path,
        content_hash: str,
        mtime_ns: int,
        size_bytes: int,
        model_name: str,
        embedding_dim: int
    ) -> None:
        """Store or update file metadata.

        Args:
            file_path: Path to the file
            content_hash: SHA256 hash of content
            mtime_ns: Modification time in nanoseconds
            size_bytes: File size in bytes
            model_name: Name of embedding model
            embedding_dim: Dimension of embedding vector
        """
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO file_metadata
            (file_path, content_hash, mtime_ns, size_bytes, model_name, embedding_dim, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (self._key(file_path), content_hash, mtime_ns, size_bytes, model_name, embedding_dim, int(time.time()))
        )
        conn.commit()

    def set_summary_metadata(
        self,
        file_path: Path,
        content_hash: str,
        summary_hash: str,
        summary_text: str
    ) -> None:
        """Update summary metadata for a file.

        Args:
            file_path: Path to the file
            content_hash: SHA256 hash of file content
            summary_hash: SHA256 hash of summary text
            summary_text: Generated summary text
        """
        conn = self._get_connection()
        key = self._key(file_path)
        # Update summary fields while preserving other metadata
        cursor = conn.execute(
            """
            UPDATE file_metadata
            SET has_summary = 1, summary_hash = ?, summary_text = ?, content_hash = ?, updated_at = ?
            WHERE file_path = ?
            """,
            (summary_hash, summary_text, content_hash, int(time.time()), key)
        )
        # If file not in database, insert minimal record (rowcount is per statement;
        # total_changes is cumulative per connection, so it missed every insert after the first write)
        if cursor.rowcount == 0:
            conn.execute(
                """
                INSERT INTO file_metadata
                (file_path, content_hash, mtime_ns, size_bytes, model_name, embedding_dim, has_summary, summary_hash, summary_text, updated_at)
                VALUES (?, ?, 0, 0, '', 0, 1, ?, ?, ?)
                """,
                (key, content_hash, summary_hash, summary_text, int(time.time()))
            )
        conn.commit()

    def get_all_paths(self, model_name: str) -> List[str]:
        """List all cached file paths for a specific model.

        Args:
            model_name: Name of embedding model

        Returns:
            List of file path strings
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT file_path FROM file_metadata WHERE model_name = ?",
            (model_name,)
        )
        return [self._from_key(row['file_path']) for row in cursor.fetchall()]

    def remove_file(self, file_path: Path) -> None:
        """Delete metadata for a file.

        Args:
            file_path: Path to the file
        """
        conn = self._get_connection()
        conn.execute(
            "DELETE FROM file_metadata WHERE file_path = ?",
            (self._key(file_path),)
        )
        conn.commit()

    def get_tag_embedding(self, tag_name: str, model_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached tag embedding.

        Args:
            tag_name: Name of the tag
            model_name: Name of embedding model

        Returns:
            Dictionary with 'content_hash' and 'embedding' keys, or None if not cached
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT content_hash, embedding_blob FROM tag_embeddings WHERE tag_name = ? AND model_name = ?",
            (tag_name, model_name)
        )
        row = cursor.fetchone()
        if row:
            return {
                'content_hash': row['content_hash'],
                'embedding': np.frombuffer(row['embedding_blob'], dtype=np.float32)
            }
        return None

    def set_tag_embedding(
        self,
        tag_name: str,
        tag_description: str,
        content_hash: str,
        model_name: str,
        embedding: np.ndarray
    ) -> None:
        """Store or update tag embedding.

        Args:
            tag_name: Name of the tag
            tag_description: Description text for the tag
            content_hash: SHA256 hash of description
            model_name: Name of embedding model
            embedding: Embedding vector
        """
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO tag_embeddings
            (tag_name, tag_description, content_hash, model_name, embedding_blob, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (tag_name, tag_description, content_hash, model_name, embedding.astype(np.float32).tobytes(), int(time.time()))
        )
        conn.commit()

    def get_metadata(self, key: str) -> Optional[str]:
        """Get metadata value.

        Args:
            key: Metadata key

        Returns:
            Value string, or None if not found
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT value FROM metadata WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()
        return row['value'] if row else None

    def set_metadata(self, key: str, value: str) -> None:
        """Set metadata value.

        Args:
            key: Metadata key
            value: Value to store
        """
        conn = self._get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            (key, value)
        )
        conn.commit()

    def log_run(self, run_data: Dict[str, Any]) -> None:
        """Log a tool execution run.

        Args:
            run_data: Dictionary containing run metadata and metrics
        """
        conn = self._get_connection()
        conn.execute(
            """
            INSERT INTO run_logs (
                run_id, timestamp, tool_name, operation, vault_path,
                files_total, files_modified, files_new, files_unchanged, files_deleted,
                links_added, links_removed, tags_applied, tags_removed,
                summaries_added, summaries_removed,
                parameters, duration_seconds, embedding_time_seconds, cache_hit_ratio,
                status, error_count, error_message, model_name, embedding_dim
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                run_data.get('run_id'),
                run_data.get('timestamp'),
                run_data.get('tool_name'),
                run_data.get('operation'),
                run_data.get('vault_path'),
                run_data.get('files_total'),
                run_data.get('files_modified'),
                run_data.get('files_new'),
                run_data.get('files_unchanged'),
                run_data.get('files_deleted'),
                run_data.get('links_added'),
                run_data.get('links_removed'),
                run_data.get('tags_applied'),
                run_data.get('tags_removed'),
                run_data.get('summaries_added'),
                run_data.get('summaries_removed'),
                run_data.get('parameters'),
                run_data.get('duration_seconds'),
                run_data.get('embedding_time_seconds'),
                run_data.get('cache_hit_ratio'),
                run_data.get('status'),
                run_data.get('error_count'),
                run_data.get('error_message'),
                run_data.get('model_name'),
                run_data.get('embedding_dim')
            )
        )
        conn.commit()

    def get_recent_runs(self, vault_path: Optional[str] = None, tool_name: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent run logs.

        Args:
            vault_path: Filter by vault path (optional)
            tool_name: Filter by tool name (optional)
            limit: Maximum number of runs to return

        Returns:
            List of run dictionaries
        """
        conn = self._get_connection()
        query = "SELECT * FROM run_logs WHERE 1=1"
        params = []

        if vault_path:
            query += " AND vault_path = ?"
            params.append(vault_path)

        if tool_name:
            query += " AND tool_name = ?"
            params.append(tool_name)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]
