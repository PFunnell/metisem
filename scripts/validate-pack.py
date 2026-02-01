#!/usr/bin/env python3
"""Validate the Claude Code RPI Plus pack before release.

Pre-flight checks for:
- Required files exist
- YAML/JSON syntax is valid
- No placeholder text remains
- No sensitive data patterns
- Cross-platform path handling

Usage:
    python scripts/validate-pack.py

Exit codes:
    0 - All checks pass
    1 - Issues found
"""

import json
import re
import sys
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

PACK_ROOT = Path(__file__).parent.parent

# Required files that must exist
REQUIRED_FILES = [
    ".claude/README.md",
    ".claude/settings.json",
    ".claude/portable_config.local.example.yaml",
    ".claude/statusline.py",
    ".claude/commands/create_plan.md",
    ".claude/commands/implement_plan.md",
    ".claude/commands/research_codebase.md",
    ".claude/commands/phase_complete.md",
    ".claude/commands/gitsync.md",
    ".claude/commands/resume_project.md",
    ".claude/rules/hard-constraints.md",
    ".claude/rules/phase-gates.md",
    ".claude/rules/command-execution.md",
    ".claude/rules/env-handling.md",
    ".claude/rules/diagnostics.md",
    "scripts/validate-artefacts.py",
    "README.md",
    "LICENSE",
]

# Patterns that indicate placeholder text (checked in non-doc files only)
PLACEHOLDER_PATTERNS = [
    r'TODO:?\s*\[',
    r'FIXME:?\s*\[',
    r'XXX:?\s*\[',
    r'\[INSERT\s',
    r'\[REPLACE\s',
]

# Files/directories where example placeholders are expected and OK
PLACEHOLDER_EXEMPT_PATHS = [
    'docs/',
    'examples/',
    'README.md',
    'CHANGELOG.md',
    'templates/',
]

# Patterns that might indicate sensitive data
SENSITIVE_PATTERNS = [
    r'password\s*[=:]\s*["\'][^"\']+["\']',
    r'api_?key\s*[=:]\s*["\'][^"\']+["\']',
    r'secret\s*[=:]\s*["\'][^"\']+["\']',
    r'token\s*[=:]\s*["\'][a-zA-Z0-9]{20,}["\']',
]

# Project-specific terms that should be removed
PROJECT_SPECIFIC = [
    'telosai',
    'epi_c',
    'prospect',
    'donor',
    'hnwi',
]


def check_required_files() -> list[str]:
    """Verify all required files exist."""
    issues = []
    for filepath in REQUIRED_FILES:
        if not (PACK_ROOT / filepath).exists():
            issues.append(f"Missing required file: {filepath}")
    return issues


def check_json_syntax() -> list[str]:
    """Verify JSON files parse correctly."""
    issues = []
    for json_file in PACK_ROOT.rglob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            issues.append(f"JSON syntax error in {json_file.relative_to(PACK_ROOT)}: {e}")
    return issues


