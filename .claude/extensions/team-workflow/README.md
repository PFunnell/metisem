# Team Workflow Extension

Multi-developer conventions and patterns for team collaboration.

## What This Extension Does

- Defines PR title and description conventions
- Provides code review integration checklist
- Documents multi-developer checkpoint handling
- Establishes shared state management patterns

## When to Use

**Install if**:
- Multiple developers on the project
- PR-based workflow with code review
- Need for consistent conventions across team
- Shared Claude Code usage patterns

**Skip if**:
- Solo project
- No code review process
- Personal tooling only

## Installation

### 1. Copy files to project docs

```bash
mkdir -p docs/workflow
cp .claude/extensions/team-workflow/pr-conventions.md docs/workflow/
cp .claude/extensions/team-workflow/review-checklist.md docs/workflow/
cp .claude/extensions/team-workflow/shared-state.md docs/workflow/
```

### 2. Reference in CLAUDE.md

Add to your project's CLAUDE.md:

```markdown
## Team Conventions

- PR format: `docs/workflow/pr-conventions.md`
- Review checklist: `docs/workflow/review-checklist.md`
- Checkpoint sharing: `docs/workflow/shared-state.md`
```

### 3. Configure GitHub CLI (optional)

For `/gitsync` CI status checks:

```bash
gh auth login
```

## Contents

### pr-conventions.md

Defines:
- PR title format (conventional commits style)
- Description template
- Linking to plans and checkpoints
- When to request review

### review-checklist.md

Provides:
- Pre-review self-check items
- Reviewer checklist
- Common issues to watch for
- Approval criteria

### shared-state.md

Documents:
- How multiple developers share checkpoints
- Handling concurrent work on same feature
- Merging checkpoint branches
- RESUME.md in multi-developer context

## Best Practices

### Checkpoint ownership

- One developer owns each phase
- Hand off cleanly at phase boundaries
- Update RESUME.md when taking over

### Branch strategy

```text
main
├── feature/auth
│   ├── (dev-1 works phases 1-2)
│   └── (dev-2 works phases 3-4)
└── feature/search
    └── (dev-3 works all phases)
```

### Communication

- Update checkpoint before switching developers
- Mention blockers in checkpoint
- Use PR comments for async discussion
