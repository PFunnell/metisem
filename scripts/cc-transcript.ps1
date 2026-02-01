<#
.SYNOPSIS
    Capture Claude Code transcript as HTML evidence.

.DESCRIPTION
    Runs uvx claude-code-transcripts to generate HTML output,
    stores in docs/transcripts/YYYY-MM-DD/YYYY-MM-DD_HHmm__<scope_slug>/,
    and appends an index line to docs/transcripts/README.md.

.PARAMETER Scope
    Label for this transcript (default: "work"). Used in folder name and index.

.EXAMPLE
    .\cc-transcript.ps1
    .\cc-transcript.ps1 -Scope "phase-2.1"
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

# Run uvx claude-code-transcripts
if ($gitRepo) {
    uvx claude-code-transcripts local -o "$outDir" --repo "$gitRepo" --limit $Limit
} else {
    uvx claude-code-transcripts local -o "$outDir" --limit $Limit
}

# Verify output was created
$indexHtml = Join-Path $outDir "index.html"
if (-not (Test-Path $indexHtml)) {
    # Clean up empty directory
    if ((Get-ChildItem $outDir -Force | Measure-Object).Count -eq 0) {
        Remove-Item $outDir -Force
    }
    Write-Host "No transcript generated (cancelled or no session selected)."
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

Write-Host "Transcript captured successfully."
Write-Host "Index entry added: $indexLine"