def check_yaml_syntax() -> list[str]:
    """Verify YAML files parse correctly."""
    if not HAS_YAML:
        return ["PyYAML not installed - skipping YAML validation"]

    issues = []
    for yaml_file in PACK_ROOT.rglob("*.yaml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            issues.append(f"YAML syntax error in {yaml_file.relative_to(PACK_ROOT)}: {e}")

    for yml_file in PACK_ROOT.rglob("*.yml"):
        try:
            with open(yml_file, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            issues.append(f"YAML syntax error in {yml_file.relative_to(PACK_ROOT)}: {e}")

    return issues


def check_placeholders() -> list[str]:
    """Find remaining placeholder text in non-documentation files."""
    issues = []
    patterns = [re.compile(p, re.IGNORECASE) for p in PLACEHOLDER_PATTERNS]

    for filepath in PACK_ROOT.rglob("*"):
        if filepath.is_dir():
            continue
        if filepath.suffix not in ['.md', '.json', '.yaml', '.yml', '.py', '.sh', '.ps1']:
            continue
        if '.git' in filepath.parts:
            continue

        # Skip files in exempt paths (docs, examples, etc. where placeholders are expected)
        rel_path = str(filepath.relative_to(PACK_ROOT)).replace('\\', '/')
        if any(rel_path.startswith(exempt) or rel_path == exempt.rstrip('/') for exempt in PLACEHOLDER_EXEMPT_PATHS):
            continue

        try:
            content = filepath.read_text(encoding='utf-8')
            for pattern in patterns:
                if pattern.search(content):
                    issues.append(f"Placeholder found in {filepath.relative_to(PACK_ROOT)}: {pattern.pattern}")
        except (UnicodeDecodeError, PermissionError):
            pass

    return issues


def check_sensitive_data() -> list[str]:
    """Scan for potential sensitive data patterns."""
    issues = []
    patterns = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]

    for filepath in PACK_ROOT.rglob("*"):
        if filepath.is_dir():
            continue
        if filepath.suffix not in ['.md', '.json', '.yaml', '.yml', '.py', '.sh', '.ps1']:
            continue
        if '.git' in filepath.parts:
            continue

        try:
            content = filepath.read_text(encoding='utf-8')
            for pattern in patterns:
                match = pattern.search(content)
                if match:
                    issues.append(f"Potential sensitive data in {filepath.relative_to(PACK_ROOT)}: {match.group()[:50]}...")
        except (UnicodeDecodeError, PermissionError):
            pass

    return issues


def check_project_specific() -> list[str]:
    """Find project-specific terms that should be removed."""
    issues = []

    for filepath in PACK_ROOT.rglob("*"):
        if filepath.is_dir():
            continue
        if filepath.suffix not in ['.md', '.json', '.yaml', '.yml', '.py', '.sh', '.ps1']:
            continue
        if '.git' in filepath.parts:
            continue
        # Skip this validation script itself
        if filepath.name == 'validate-pack.py':
            continue

        try:
            content = filepath.read_text(encoding='utf-8').lower()
            for term in PROJECT_SPECIFIC:
                if term in content:
                    issues.append(f"Project-specific term '{term}' in {filepath.relative_to(PACK_ROOT)}")
        except (UnicodeDecodeError, PermissionError):
            pass

    return issues


def main() -> int:
    """Run all validation checks."""
    print("Claude Code RPI Plus Validator")
    print("=" * 31)
    print()

    all_issues = []

    print("Checking required files...")
    issues = check_required_files()
    all_issues.extend(issues)
    print(f"  {len(REQUIRED_FILES) - len(issues)}/{len(REQUIRED_FILES)} files present")

    print("Checking JSON syntax...")
    issues = check_json_syntax()
    all_issues.extend(issues)
    print(f"  {'PASS' if not issues else f'{len(issues)} errors'}")

    print("Checking YAML syntax...")
    issues = check_yaml_syntax()
    all_issues.extend(issues)
    print(f"  {'PASS' if not issues else f'{len(issues)} errors'}")

    print("Checking for placeholders...")
    issues = check_placeholders()
    all_issues.extend(issues)
    print(f"  {'PASS' if not issues else f'{len(issues)} found'}")

    print("Checking for sensitive data patterns...")
    issues = check_sensitive_data()
    all_issues.extend(issues)
    print(f"  {'PASS' if not issues else f'{len(issues)} potential issues'}")

    print("Checking for project-specific terms...")
    issues = check_project_specific()
    all_issues.extend(issues)
    print(f"  {'PASS' if not issues else f'{len(issues)} found'}")

    print()

    if all_issues:
        print("Issues found:")
        for issue in all_issues:
            print(f"  - {issue}")
        print()
        print(f"FAIL: {len(all_issues)} issue(s) found")
        return 1
    else:
        print("PASS: All checks passed")
        return 0


if __name__ == "__main__":
    sys.exit(main())
