# /implement_plan

You are an implementation agent. Your job is to execute an approved plan for this repo.

## Configuration

**Before executing any steps**, read `.claude/portable_config.local.yaml` to obtain:
- `project.name` - project name for checkpoint headers
- `tests.command` - test execution command
- `validator.command` - artefact validator command
- `validator.enabled` - whether to run validator (default: true)
- `ui.enabled` - whether UI smoke testing is enabled
- `ui.root` - UI directory for change detection
- `artefacts.state_dir` - where to write checkpoints

If the config file does not exist, STOP with:
```text
ERROR: Missing config file .claude/portable_config.local.yaml
Action: Copy .claude/portable_config.local.example.yaml to .claude/portable_config.local.yaml and configure.
```

## Constraints

- Read the plan and any referenced files fully before editing.
- Work phase-by-phase. After each phase, execute the Phase Gate (see below).
- Keep diffs small and focused.
- If reality (code/spec) conflicts with the plan:
  - STOP
  - Explain the discrepancy
  - Ask for guidance before continuing

## Phase Gate

After completing each phase, execute these steps in order:

### 1. Run tests
Execute the command from `tests.command` in config.
- Record: passed/failed/skipped counts
- If FAIL: record failure, continue verification, then STOP at gate verdict

### 2. Run artefact validator (if enabled)
Execute the command from `validator.command` in config (if `validator.enabled` is true).
- Record: PASS or violations
- If FAIL: record violations, continue verification, then STOP at gate verdict

### 3. Detect UI changes (if UI enabled)
If `ui.enabled` is true:
- Check `git diff --name-only` for files under the path specified in `ui.root`
- UI changed = any file path starts with `ui.root` value

### 4. Conditional UI smoke (if UI enabled)

**If UI changed AND Chrome connected:**
- Run `/ui_smoke`
- Record result (PASS/FAIL) and screenshot paths

**If UI changed AND Chrome NOT connected:**
- Record: `BLOCKED`
- STOP with message:
  ```text
  STOP: UI files changed but Chrome not connected.
  Action: Restart Claude Code with `claude --chrome` and rerun phase verification.
  ```
- Write checkpoint with BLOCKED status before halting

**If NO UI changes OR UI not enabled:**
- Record: `SKIPPED`

### 5. Write checkpoint
- Path: `{artefacts.state_dir}/phase_{X.Y}_checkpoint.md`
- Include Verification Summary section (see template below)

### 6. Write RESUME.md (only if verification PASSED)
- Path: `{artefacts.state_dir}/RESUME.md`
- Overwrite on each phase (pointer, not log)
- Format:
```markdown
# RESUME
- Plan: <relative path to current plan file>
- Latest checkpoint: <relative path to checkpoint just written>
- Git: <branch> @ <short SHA>
- Next actions:
  - <action 1>
  - <action 2> (optional)
  - <action 3> (optional)
- Verify: /phase_complete
- Blockers: <only if present; otherwise omit line>
```

### 7. Gate verdict
- If all checks PASS (or SKIPPED where appropriate): pause for human review
- If any check FAIL or BLOCKED: STOP, do not proceed (skip RESUME.md)

Do not proceed to next phase until:
1. All verification checks pass
2. Checkpoint file is written
3. RESUME.md is updated
4. Human approves continuation

## Checkpoint Template

Each checkpoint must include these sections:

```markdown
# Phase {X.Y} Checkpoint

**Status**: Complete | In Progress | Blocked
**Date**: YYYY-MM-DD

---

## Summary

[Brief overview of what was accomplished]

---

## Completed Work

[Detailed breakdown with subsections as needed]

---

## Acceptance Criteria Status

| Criterion | Status |
|-----------|--------|
| ... | done / partial / blocked |

---

## Verification Summary

| Check | Result | Detail |
|-------|--------|--------|
| Tests | PASS/FAIL | X passed, Y failed, Z skipped |
| Validator | PASS/FAIL/SKIP | violations or clean |
| UI Smoke | PASS/FAIL/SKIPPED/BLOCKED | reason |

---

## Test Results

[Test statistics: X passed, Y failed, Z skipped]
[First failure if any]

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| ... | ... |

---

## Known Limitations

[Issues or incomplete items]

---

## Next Phase

[Pointer to next checkpoint or work items]

---

## Blockers

[Any blocking issues, or "None"]

---

## Transcript

- [ ] Generate transcript if needed
- path: (link after generation)
```

## Stop Conditions

STOP immediately (after writing checkpoint) if:
- Tests failed
- Validator failed
- UI changed but Chrome not connected (when UI enabled)

Never bypass the hard constraints set out in `.claude/rules/hard-constraints.md`.
