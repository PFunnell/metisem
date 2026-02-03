"""SQLite database for cache metadata and tag embeddings.

This module provides persistent storage for file metadata (hashes, mtimes) and
tag embeddings, enabling fast incremental processing.
"""

import sqlite3
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import numpy as np


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

    def __init__(self, db_path: Path):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._initialize_schema()

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
            (str(file_path),)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

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
            (str(file_path), content_hash, mtime_ns, size_bytes, model_name, embedding_dim, int(time.time()))
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
        return [row['file_path'] for row in cursor.fetchall()]

    def remove_file(self, file_path: Path) -> None:
        """Delete metadata for a file.

        Args:
            file_path: Path to the file
        """
        conn = self._get_connection()
        conn.execute(
            "DELETE FROM file_metadata WHERE file_path = ?",
            (str(file_path),)
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
