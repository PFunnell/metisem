# Claude Code Configuration

## Quick Start

1. Copy `portable_config.local.example.yaml` to `portable_config.local.yaml`
2. Edit with your project settings
3. Optionally add `settings.local.json` for machine-specific overrides

## Files

| File | Committed | Purpose |
|------|-----------|---------|
| `settings.json` | Yes | Baseline permissions |
| `settings.local.json` | No | User-specific permissions |
| `portable_config.local.yaml` | No | Project configuration |
| `statusline.py` | Yes | Custom statusline |
| `commands/` | Yes | Custom slash commands |
| `rules/` | Yes | Behavioral constraints (auto-loaded) |
| `extensions/` | Yes | Optional modules |

**Note**: `commands/` still works, but `.claude/skills/` is the modern pattern for new projects.

## Rules Loading

Claude Code automatically loads all `.md` files from `.claude/rules/`. No configuration needed.

**Precedence** (highest priority last):
1. `~/.claude/rules/` - User-level (all your projects)
2. `./.claude/rules/` - Project-level (this project, overrides user-level)

**When to use each**:
- **User-level** (`~/.claude/rules/`): Personal preferences across all projects (e.g., output style)
- **Project-level** (`./.claude/rules/`): Team conventions committed to repo (e.g., workflow rules)

## Settings Precedence

1. `settings.json` - team baseline
2. `settings.local.json` - personal overrides (extends, doesn't replace)

## Permissions

**Prefer generic patterns**: `"Bash(python:*)"` over absolute paths.

**Known limitation**: Pipes/redirects/chaining bypass permission matching.

**Never put credentials in settings files** - use `.env` instead.

## Commands

| Command | Purpose |
|---------|---------|
| `/create_plan` | Propose implementation plans |
| `/implement_plan` | Execute plans phase-by-phase |
| `/research_codebase` | Analyse current state |
| `/phase_complete` | Verify phase gate criteria |
| `/gitsync` | Stage, commit, push |
| `/resume_project` | Restore session context |

## Extensions

See `extensions/README.md`:
- `ui-smoke/` - Browser verification
- `data-contracts/` - Schema governance
- `team-workflow/` - Multi-developer patterns
