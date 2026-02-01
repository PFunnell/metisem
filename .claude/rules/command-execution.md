# Command Execution

## Shell Rules

- **PowerShell encoding**: Avoid Unicode chars; use [OK]/[FAIL] not checkmarks
- **pytest conflicts**: Use `-o addopts=""` to clear pyproject.toml defaults
- **Permission patterns**: Pipes/redirects/chaining bypass matching; avoid them

## Tool Preference

Use Claude Code tools over bash:
- Read tool, not `cat`/`head`/`tail`
- Grep tool, not `grep`/`rg`
- Glob tool, not `find`/`ls`
- Edit tool, not `sed`/`awk`
- Write tool, not `echo >`

Bash is for: git, npm/pip, pytest, database CLIs, actual shell commands.

## Descriptions

All Bash commands need clear `description` parameter for permission prompts.
