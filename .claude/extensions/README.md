# Extensions

Optional modules for specific use cases. Install by copying files to parent directories.

## Available Extensions

| Extension | Use Case | Install Complexity |
|-----------|----------|-------------------|
| ui-smoke | Web applications with browser UI | Medium (requires Chrome) |
| data-contracts | APIs, databases, complex data models | Low |
| team-workflow | Multi-developer projects | Low |

## Installation

Each extension contains a README with specific installation instructions. General pattern:

1. Read the extension's README to understand prerequisites
2. Copy command files to `.claude/commands/`
3. Copy rule files to `.claude/rules/`
4. Update `.claude/portable_config.local.yaml` if needed
5. Add permission entries to `.claude/settings.local.json` if needed

## When to Use

### ui-smoke

**Install if**: Your project has a web frontend that should be verified after changes

**Skip if**: CLI tool, library, backend-only service

**Prerequisites**:
- Claude Code started with `--chrome` flag
- Chrome browser installed
- UI dev server running

**What it adds**:
- `/ui_smoke` command for browser-based verification
- Automatic UI change detection in phase gates
- Screenshot evidence collection

### data-contracts

**Install if**: Project has data models, API contracts, or database schemas that must stay synchronized

**Skip if**: Simple scripts, no structured data

**What it adds**:
- Data dictionary protocol rule
- Template for documenting models
- Phase gate integration for model changes

### team-workflow

**Install if**: Multiple developers, shared conventions needed, PR-based workflow

**Skip if**: Solo project, personal tooling

**What it adds**:
- PR title/description format conventions
- Code review checklist integration
- Multi-developer checkpoint handling patterns

## Localization Considerations

Extensions may need adjustment for:

- **Language**: Command descriptions assume English; translate if needed
- **Paths**: Unix vs Windows separators (use forward slashes in YAML configs)
- **Tools**: Some extensions assume specific CLIs:
  - ui-smoke: Chrome browser
  - team-workflow: GitHub CLI (`gh`)

## Creating Custom Extensions

To create your own extension:

1. Create a directory under `.claude/extensions/your-extension/`
2. Include a README.md explaining:
   - What the extension does
   - Prerequisites
   - Installation steps
   - Configuration options
3. Prefix command files for clarity (e.g., `your_extension_command.md`)
4. Test independently before integrating with phase gates

## Uninstalling Extensions

1. Remove copied files from `.claude/commands/` and `.claude/rules/`
2. Remove related entries from `.claude/settings.local.json`
3. Remove related config from `.claude/portable_config.local.yaml`
4. Delete the extension directory (optional - doesn't affect installed copies)
