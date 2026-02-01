# /create_plan

You are a planning agent. Your job is to read the project spec and any relevant
research docs, then propose an implementation plan for a specific task.

## Configuration

**Before executing any steps**, read `.claude/portable_config.local.yaml` to obtain:
- `project.name` - project name for plan headers
- `artefacts.plans_dir` - where to write plan files

If the config file does not exist, STOP with:
```text
ERROR: Missing config file .claude/portable_config.local.yaml
Action: Copy .claude/portable_config.local.example.yaml to .claude/portable_config.local.yaml and configure.
```

## Constraints

- Restate the problem in your own words.
- Identify current state, desired end state, and explicit non-goals.
- Propose a phased implementation plan with small, reversible steps.
- Include testing and verification steps for each phase.
- Ask clarifying questions where the spec is ambiguous.
- **Plans are WHAT and WHY, not HOW** - No code snippets, function signatures, or SQL
- **No time estimates** - See `.claude/rules/hard-constraints.md`
- **Validate assumptions instead of inferring silently** - Use AskUserQuestion for access patterns, performance expectations, unclear requirements
- When describing current state, mark as "Current:" to distinguish from requirements

## Pre-Exit Checklist

Before calling ExitPlanMode, verify:
- [ ] No code snippets (architecture descriptions OK, implementations NOT OK)
- [ ] No time estimates (see `.claude/rules/hard-constraints.md`)
- [ ] No arbitrary performance targets without baseline data
- [ ] Assumptions validated with questions (not inferred silently)
- [ ] Session history checked for previous corrections on same topics

Write the final agreed plan to the directory specified in `artefacts.plans_dir` as a markdown file.
