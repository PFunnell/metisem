"""Query and analyse run logs from Metisem tools.

This utility provides analysis and export capabilities for run logs stored in the
.metisem/metisem.db database.
"""

import argparse
import json
import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from metisem.core.database import CacheDatabase


def format_timestamp(ts: int) -> str:
    """Format Unix timestamp as human-readable datetime."""
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


def print_run_summary(run: Dict[str, Any], detailed: bool = False) -> None:
    """Print a formatted summary of a single run."""
    print(f"\n{'='*60}")
    print(f"Run ID: {run['run_id']}")
    print(f"Time: {format_timestamp(run['timestamp'])}")
    print(f"Tool: {run['tool_name']} ({run['operation']})")
    print(f"Status: {run['status']}")

    if run.get('duration_seconds'):
        print(f"Duration: {run['duration_seconds']:.2f}s")

    print(f"\nFile Statistics:")
    print(f"  Total: {run.get('files_total', 0)}")
    print(f"  Modified: {run.get('files_modified', 0)}")
    print(f"  New: {run.get('files_new', 0)}")
    print(f"  Unchanged: {run.get('files_unchanged', 0)}")
    print(f"  Deleted: {run.get('files_deleted', 0)}")

    if run.get('cache_hit_ratio') is not None:
        print(f"  Cache hit ratio: {run['cache_hit_ratio']:.1%}")

    # Tool-specific metrics
    if run.get('links_added') or run.get('links_removed'):
        print(f"\nLinks:")
        if run.get('links_added'):
            print(f"  Added: {run['links_added']}")
        if run.get('links_removed'):
            print(f"  Removed: {run['links_removed']}")

    if run.get('tags_applied') or run.get('tags_removed'):
        print(f"\nTags:")
        if run.get('tags_applied'):
            print(f"  Applied: {run['tags_applied']}")
        if run.get('tags_removed'):
            print(f"  Removed: {run['tags_removed']}")

    if run.get('summaries_added') or run.get('summaries_removed'):
        print(f"\nSummaries:")
        if run.get('summaries_added'):
            print(f"  Added: {run['summaries_added']}")
        if run.get('summaries_removed'):
            print(f"  Removed: {run['summaries_removed']}")

    if run.get('model_name'):
        print(f"\nModel: {run['model_name']}")
        if run.get('embedding_dim'):
            print(f"Embedding dimension: {run['embedding_dim']}")

    if detailed and run.get('parameters'):
        print(f"\nParameters: {run['parameters']}")

    if run.get('error_message'):
        print(f"\nErrors: {run['error_message']}")
        if run.get('error_count'):
            print(f"Error count: {run['error_count']}")


def export_json(runs: List[Dict[str, Any]], output_path: str) -> None:
    """Export runs to JSON file."""
    # Convert timestamps to ISO format for readability
    export_data = []
    for run in runs:
        run_copy = run.copy()
        run_copy['timestamp_iso'] = format_timestamp(run['timestamp'])
        export_data.append(run_copy)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2)
    print(f"Exported {len(runs)} runs to {output_path}")


