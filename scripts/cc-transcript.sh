#!/bin/bash
#
# Capture Claude Code transcript as HTML evidence.
#
# Runs uvx claude-code-transcripts to generate HTML output,
# stores in docs/transcripts/YYYY-MM-DD/YYYY-MM-DD_HHmm__<scope_slug>/,
# and appends an index line to docs/transcripts/README.md.
#
# Usage:
#   ./cc-transcript.sh [scope] [limit]
#
# Examples:
#   ./cc-transcript.sh
#   ./cc-transcript.sh "phase-2.1"
#   ./cc-transcript.sh "phase-2.1" 50

set -e

SCOPE="${1:-work}"
LIMIT="${2:-30}"

# Derive scope slug (lowercase, replace spaces/special chars with hyphens)
SCOPE_SLUG=$(echo "$SCOPE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-zA-Z0-9-]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//')
[ -z "$SCOPE_SLUG" ] && SCOPE_SLUG="work"

# Timestamps
DATE_FOLDER=$(date +"%Y-%m-%d")
TIMESTAMP=$(date +"%Y-%m-%d_%H%M")

# Build output path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
TRANSCRIPTS_ROOT="$REPO_ROOT/docs/transcripts"
DATE_PATH="$TRANSCRIPTS_ROOT/$DATE_FOLDER"
OUT_DIR="$DATE_PATH/${TIMESTAMP}__${SCOPE_SLUG}"

# Ensure directories exist
mkdir -p "$OUT_DIR"

echo "Capturing transcript to: $OUT_DIR"

# Auto-detect GitHub repo from git remote
GIT_REPO=""
REMOTE_URL=$(git -C "$REPO_ROOT" remote get-url origin 2>/dev/null || true)
if [[ "$REMOTE_URL" =~ github\.com[:/]([^/]+/[^/]+)(\.git)?$ ]]; then
    GIT_REPO="${BASH_REMATCH[1]}"
    echo "Detected GitHub repo: $GIT_REPO"
fi

# Run uvx claude-code-transcripts
if [ -n "$GIT_REPO" ]; then
    uvx claude-code-transcripts local -o "$OUT_DIR" --repo "$GIT_REPO" --limit "$LIMIT"
else
    uvx claude-code-transcripts local -o "$OUT_DIR" --limit "$LIMIT"
fi

# Verify output was created
INDEX_HTML="$OUT_DIR/index.html"
if [ ! -f "$INDEX_HTML" ]; then
    # Clean up empty directory
    rmdir "$OUT_DIR" 2>/dev/null || true
    echo "No transcript generated (cancelled or no session selected)."
    exit 1
fi

# Append index line to README.md
README_PATH="$TRANSCRIPTS_ROOT/README.md"
RELATIVE_PATH="docs/transcripts/$DATE_FOLDER/${TIMESTAMP}__${SCOPE_SLUG}/"
INDEX_LINE="- ${TIMESTAMP}: $SCOPE ($RELATIVE_PATH)"

if [ ! -f "$README_PATH" ]; then
    # Create README with header if missing
    cat > "$README_PATH" << 'EOF'
# Claude Code Transcripts

Execution transcripts captured from Claude Code sessions.
These are evidence artefacts, not working context.

Each entry corresponds to a completed work package or phase.

EOF
fi

echo "$INDEX_LINE" >> "$README_PATH"

echo "Transcript captured successfully."
echo "Index entry added: $INDEX_LINE"
