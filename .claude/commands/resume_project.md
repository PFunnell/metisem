# /resume_project

Restore session context from RESUME.md.

## Configuration

Read `.claude/portable_config.local.yaml` for `artefacts.state_dir`.

If the config file does not exist, STOP with:
```text
ERROR: Missing config file .claude/portable_config.local.yaml
Action: Copy .claude/portable_config.local.example.yaml to .claude/portable_config.local.yaml and configure.
```

## Steps

1. **Read RESUME.md** from `{state_dir}/RESUME.md`
   - If not found: "No RESUME.md. Starting fresh."

2. **Load referenced files**:
   - Plan file (scope, current phase)
   - Checkpoint file (status, known issues)

3. **Check git state**:
   - Compare current HEAD to RESUME.md reference
   - Note drift if any

4. **Present summary**:
   ```text
   Plan: [name] - Phase [X] of [Y]
   Status: [from checkpoint]
   Git: [HEAD] [matches/diverged from RESUME.md]
   Next: [actions from RESUME.md]
   Issues: [from checkpoint or "None"]
   ```

5. **Await direction** - do not start work without user confirmation

## Constraints

- Read-only: do not modify files
- Concise: user can ask for details
- See `.claude/rules/phase-gates.md` for RESUME.md format