def export_csv(runs: List[Dict[str, Any]], output_path: str) -> None:
    """Export runs to CSV file."""
    if not runs:
        print("No runs to export")
        return

    # Define column order
    columns = [
        'run_id', 'timestamp', 'tool_name', 'operation', 'status',
        'duration_seconds', 'files_total', 'files_modified', 'files_new',
        'files_unchanged', 'files_deleted', 'cache_hit_ratio',
        'links_added', 'links_removed', 'tags_applied', 'tags_removed',
        'summaries_added', 'summaries_removed', 'model_name',
        'embedding_dim', 'error_count', 'parameters'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()

        for run in runs:
            # Convert timestamp for readability
            row = run.copy()
            row['timestamp'] = format_timestamp(run['timestamp'])
            writer.writerow(row)

    print(f"Exported {len(runs)} runs to {output_path}")


def analyse_parameter_impact(runs: List[Dict[str, Any]], param_name: str) -> None:
    """Analyse how a parameter affects outcomes."""
    print(f"\nParameter Impact Analysis: {param_name}")
    print(f"{'='*60}")

    # Group runs by parameter value
    groups: Dict[str, List[Dict]] = {}
    for run in runs:
        if run.get('parameters'):
            try:
                params = json.loads(run['parameters'])
                value = params.get(param_name)
                if value is not None:
                    key = str(value)
                    if key not in groups:
                        groups[key] = []
                    groups[key].append(run)
            except json.JSONDecodeError:
                continue

    if not groups:
        print(f"No runs found with parameter '{param_name}'")
        return

    # Print analysis for each parameter value
    for value, group_runs in sorted(groups.items()):
        print(f"\n{param_name} = {value} ({len(group_runs)} runs)")

        # Calculate averages (handle None values)
        avg_links = sum(r.get('links_added') or 0 for r in group_runs) / len(group_runs)
        avg_tags = sum(r.get('tags_applied') or 0 for r in group_runs) / len(group_runs)
        avg_duration = sum(r.get('duration_seconds') or 0 for r in group_runs) / len(group_runs)
        avg_modified = sum(r.get('files_modified') or 0 for r in group_runs) / len(group_runs)

        if avg_links > 0:
            print(f"  Avg links added: {avg_links:.1f}")
        if avg_tags > 0:
            print(f"  Avg tags applied: {avg_tags:.1f}")
        if avg_modified > 0:
            print(f"  Avg files modified: {avg_modified:.1f}")
        if avg_duration > 0:
            print(f"  Avg duration: {avg_duration:.2f}s")


def main():
    parser = argparse.ArgumentParser(
        description="Query and analyse Metisem run logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View recent runs
  python scripts/query_runs.py /path/to/vault

  # View runs for specific tool
  python scripts/query_runs.py /path/to/vault --tool linker

  # Export to JSON
  python scripts/query_runs.py /path/to/vault --export runs.json

  # Export to CSV
  python scripts/query_runs.py /path/to/vault --export runs.csv

  # Analyse parameter impact
  python scripts/query_runs.py /path/to/vault --analyse similarity
        """
    )

    parser.add_argument('vault_path', help='Path to vault')
    parser.add_argument('--tool', choices=['linker', 'tagger', 'summariser'],
                       help='Filter by tool name')
    parser.add_argument('--limit', type=int, default=10,
                       help='Number of runs to retrieve (default: 10)')
    parser.add_argument('--export', metavar='FILE',
                       help='Export to JSON or CSV file (format determined by extension)')
    parser.add_argument('--analyse', metavar='PARAM',
                       help='Analyse impact of a parameter (e.g., similarity, max_links)')
    parser.add_argument('--detailed', action='store_true',
                       help='Show detailed output including parameters')
    parser.add_argument('--status', choices=['success', 'partial', 'error'],
                       help='Filter by status')

    args = parser.parse_args()

    # Open database
    vault_path = Path(args.vault_path).resolve()
    db_path = vault_path / ".metisem" / "metisem.db"

    if not db_path.exists():
        print(f"Error: No database found at {db_path}")
        print("Have you run any Metisem tools on this vault yet?")
        return 1

    db = CacheDatabase(db_path)

    # Query runs
    runs = db.get_recent_runs(
        vault_path=str(vault_path),
        tool_name=args.tool,
        limit=args.limit if not args.export else 1000  # Get more for export
    )

    # Filter by status if requested
    if args.status:
        runs = [r for r in runs if r.get('status') == args.status]

    if not runs:
        print("No runs found matching criteria")
        return 0

    # Export mode
    if args.export:
        export_path = args.export
        if export_path.endswith('.json'):
            export_json(runs, export_path)
        elif export_path.endswith('.csv'):
            export_csv(runs, export_path)
        else:
            print("Error: Export file must have .json or .csv extension")
            return 1
        return 0

    # Analysis mode
    if args.analyse:
        analyse_parameter_impact(runs, args.analyse)
        return 0

    # Display mode
    print(f"\nShowing {len(runs)} most recent runs")
    for run in runs:
        print_run_summary(run, detailed=args.detailed)

    print(f"\n{'='*60}\n")
    print(f"Use --export to save runs to JSON/CSV")
    print(f"Use --analyse <param> to analyse parameter impact")

    db.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
