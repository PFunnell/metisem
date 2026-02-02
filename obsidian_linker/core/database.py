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
