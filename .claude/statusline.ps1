# Custom statusline for Claude Code phased development workflow.
# Alternative to statusline.py for PowerShell-native environments.
#
# Note: This is a simplified version. The Python statusline.py provides
# more features including plan detection from RESUME.md.

# Read JSON from stdin
$input = $null
try {
    $input = $Input | ConvertFrom-Json
} catch {
    # Ignore parse errors
}

# Extract values with defaults
$model = "Claude"
$context = 0
if ($input) {
    if ($input.model.display_name) { $model = $input.model.display_name }
    if ($input.context_window.used_percentage) { $context = [int]$input.context_window.used_percentage }
}

# ANSI escape codes
$ESC = [char]27
$BLUE = "$ESC[0;34m"
$GREEN = "$ESC[0;32m"
$YELLOW = "$ESC[1;33m"
$RED = "$ESC[0;31m"
$GRAY = "$ESC[0;90m"
$RESET = "$ESC[0m"

# Git status
$gitInfo = ""
try {
    $null = git rev-parse --git-dir 2>$null
    if ($LASTEXITCODE -eq 0) {
        $branch = git branch --show-current 2>$null
        if ($branch) {
            $dirty = ""
            git diff-index --quiet HEAD 2>$null
            if ($LASTEXITCODE -ne 0) {
                $dirty = "$YELLOW*$RESET"
            }
            $gitInfo = "$GREEN$branch$dirty$RESET"
        }
    }
} catch {
    # Ignore git errors
}

# Context color
if ($context -ge 75) {
    $ctxColor = $RED
} elseif ($context -ge 50) {
    $ctxColor = $YELLOW
} else {
    $ctxColor = $GRAY
}

# Assemble status
$status = "$BLUE[$model]$RESET"
if ($gitInfo) { $status += " $gitInfo" }
$status += " | ${ctxColor}ctx:${context}%$RESET"

Write-Host $status
