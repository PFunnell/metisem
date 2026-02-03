"""Run logging for Metisem tools.

This module provides a RunLogger class for tracking tool executions and
persisting metrics to the database for parameter tuning and analysis.
"""

import time
import uuid
import json
from pathlib import Path
from typing import Optional, Dict, Any
from .database import CacheDatabase


class RunLogger:
    """Tracks and logs tool execution runs."""

    def __init__(self, vault_path: str, tool_name: str):
        """Initialise logger for a tool run.

        Args:
            vault_path: Path to vault
            tool_name: 'linker', 'tagger', or 'summariser'
        """
        self.vault_path = str(Path(vault_path).resolve())
        self.tool_name = tool_name
        self.run_id = str(uuid.uuid4())
        self.start_time = time.time()
        self.metrics: Dict[str, Any] = {
            'run_id': self.run_id,
            'vault_path': self.vault_path,
            'tool_name': tool_name,
            'timestamp': int(self.start_time),
            'status': 'in_progress'
        }

        # Initialize database connection
        cache_dir = Path(vault_path) / ".metisem"
        self.db = CacheDatabase(cache_dir / "metisem.db")

    def set_operation(self, operation: str) -> None:
        """Set the operation type (e.g., 'apply', 'remove', 'preview').

        Args:
            operation: Operation type string
        """
        self.metrics['operation'] = operation

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Store run parameters as JSON.

        Args:
            params: Dictionary of parameters
        """
        self.metrics['parameters'] = json.dumps(params)

    def set_file_stats(self, total: int = 0, modified: int = 0, new: int = 0,
                       unchanged: int = 0, deleted: int = 0) -> None:
        """Set file statistics.

        Args:
            total: Total files processed
            modified: Files modified
            new: New files
            unchanged: Unchanged files
            deleted: Deleted files
        """
        self.metrics['files_total'] = total
        self.metrics['files_modified'] = modified
        self.metrics['files_new'] = new
        self.metrics['files_unchanged'] = unchanged
        self.metrics['files_deleted'] = deleted

        # Calculate cache hit ratio
        if total > 0:
            self.metrics['cache_hit_ratio'] = unchanged / total
        else:
            self.metrics['cache_hit_ratio'] = 0.0

    def set_link_stats(self, added: int = 0, removed: int = 0) -> None:
        """Set link statistics.

        Args:
            added: Links added
            removed: Links removed
        """
        self.metrics['links_added'] = added
        self.metrics['links_removed'] = removed

    def set_tag_stats(self, applied: int = 0, removed: int = 0) -> None:
        """Set tag statistics.

        Args:
            applied: Tags applied
            removed: Tags removed
        """
        self.metrics['tags_applied'] = applied
        self.metrics['tags_removed'] = removed

    def set_summary_stats(self, added: int = 0, removed: int = 0) -> None:
        """Set summary statistics.

        Args:
            added: Summaries added
            removed: Summaries removed
        """
        self.metrics['summaries_added'] = added
        self.metrics['summaries_removed'] = removed

    def set_model_info(self, model_name: str, embedding_dim: Optional[int] = None) -> None:
        """Set model information.

        Args:
            model_name: Name of embedding model
            embedding_dim: Dimension of embeddings
        """
        self.metrics['model_name'] = model_name
        if embedding_dim is not None:
            self.metrics['embedding_dim'] = embedding_dim

    def set_embedding_time(self, seconds: float) -> None:
        """Set embedding generation time.

        Args:
            seconds: Time spent generating embeddings
        """
        self.metrics['embedding_time_seconds'] = seconds

    def add_error(self, error_message: str) -> None:
        """Record an error during the run.

        Args:
            error_message: Error description
        """
        error_count = self.metrics.get('error_count', 0)
        self.metrics['error_count'] = error_count + 1

        # Append to error message
        existing_msg = self.metrics.get('error_message', '')
        if existing_msg:
            self.metrics['error_message'] = f"{existing_msg}; {error_message}"
        else:
            self.metrics['error_message'] = error_message

    def complete(self, status: str = 'success') -> None:
        """Finalise run and persist to database.

        Args:
            status: Final status ('success', 'partial', 'error')
        """
        # Calculate duration
        end_time = time.time()
        self.metrics['duration_seconds'] = end_time - self.start_time
        self.metrics['status'] = status

        # Persist to database
        try:
            self.db.log_run(self.metrics)
        except Exception as e:
            # Log error but don't fail the run
            print(f"Warning: Failed to log run: {e}")
        finally:
            self.db.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically complete run."""
        if exc_type is not None:
            # Exception occurred
            self.add_error(f"{exc_type.__name__}: {exc_val}")
            self.complete(status='error')
        else:
            # Normal completion
            error_count = self.metrics.get('error_count', 0)
            if error_count > 0:
                self.complete(status='partial')
            else:
                self.complete(status='success')
        return False  # Don't suppress exceptions
