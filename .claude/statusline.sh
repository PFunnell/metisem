#!/bin/bash
#
# Custom statusline for Claude Code phased development workflow.
# Alternative to statusline.py for environments without Python.
#
# Displays:
# - Git branch and dirty state
# - Context window usage (from stdin JSON)
#
# Note: This is a simplified version. The Python statusline.py provides
# more features including plan detection from RESUME.md.

# ANSI color codes
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
GRAY='\033[0;90m'
RESET='\033[0m'

# Read JSON from stdin (if jq is available)
if command -v jq &> /dev/null; then
    INPUT=$(cat)
    MODEL=$(echo "$INPUT" | jq -r '.model.display_name // "Claude"')
    CONTEXT=$(echo "$INPUT" | jq -r '.context_window.used_percentage // 0' | cut -d'.' -f1)
else
    MODEL="Claude"
    CONTEXT="0"
fi

# Git status
GIT_INFO=""
if git rev-parse --git-dir &> /dev/null; then
    BRANCH=$(git branch --show-current 2>/dev/null)
    if [ -n "$BRANCH" ]; then
        DIRTY=""
        if ! git diff-index --quiet HEAD 2>/dev/null; then
            DIRTY="${YELLOW}*${RESET}"
        fi
        GIT_INFO="${GREEN}${BRANCH}${DIRTY}${RESET}"
    fi
fi

# Context color
if [ "$CONTEXT" -ge 75 ]; then
    CTX_COLOR="$RED"
elif [ "$CONTEXT" -ge 50 ]; then
    CTX_COLOR="$YELLOW"
else
    CTX_COLOR="$GRAY"
fi

# Assemble status
STATUS="${BLUE}[${MODEL}]${RESET}"
[ -n "$GIT_INFO" ] && STATUS="$STATUS $GIT_INFO"
STATUS="$STATUS | ${CTX_COLOR}ctx:${CONTEXT}%${RESET}"

echo -e "$STATUS"
