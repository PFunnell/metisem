"""Clean up old run logs from Metisem database.

This utility helps manage log retention by removing old run logs based on age or count.
"""

import argparse
import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def parse_time_duration(duration_str: str) -> int:
    """Parse duration string (e.g., '30d', '12w', '6m') into seconds.

    Args:
        duration_str: Duration string with format like '30d', '12w', '6m', '1y'

    Returns:
        Number of seconds
    """
    unit = duration_str[-1].lower()
    value = int(duration_str[:-1])

    units = {
        'd': 86400,      # days
        'w': 604800,     # weeks
        'm': 2592000,    # months (30 days)
        'y': 31536000    # years (365 days)
    }

    if unit not in units:
        raise ValueError(f"Invalid time unit '{unit}'. Use d (days), w (weeks), m (months), or y (years)")

    return value * units[unit]


def cleanup_logs(vault_path: str, older_than: Optional[str] = None,
                 keep_last: Optional[int] = None, tool_name: Optional[str] = None,
                 dry_run: bool = False) -> int:
    """Clean up old run logs.

    Args:
        vault_path: Path to vault
        older_than: Remove logs older than this duration (e.g., '30d', '12w')
        keep_last: Keep only the N most recent logs
        tool_name: Only clean logs for specific tool
        dry_run: Preview what would be deleted without actually deleting

    Returns:
        Number of logs deleted (or would be deleted in dry run mode)
    """
    vault_path = Path(vault_path).resolve()
    db_path = vault_path / ".metisem" / "metisem.db"

    if not db_path.exists():
        print(f"Error: No database found at {db_path}")
        return 0

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Build query
    if older_than:
        # Delete logs older than threshold
        seconds_ago = parse_time_duration(older_than)
        threshold_timestamp = int((datetime.now() - timedelta(seconds=seconds_ago)).timestamp())

        query = "SELECT COUNT(*) FROM run_logs WHERE timestamp < ?"
        params = [threshold_timestamp]

        if tool_name:
            query += " AND tool_name = ?"
            params.append(tool_name)

        cursor = conn.execute(query, params)
        count = cursor.fetchone()[0]

        if dry_run:
            print(f"[DRY RUN] Would delete {count} log(s) older than {older_than}")
        else:
            delete_query = query.replace("SELECT COUNT(*)", "DELETE")
            conn.execute(delete_query, params)
            conn.commit()
            print(f"Deleted {count} log(s) older than {older_than}")

    elif keep_last:
        # Keep only N most recent logs
        query = "SELECT run_id FROM run_logs"
        params = []

        if tool_name:
            query += " WHERE tool_name = ?"
            params.append(tool_name)

        query += " ORDER BY timestamp DESC"

        cursor = conn.execute(query, params)
        all_runs = [row['run_id'] for row in cursor.fetchall()]

        if len(all_runs) <= keep_last:
            print(f"Only {len(all_runs)} log(s) found, nothing to delete")
            count = 0
        else:
            to_delete = all_runs[keep_last:]
            count = len(to_delete)

            if dry_run:
                print(f"[DRY RUN] Would delete {count} log(s), keeping {keep_last} most recent")
            else:
                placeholders = ','.join('?' * len(to_delete))
                conn.execute(f"DELETE FROM run_logs WHERE run_id IN ({placeholders})", to_delete)
                conn.commit()
                print(f"Deleted {count} log(s), kept {keep_last} most recent")
    else:
        print("Error: Must specify either --older-than or --keep-last")
        conn.close()
        return 0

    conn.close()
    return count


def show_stats(vault_path: str) -> None:
    """Show statistics about run logs."""
    vault_path = Path(vault_path).resolve()
    db_path = vault_path / ".metisem" / "metisem.db"

    if not db_path.exists():
        print(f"Error: No database found at {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Total logs
    cursor = conn.execute("SELECT COUNT(*) as count FROM run_logs")
    total = cursor.fetchone()['count']
    print(f"\nTotal run logs: {total}")

    # Logs by tool
    cursor = conn.execute("""
        SELECT tool_name, COUNT(*) as count
        FROM run_logs
        GROUP BY tool_name
        ORDER BY count DESC
    """)
    print("\nLogs by tool:")
    for row in cursor:
        print(f"  {row['tool_name']}: {row['count']}")

    # Oldest and newest
    cursor = conn.execute("""
        SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest
        FROM run_logs
    """)
    row = cursor.fetchone()
    if row['oldest']:
        oldest = datetime.fromtimestamp(row['oldest']).strftime('%Y-%m-%d %H:%M:%S')
        newest = datetime.fromtimestamp(row['newest']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"\nOldest log: {oldest}")
        print(f"Newest log: {newest}")

    # Database size
    db_size = db_path.stat().st_size
    print(f"\nDatabase size: {db_size / 1024:.1f} KB")

    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Clean up old Metisem run logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview deletion of logs older than 90 days
  python scripts/cleanup_logs.py /path/to/vault --older-than 90d --dry-run

  # Delete logs older than 3 months
  python scripts/cleanup_logs.py /path/to/vault --older-than 12w

  # Keep only 50 most recent logs
  python scripts/cleanup_logs.py /path/to/vault --keep-last 50

  # Keep only 20 most recent linker logs
  python scripts/cleanup_logs.py /path/to/vault --keep-last 20 --tool linker

  # Show log statistics
  python scripts/cleanup_logs.py /path/to/vault --stats
        """
    )

    parser.add_argument('vault_path', help='Path to vault')
    parser.add_argument('--older-than', metavar='DURATION',
                       help='Delete logs older than duration (e.g., 30d, 12w, 6m, 1y)')
    parser.add_argument('--keep-last', type=int, metavar='N',
                       help='Keep only the N most recent logs')
    parser.add_argument('--tool', choices=['linker', 'tagger', 'summariser'],
                       help='Only clean logs for specific tool')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview what would be deleted without actually deleting')
    parser.add_argument('--stats', action='store_true',
                       help='Show log statistics without deleting anything')

    args = parser.parse_args()

    if args.stats:
        show_stats(args.vault_path)
        return 0

    if not args.older_than and not args.keep_last:
        parser.print_help()
        print("\nError: Must specify either --older-than or --keep-last (or use --stats)")
        return 1

    cleanup_logs(
        vault_path=args.vault_path,
        older_than=args.older_than,
        keep_last=args.keep_last,
        tool_name=args.tool,
        dry_run=args.dry_run
    )

    return 0


if __name__ == '__main__':
    sys.exit(main())
