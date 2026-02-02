#!/usr/bin/env bash
#
# Capture transcript for the most recent Claude Code session (non-interactive).
#
# Usage:
#   ./cc-transcript-latest.sh [scope]
#
# Examples:
#   ./cc-transcript-latest.sh
#   ./cc-transcript-latest.sh post-phase-1.2

set -euo pipefail

SCOPE="${1:-work}"
LIMIT=30

# Derive scope slug (lowercase, replace special chars with hyphens)
scope_slug=$(echo "$SCOPE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g' | sed 's/-\+/-/g' | sed 's/^-//;s/-$//')
[ -z "$scope_slug" ] && scope_slug="work"

# Timestamps
date_folder=$(date +%Y-%m-%d)
timestamp=$(date +%Y-%m-%d_%H%M)

# Build output path
repo_root=$(cd "$(dirname "$0")/.." && pwd)
transcripts_root="$repo_root/docs/transcripts"
date_path="$transcripts_root/$date_folder"
out_dir="$date_path/${timestamp}__${scope_slug}"

# Ensure directories exist
mkdir -p "$transcripts_root"
mkdir -p "$date_path"
mkdir -p "$out_dir"

echo "Capturing transcript to: $out_dir"

# Auto-detect GitHub repo from git remote
git_repo=""
if git_remote=$(git -C "$repo_root" remote get-url origin 2>/dev/null); then
    if [[ "$git_remote" =~ github\.com[:/]([^/]+/[^/]+)(\.git)?$ ]]; then
        git_repo="${BASH_REMATCH[1]}"
        echo "Detected GitHub repo: $git_repo"
    fi
fi

# Find Claude Code session files
claude_config_dir="$HOME/.claude"
projects_dir="$claude_config_dir/projects"

if [ ! -d "$projects_dir" ]; then
    echo "Error: Claude projects directory not found: $projects_dir"
    exit 1
fi

# Get normalized repo path for matching (Claude uses -- for :/, - for remaining / or \)
normalized_repo_root=$(echo "$repo_root" | sed 's|:/|--|g' | sed 's|:\\|--|g' | sed 's|/|-|g' | sed 's|\\|-|g')

# Find project directory for this repo
project_dir=$(find "$projects_dir" -maxdepth 1 -type d -name "*$normalized_repo_root*" | head -1)

if [ -z "$project_dir" ]; then
    echo "Error: Could not find Claude Code project directory for this repo"
    echo "Expected pattern: *$normalized_repo_root*"
    echo "Searched in: $projects_dir"
    exit 1
fi

echo "Found project directory: $(basename "$project_dir")"

# Find most recent .jsonl session file
latest_session=$(find "$project_dir" -maxdepth 1 -name "*.jsonl" -type f -printf "%T@ %p\n" 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)

if [ -z "$latest_session" ]; then
    echo "Error: No session files found in $project_dir"
    exit 1
fi

session_mtime=$(stat -c %y "$latest_session" 2>/dev/null || stat -f "%Sm" "$latest_session" 2>/dev/null || echo "unknown")
echo "Latest session: $(basename "$latest_session") (modified: $session_mtime)"

# Build uvx command with explicit session file (use 'json' command, not 'local')
if [ -n "$git_repo" ]; then
    echo "Running: uvx claude-code-transcripts json -o \"$out_dir\" --repo \"$git_repo\" \"$latest_session\""
    uvx claude-code-transcripts json -o "$out_dir" --repo "$git_repo" "$latest_session"
else
    echo "Running: uvx claude-code-transcripts json -o \"$out_dir\" \"$latest_session\""
    uvx claude-code-transcripts json -o "$out_dir" "$latest_session"
fi

# Verify output was created
index_html="$out_dir/index.html"
if [ ! -f "$index_html" ]; then
    # Clean up empty directory
    if [ -z "$(ls -A "$out_dir")" ]; then
        rmdir "$out_dir"
    fi
    echo "Error: Transcript generation failed - no index.html created"
    exit 1
fi

# Append index line to README.md
readme_path="$transcripts_root/README.md"
relative_path="docs/transcripts/$date_folder/${timestamp}__${scope_slug}/"
index_line="- ${timestamp}: $SCOPE ($relative_path)"

if [ ! -f "$readme_path" ]; then
    # Create README with header if missing
    cat > "$readme_path" << 'EOF'
# Claude Code Transcripts

Execution transcripts captured from Claude Code sessions.
These are evidence artefacts, not working context.

Each entry corresponds to a completed work package or phase.

EOF
fi

echo "$index_line" >> "$readme_path"

echo ""
echo "SUCCESS: Transcript captured"
echo "  Output: $relative_path"
echo "  Index entry: $index_line"
echo ""
