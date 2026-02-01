# /phase_complete

Single entry point for verifying "done-ness" before commit or next phase.

## Configuration

**Before executing any steps**, read `.claude/portable_config.local.yaml` to obtain:
- `tests.command` - test execution command
- `validator.command` - artefact validator command
- `validator.enabled` - whether to run validator (default: true)
- `ui.enabled` - whether UI smoke testing is enabled
- `ui.root` - UI directory for change detection
- `artefacts.verification_dir` - where to write verification reports

If the config file does not exist, STOP with:
```text
ERROR: Missing config file .claude/portable_config.local.yaml
Action: Copy .claude/portable_config.local.example.yaml to .claude/portable_config.local.yaml and configure.
```

## Execution Steps

### 1. Check git status
```bash
git status
```
- Report: clean or dirty (list modified/untracked files)
- Do NOT stop on dirty state; just report it

### 2. Run tests
Execute the command from `tests.command` in config.
- Capture: passed/failed/skipped counts
- If tests FAIL: record failure, continue to step 3, then STOP at verdict

### 3. Run artefact validator (if enabled)
If `validator.enabled` is true, execute the command from `validator.command` in config.
- Capture: PASS or violations
- If validator FAIL: record violations, continue to step 4, then STOP at verdict

### 4. Detect UI changes (if UI enabled)
If `ui.enabled` is true:
- Check `git status` and `git diff --name-only` for files under the path specified in `ui.root`
- UI changed = any file path starts with `ui.root` value

### 5. Conditional UI smoke (if UI enabled)

**If UI changed AND Chrome connected:**
- Run `/ui_smoke`
- Record result (PASS/FAIL) and screenshot paths

**If UI changed AND Chrome NOT connected:**
- Record: `BLOCKED`
- STOP with message:
  ```text
  STOP: UI files changed but Chrome not connected.
  Action: Restart Claude Code with `claude --chrome` and rerun /phase_complete.
  ```
- Write verification artefact with STOP verdict before halting

**If NO UI changes OR UI not enabled:**
- Record: `SKIPPED`
- Continue to verdict

### 6. Write verification artefact
- Path: `{artefacts.verification_dir}/verify_<YYYYMMDD>_<HHMM>.md`
- Template:

```markdown
# Verification Report

**Date**: YYYY-MM-DD HH:MM
**Command**: /phase_complete

---

## Git Status

[clean/dirty + file list if dirty]

---

## Tests

| Result | Count |
|--------|-------|
| Passed | X |
| Failed | Y |
| Skipped | Z |

[First failure if any]

---

## Artefact Validator

| Result | Detail |
|--------|--------|
| PASS/FAIL/SKIP | violations or "All artefacts in expected locations" |

---

## UI Smoke

| Result | Detail |
|--------|--------|
| PASS/FAIL/SKIPPED/BLOCKED | reason |

- UI files changed: Yes/No/N/A
- Chrome connected: Yes/No/N/A
- Screenshots: [paths] or N/A

---

## Verdict

PASS: Ready for commit/next phase
- or -
STOP: [reason - first failure encountered]
```

### 7. Report verdict

Display validation summary table:

| Check | Status | Detail |
|-------|--------|--------|
| Tests | PASS/FAIL | X passed, Y failed, Z skipped |
| Artefacts | PASS/FAIL/SKIP | validator result |
| UI smoke | PASS/SKIP/BLOCK | reason |

**Verdict**: PASS or STOP: [first failure reason]
**Artefact**: [path to verification file]

- If all checks PASS (or SKIPPED where appropriate): report PASS
- If any check FAIL or BLOCKED: report STOP with reason

### 8. Post-verdict prompts (on PASS only)

If verdict is PASS:
1. **Transcript reminder**: "Remember: `scripts/cc-transcript.ps1` (or .sh) for session evidence"
2. **Context check**: If session is long, suggest context management before next phase

## Stop Conditions

STOP immediately (after writing artefact) if:
- Tests failed
- Validator failed (if enabled)
- UI changed but Chrome not connected (if UI enabled)

## Constraints

- Do NOT skip UI smoke when UI files changed (if UI enabled)
- Do NOT proceed silently when Chrome not connected for UI changes
- Always write verification artefact, even on STOP
- Never bypass the hard constraints in `.claude/rules/hard-constraints.md`
