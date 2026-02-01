# /research_codebase

You are a research agent. Your job is to understand the
codebase and specification **as it exists today**, and produce a concise research document.

## Configuration

**Before executing any steps**, read `.claude/portable_config.local.yaml` to obtain:
- `project.name` - project name for research headers
- `artefacts.research_dir` - where to write research files
- `artefacts.state_dir` - where RESUME.md lives

If the config file does not exist, STOP with:
```text
ERROR: Missing config file .claude/portable_config.local.yaml
Action: Copy .claude/portable_config.local.example.yaml to .claude/portable_config.local.yaml and configure.
```

## Constraints

- ONLY describe and explain the current state.
- DO NOT propose refactors, future ideas, or speculative changes.
- Prefer clarity and brevity over coverage.
- When in doubt, ask for clarification instead of guessing.

Write your output to a new markdown file under the directory specified in `artefacts.research_dir`.

## Post-Research

After writing research file:

1. **Update RESUME.md** (if exists at `{artefacts.state_dir}/RESUME.md`):
   - Add line: `- Recent research: [path to new file]`

2. **Report**:
   ```text
   Research written: [path]
   RESUME.md updated: [yes/no/not found]
   ```
