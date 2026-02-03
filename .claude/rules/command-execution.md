# Command Execution

## Shell Type

This environment runs **bash** (not PowerShell or cmd).

## Critical Shell Rules

1. **Command chaining**: Use `&&` for sequential commands, NOT `&amp;&amp;`
   - Example: `cd /path && python script.py` (CORRECT)
   - Never: `cd /path &amp;&amp; python script.py` (XML-escaped, WRONG)

2. **Windows paths in bash**:
   - Quote paths with spaces: `cd "D:\path with spaces"`
   - Or use forward slashes: `cd D:/dev/project`
   - Prefer absolute Python invocation: `python D:/full/path/script.py`
   - Avoid unnecessary `cd` by using absolute paths

3. **Python scripts**: Call directly with absolute paths
   - Good: `python D:/dev/project/script.py`
   - Avoid: `cd D:\dev\project && python script.py`

4. **Permission patterns**: Pipes/redirects/chaining bypass matching; avoid when possible

5. **Output encoding**: Use `[OK]`/`[FAIL]` not Unicode checkmarks

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
