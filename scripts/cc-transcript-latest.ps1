<#
.SYNOPSIS
    Capture transcript for the most recent Claude Code session (non-interactive).

.DESCRIPTION
    Automatically selects the most recent session from Claude Code's local storage
    and generates an HTML transcript. Useful for programmatic execution.

.PARAMETER Scope
    Label for this transcript (default: "work"). Used in folder name and index.

.PARAMETER Limit
    Number of most recent sessions to consider (default: 30)

.EXAMPLE
    .\cc-transcript-latest.ps1
    .\cc-transcript-latest.ps1 -Scope "post-phase-1.2"
#>

param(
    [string]$Scope = "work",
    [int]$Limit = 30
)

$ErrorActionPreference = "Stop"

# Derive scope slug (lowercase, replace spaces/special chars with hyphens)
$scopeSlug = ($Scope -replace '[^a-zA-Z0-9-]', '-').ToLower()
$scopeSlug = $scopeSlug -replace '-+', '-'
$scopeSlug = $scopeSlug.Trim('-')
if (-not $scopeSlug) { $scopeSlug = "work" }

# Timestamps
$now = Get-Date
$dateFolder = $now.ToString("yyyy-MM-dd")
$timestamp = $now.ToString("yyyy-MM-dd_HHmm")

# Build output path
$repoRoot = Split-Path -Parent $PSScriptRoot
$transcriptsRoot = Join-Path $repoRoot "docs\transcripts"
$datePath = Join-Path $transcriptsRoot $dateFolder
$outDir = Join-Path $datePath "${timestamp}__${scopeSlug}"

# Ensure directories exist
if (-not (Test-Path $transcriptsRoot)) {
    New-Item -ItemType Directory -Path $transcriptsRoot -Force | Out-Null
}
if (-not (Test-Path $datePath)) {
    New-Item -ItemType Directory -Path $datePath -Force | Out-Null
}
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

Write-Host "Capturing transcript to: $outDir"

# Auto-detect GitHub repo from git remote
$gitRepo = $null
try {
    $remoteUrl = git -C $repoRoot remote get-url origin 2>$null
    if ($remoteUrl -match 'github\.com[:/]([^/]+/[^/]+?)(\.git)?$') {
        $gitRepo = $Matches[1]
        Write-Host "Detected GitHub repo: $gitRepo"
    }
}
catch {
    # Ignore - repo detection is optional
}

# Find Claude Code session files
$claudeConfigDir = Join-Path $env:USERPROFILE ".claude"
$projectsDir = Join-Path $claudeConfigDir "projects"

# Get normalized repo path for matching (Claude uses -- for :\, - for \)
$normalizedRepoRoot = $repoRoot.Replace(':\', '--').Replace('\', '-')

# Find project directory for this repo
$projectDir = Get-ChildItem -Path $projectsDir -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "*$normalizedRepoRoot*" } |
    Select-Object -First 1

if (-not $projectDir) {
    Write-Host "Error: Could not find Claude Code project directory for this repo"
    Write-Host "Expected pattern: *$normalizedRepoRoot*"
    Write-Host "Searched in: $projectsDir"
    exit 1
}

Write-Host "Found project directory: $($projectDir.Name)"

# Find most recent .jsonl session file
$sessionFiles = Get-ChildItem -Path $projectDir.FullName -Filter "*.jsonl" -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $sessionFiles) {
    Write-Host "Error: No session files found in $($projectDir.FullName)"
    exit 1
}

$latestSession = $sessionFiles
Write-Host "Latest session: $($latestSession.Name) (modified: $($latestSession.LastWriteTime))"

# Build uvx command with explicit session file (use 'json' command, not 'local')
$sessionPath = $latestSession.FullName

if ($gitRepo) {
    Write-Host "Running: uvx claude-code-transcripts json -o `"$outDir`" --repo `"$gitRepo`" `"$sessionPath`""
    uvx claude-code-transcripts json -o "$outDir" --repo "$gitRepo" "$sessionPath"
} else {
    Write-Host "Running: uvx claude-code-transcripts json -o `"$outDir`" `"$sessionPath`""
    uvx claude-code-transcripts json -o "$outDir" "$sessionPath"
}

# Verify output was created
$indexHtml = Join-Path $outDir "index.html"
if (-not (Test-Path $indexHtml)) {
    # Clean up empty directory
    if ((Get-ChildItem $outDir -Force | Measure-Object).Count -eq 0) {
        Remove-Item $outDir -Force
    }
    Write-Host "Error: Transcript generation failed - no index.html created"
    exit 1
}

# Append index line to README.md
$readmePath = Join-Path $transcriptsRoot "README.md"
$relativePath = "docs/transcripts/$dateFolder/${timestamp}__${scopeSlug}/"
$indexLine = "- ${timestamp}: $Scope ($relativePath)"

if (-not (Test-Path $readmePath)) {
    # Create README with header if missing
    $header = @"
# Claude Code Transcripts

Execution transcripts captured from Claude Code sessions.
These are evidence artefacts, not working context.

Each entry corresponds to a completed work package or phase.

"@
    Set-Content -Path $readmePath -Value $header -Encoding UTF8
}

Add-Content -Path $readmePath -Value $indexLine -Encoding UTF8

Write-Host ""
Write-Host "SUCCESS: Transcript captured"
Write-Host "  Output: $relativePath"
Write-Host "  Index entry: $indexLine"
Write-Host ""
