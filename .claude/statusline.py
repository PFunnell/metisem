#!/usr/bin/env python3
"""Custom statusline for Claude Code phased development workflow.

Displays:
- Current model
- Git branch and dirty state
- Active plan (from RESUME.md)
- Context window usage with color warnings
"""
import json
import sys
import subprocess
import os
from pathlib import Path

# Read JSON from stdin (Claude Code provides workspace context)
try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, Exception):
    data = {}

# Extract fields with fallbacks
model = data.get('model', {}).get('display_name', 'Claude')
context_used = data.get('context_window', {}).get('used_percentage', 0)
cwd = data.get('workspace', {}).get('current_dir', os.getcwd())

# ANSI color codes
BLUE = '\033[0;34m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
CYAN = '\033[0;36m'
GRAY = '\033[0;90m'
RESET = '\033[0m'


def get_git_info(cwd: str) -> str:
    """Get git branch and dirty status."""
    try:
        # Check if we're in a git repo
        subprocess.run(['git', 'rev-parse', '--git-dir'],
                       capture_output=True, check=True, cwd=cwd)

        # Get current branch
        result = subprocess.run(['git', 'branch', '--show-current'],
                              capture_output=True, text=True, cwd=cwd)
        branch = result.stdout.strip()

        if branch:
            # Check for uncommitted changes
            dirty = ""
            result = subprocess.run(['git', 'diff-index', '--quiet', 'HEAD'],
                                  capture_output=True, cwd=cwd)
            if result.returncode != 0:
                dirty = f"{YELLOW}*{RESET}"

            return f"{GREEN}{branch}{dirty}{RESET}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return ""


def get_plan_info(cwd: str) -> str:
    """Extract current plan from RESUME.md."""
    # Try common state directory locations
    possible_paths = [
        Path(cwd) / "docs" / "state" / "RESUME.md",
        Path(cwd) / "thoughts" / "shared" / "state" / "RESUME.md",
    ]

    for resume_file in possible_paths:
        if resume_file.exists():
            try:
                content = resume_file.read_text(encoding='utf-8')
                for line in content.splitlines():
                    if line.startswith('- Plan:'):
                        plan_path = line.split()[2] if len(line.split()) > 2 else ""
                        if plan_path:
                            plan_name = Path(plan_path).stem
                            # Extract topic from plan name
                            # e.g., "feature_auth_implementation" -> "Auth"
                            if '_implementation' in plan_name:
                                parts = plan_name.replace('_implementation', '').split('_', 1)
                                if len(parts) >= 2:
                                    topic = ' '.join(word.capitalize() for word in parts[1].split('_'))
                                    return f"{CYAN}{topic}{RESET}"
                            # Fallback: truncate long names
                            return f"{CYAN}{plan_name[:20]}{RESET}"
                        break
            except Exception:
                pass

    return ""


def get_context_info(context_used: float) -> str:
    """Format context window usage with color based on percentage."""
    context_int = int(round(context_used))
    if context_int >= 75:
        return f"{RED}ctx:{context_int}%{RESET}"
    elif context_int >= 50:
        return f"{YELLOW}ctx:{context_int}%{RESET}"
    else:
        return f"{GRAY}ctx:{context_int}%{RESET}"


# Assemble status line
status = f"{BLUE}[{model}]{RESET}"

git_info = get_git_info(cwd)
if git_info:
    status += f" {git_info}"

plan_info = get_plan_info(cwd)
if plan_info:
    status += f" | {plan_info}"

status += f" | {get_context_info(context_used)}"

print(status)
