#!/usr/bin/env python3
"""Validate that artefacts are in canonical locations.

This script checks that plans, checkpoints, and research files are in their
expected directories according to repo conventions.

Usage:
    python scripts/validate-artefacts.py

Exit codes:
    0 - All artefacts in expected locations
    1 - Misplaced artefacts found
"""

import sys
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

REPO_ROOT = Path(__file__).parent.parent

# Default locations (used if config not found)
DEFAULT_LOCATIONS = {
    "plans": "docs/plans",
    "state": "docs/state",
    "research": "docs/research",
    "verification": "docs/verification",
}


def load_config() -> dict:
    """Load artefact paths from config file."""
    config_path = REPO_ROOT / ".claude" / "portable_config.local.yaml"

    if not config_path.exists():
        print(f"Note: Config not found at {config_path}, using defaults")
        return {}

    if not HAS_YAML:
        print("Note: PyYAML not installed, using default locations")
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('artefacts', {})
    except Exception as e:
        print(f"Warning: Could not parse config: {e}")
        return {}


def get_expected_locations() -> dict[str, Path]:
    """Get expected artefact locations from config or defaults."""
    config = load_config()

    locations = {
        "plans": REPO_ROOT / config.get('plans_dir', DEFAULT_LOCATIONS['plans']),
        "state": REPO_ROOT / config.get('state_dir', DEFAULT_LOCATIONS['state']),
        "research": REPO_ROOT / config.get('research_dir', DEFAULT_LOCATIONS['research']),
        "verification": REPO_ROOT / config.get('verification_dir', DEFAULT_LOCATIONS['verification']),
    }

    return locations


# Patterns that indicate artefact type
ARTEFACT_INDICATORS = {
    "_plan": "plans",
    "_implementation": "plans",
    "_checkpoint": "state",
    "_state": "state",
    "_research": "research",
    "_analysis": "research",
    ".brief": "research",
    "verify_": "verification",
}


def get_expected_location(filename: str) -> str | None:
    """Determine expected location based on filename patterns."""
    for pattern, location in ARTEFACT_INDICATORS.items():
        if pattern in filename.lower():
            return location
    return None


def check_misplaced_artefacts(expected_locations: dict[str, Path]) -> list[str]:
    """Find artefacts in wrong locations."""
    issues = []

    # Check common artefact directories
    search_dirs = [
        REPO_ROOT / "docs",
        REPO_ROOT / "thoughts",
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        for md_file in search_dir.rglob("*.md"):
            expected_type = get_expected_location(md_file.name)
            if expected_type is None:
                continue

            expected_dir = expected_locations.get(expected_type)
            if expected_dir is None:
                continue

            # Check if file is in expected location or a subdirectory of it
            try:
                md_file.relative_to(expected_dir)
                # File is in correct location
                continue
            except ValueError:
                # File is not under expected directory
                issues.append(
                    f"Misplaced: {md_file.relative_to(REPO_ROOT)} "
                    f"(expected in {expected_type}/ -> {expected_dir.relative_to(REPO_ROOT)})"
                )

    return issues


def check_empty_required_dirs(expected_locations: dict[str, Path]) -> list[str]:
    """Check that required directories exist."""
    issues = []
    for name, path in expected_locations.items():
        if not path.exists():
            issues.append(f"Missing directory: {path.relative_to(REPO_ROOT)}")
    return issues


def main() -> int:
    """Run validation and report results."""
    expected_locations = get_expected_locations()
    all_issues = []

    # Check directory structure
    dir_issues = check_empty_required_dirs(expected_locations)
    all_issues.extend(dir_issues)

    # Check artefact locations
    artefact_issues = check_misplaced_artefacts(expected_locations)
    all_issues.extend(artefact_issues)

    if all_issues:
        print("Artefact location issues found:")
        for issue in all_issues:
            print(f"  - {issue}")
        return 1
    else:
        print("All artefacts in expected locations.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
