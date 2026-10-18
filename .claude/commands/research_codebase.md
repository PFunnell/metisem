# /research_codebase

You are a research agent. Your job is to understand the
codebase and specification **as it exists today**, and produce a concise research document.

## Constraints

- ONLY describe and explain the current state.
- DO NOT propose refactors, future ideas, or speculative changes.
- Prefer clarity and brevity over coverage.
- When in doubt, ask for clarification instead of guessing.

Write your output to `docs/research/<topic>_research.md`. That folder is gitignored, so the file stays local.

## Post-Research

Add one line for the new file to `docs/index.md`, then report:

```text
Research written: [path]
```
