#!/usr/bin/env python
"""Automated test script for Metisem run logging and core functionality.

This script tests:
1. Linker functionality and logging
2. Tagger functionality and logging
3. Query utility
4. Parameter impact analysis
5. CSV export
6. Cleanup utility
"""

import sys
import subprocess
import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

# Colour codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name):
    """Print test name."""
    print(f"\n{BLUE}> {name}{RESET}")

def print_pass(message):
    """Print pass message."""
    print(f"  {GREEN}[PASS]{RESET} {message}")

def print_fail(message):
    """Print fail message."""
    print(f"  {RED}[FAIL]{RESET} {message}")

def print_warn(message):
    """Print warning message."""
    print(f"  {YELLOW}[WARN]{RESET} {message}")

def run_command(cmd, check=True, timeout=120):
    """Run command and return result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        return e
    except subprocess.TimeoutExpired:
        print_fail(f"Command timed out after {timeout}s")
        return None

def get_test_vault():
    """Get test vault path from .env or config."""
    # Try .env first
    env_file = Path('.env')
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith('TEST_VAULT_PATH='):
                vault = line.split('=', 1)[1].strip()
                return vault

    # Try config
    try:
        import yaml
        config_file = Path('.claude/portable_config.local.yaml')
        if config_file.exists():
            with open(config_file) as f:
                config = yaml.safe_load(f)
                vault = config.get('testing', {}).get('vault_path')
                if vault:
                    return vault
    except Exception:
        pass

    return None

def count_logs(vault_path, tool_name=None):
    """Count run logs in database."""
    db_path = Path(vault_path) / ".metisem" / "metisem.db"
    if not db_path.exists():
        return 0

    conn = sqlite3.connect(str(db_path))
    if tool_name:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM run_logs WHERE tool_name = ?",
            (tool_name,)
        )
    else:
        cursor = conn.execute("SELECT COUNT(*) FROM run_logs")

    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_latest_log(vault_path, tool_name=None):
    """Get latest run log."""
    db_path = Path(vault_path) / ".metisem" / "metisem.db"
    if not db_path.exists():
        return None

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    if tool_name:
        cursor = conn.execute(
            "SELECT * FROM run_logs WHERE tool_name = ? ORDER BY timestamp DESC LIMIT 1",
            (tool_name,)
        )
    else:
        cursor = conn.execute(
            "SELECT * FROM run_logs ORDER BY timestamp DESC LIMIT 1"
        )

    row = cursor.fetchone()
    result = dict(row) if row else None
    conn.close()
    return result

def test_linker(vault_path):
    """Test linker functionality."""
    print_test("Testing Linker")

    initial_count = count_logs(vault_path, 'linker')

    # Run linker in preview mode
    cmd = f'python main.py "{vault_path}" --similarity 0.7 --max-links 5'
    result = run_command(cmd)

    if result and result.returncode == 0:
        print_pass("Linker executed successfully")

        # Check log was created
        new_count = count_logs(vault_path, 'linker')
        if new_count > initial_count:
            print_pass(f"Run log created ({new_count - initial_count} new log)")

            # Verify log contents
            log = get_latest_log(vault_path, 'linker')
            if log:
                # Check required fields
                assert log['tool_name'] == 'linker', "Tool name incorrect"
                assert log['operation'] == 'preview', "Operation incorrect"
                assert log['status'] in ['success', 'partial', 'error'], "Invalid status"
                assert log['files_total'] > 0, "No files processed"
                assert log['duration_seconds'] > 0, "Duration not recorded"

                # Check parameters
                params = json.loads(log['parameters'])
                assert params['similarity'] == 0.7, "Similarity parameter not logged"
                assert params['max_links'] == 5, "Max links parameter not logged"

                print_pass(f"Log validated: {log['files_total']} files, {log.get('links_added', 0)} links, {log['duration_seconds']:.2f}s")

                # Check cache hit ratio
                if log.get('cache_hit_ratio') is not None:
                    print_pass(f"Cache hit ratio: {log['cache_hit_ratio']:.0%}")
            else:
                print_fail("Could not retrieve log")
                return False
        else:
            print_fail("Run log not created")
            return False
    else:
        print_fail("Linker execution failed")
        if result:
            print(result.stderr)
        return False

    return True

def test_tagger(vault_path):
    """Test tagger functionality."""
    print_test("Testing Tagger")

    # Check if tags file exists
    tags_file = Path('tags.txt')
    if not tags_file.exists():
        print_warn("tags.txt not found - skipping tagger test")
        return None

    initial_count = count_logs(vault_path, 'tagger')

    # Run tagger in preview mode (without --apply-tags)
    cmd = f'python tagger.py "{vault_path}" --tags-file tags.txt'
    result = run_command(cmd, timeout=180)

    if result and result.returncode == 0:
        print_pass("Tagger executed successfully")

        # Check log was created
        new_count = count_logs(vault_path, 'tagger')
        if new_count > initial_count:
            print_pass(f"Run log created ({new_count - initial_count} new log)")

            # Verify log contents
            log = get_latest_log(vault_path, 'tagger')
            if log:
                assert log['tool_name'] == 'tagger', "Tool name incorrect"
                assert log['status'] in ['success', 'partial', 'error'], "Invalid status"
                print_pass(f"Log validated: {log['files_total']} files, {log['duration_seconds']:.2f}s")
            else:
                print_fail("Could not retrieve log")
                return False
        else:
            print_fail("Run log not created")
            return False
    else:
        print_fail("Tagger execution failed")
        if result:
            print(result.stderr)
        return False

    return True

def test_query_utility(vault_path):
    """Test query utility."""
    print_test("Testing Query Utility")

    # Test basic query
    cmd = f'python scripts/query_runs.py "{vault_path}" --limit 2'
    result = run_command(cmd)

    if result and result.returncode == 0:
        print_pass("Query utility works")
        if "Run ID:" in result.stdout:
            print_pass("Output formatted correctly")
        else:
            print_fail("Output format unexpected")
            return False
    else:
        print_fail("Query utility failed")
        return False

    # Test parameter analysis
    cmd = f'python scripts/query_runs.py "{vault_path}" --analyse similarity'
    result = run_command(cmd)

    if result and result.returncode == 0:
        print_pass("Parameter analysis works")
    else:
        print_warn("Parameter analysis failed (may need multiple runs)")

    return True

def test_csv_export(vault_path):
    """Test CSV export."""
    print_test("Testing CSV Export")

    export_file = "test_export.csv"
    cmd = f'python scripts/query_runs.py "{vault_path}" --export {export_file}'
    result = run_command(cmd)

    if result and result.returncode == 0:
        print_pass("CSV export command succeeded")

        # Check file exists
        if Path(export_file).exists():
            print_pass(f"CSV file created: {export_file}")

            # Check contents
            with open(export_file) as f:
                lines = f.readlines()
                if len(lines) > 1:  # Header + at least one row
                    print_pass(f"CSV contains {len(lines)-1} run(s)")

                    # Check header
                    header = lines[0]
                    required_fields = ['run_id', 'timestamp', 'tool_name', 'operation',
                                     'files_total', 'duration_seconds', 'parameters']
                    for field in required_fields:
                        if field not in header:
                            print_fail(f"Missing field in CSV: {field}")
                            return False
                    print_pass("CSV header validated")
                else:
                    print_fail("CSV is empty")
                    return False

            # Clean up
            Path(export_file).unlink()
        else:
            print_fail("CSV file not created")
            return False
    else:
        print_fail("CSV export failed")
        return False

    return True

def test_cleanup_utility(vault_path):
    """Test cleanup utility."""
    print_test("Testing Cleanup Utility")

    # Test stats
    cmd = f'python scripts/cleanup_logs.py "{vault_path}" --stats'
    result = run_command(cmd)

    if result and result.returncode == 0:
        print_pass("Stats command works")
        if "Total run logs:" in result.stdout:
            print_pass("Stats output formatted correctly")
        else:
            print_fail("Stats output format unexpected")
            return False
    else:
        print_fail("Stats command failed")
        return False

    # Test dry-run
    cmd = f'python scripts/cleanup_logs.py "{vault_path}" --keep-last 1 --dry-run'
    result = run_command(cmd)

    if result and result.returncode == 0:
        print_pass("Dry-run works")
        if "[DRY RUN]" in result.stdout or "nothing to delete" in result.stdout.lower():
            print_pass("Dry-run output correct")
        else:
            print_warn("Dry-run output unexpected")
    else:
        print_fail("Dry-run failed")
        return False

    return True

def main():
    """Run all tests."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Metisem Run Logging Test Suite{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    # Get test vault
    vault_path = get_test_vault()
    if not vault_path:
        print_fail("Test vault path not configured")
        print("  Add TEST_VAULT_PATH to .env or testing.vault_path to config")
        return 1

    vault_path = Path(vault_path)
    if not vault_path.exists():
        print_fail(f"Test vault not found: {vault_path}")
        return 1

    print(f"Test vault: {vault_path}")

    # Run tests
    results = {}

    results['linker'] = test_linker(vault_path)
    results['tagger'] = test_tagger(vault_path)
    results['query'] = test_query_utility(vault_path)
    results['csv_export'] = test_csv_export(vault_path)
    results['cleanup'] = test_cleanup_utility(vault_path)

    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    passed = sum(1 for v in results.values() if v is True)
    skipped = sum(1 for v in results.values() if v is None)
    failed = sum(1 for v in results.values() if v is False)
    total = len(results)

    for name, result in results.items():
        if result is True:
            print(f"  {GREEN}[PASS]{RESET} {name}")
        elif result is None:
            print(f"  {YELLOW}[SKIP]{RESET} {name}")
        else:
            print(f"  {RED}[FAIL]{RESET} {name}")

    print(f"\n{passed}/{total} tests passed")
    if skipped > 0:
        print(f"{skipped} tests skipped")
    if failed > 0:
        print(f"{RED}{failed} tests failed{RESET}")

    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
