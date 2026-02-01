# Shared State Management

Patterns for multi-developer checkpoint and session handling.

## RESUME.md in Team Context

### Single developer per feature

The simplest pattern: one developer owns a feature branch.

```text
feature/auth
├── RESUME.md        # Developer A maintains
├── checkpoints/     # Developer A writes
└── plans/           # Shared reference
```

### Developer handoff

When switching developers mid-feature:

1. **Outgoing developer**:
   - Complete current phase
   - Write checkpoint with all context
   - Update RESUME.md with explicit next actions
   - Commit: `chore: handoff to [incoming dev]`

2. **Incoming developer**:
   - Read RESUME.md first
   - Read linked checkpoint
   - Read linked plan
   - Run `/resume_project` to verify understanding
   - Confirm with outgoing dev before starting

### RESUME.md handoff format

```markdown
# RESUME

- Plan: docs/plans/auth_implementation.md
- Latest checkpoint: docs/state/phase_2.1_checkpoint.md
- Git: feature/auth @ abc1234
- **Handoff to**: @developer-b
- **Handoff context**: Phase 2 complete, phase 3 ready to start
- Next actions:
  - Implement password reset endpoint
  - Add email service integration
  - Write tests for reset flow
- Blockers: Email service API key needed
```

## Parallel Development

When multiple developers work on same codebase:

### Separate feature branches

```text
main
├── feature/auth     (dev-a)
├── feature/search   (dev-b)
└── feature/checkout (dev-c)
```

Each maintains own RESUME.md. Merge conflicts are rare.

### Same feature, different phases

```text
feature/large-feature
├── phase-1-2 (dev-a)    # Merged when complete
└── phase-3-4 (dev-b)    # Started after phase 2 merges
```

Wait for clean handoff points (completed phases).

### Concurrent phases (advanced)

Only when phases are truly independent:

```text
feature/large-feature
├── phase-1 (dev-a)      # Backend models
└── phase-2 (dev-b)      # Frontend components
```

Requires:
- Clear interface contracts
- Frequent sync
- Careful merge strategy

## Checkpoint Conflicts

### Prevention

- Each phase has single owner
- Don't edit others' in-progress checkpoints
- Use git branches to isolate work

### Resolution

If checkpoints conflict:

1. Keep both versions temporarily
2. Sync with other developer
3. Consolidate into single authoritative checkpoint
4. Delete duplicate

### Checkpoint naming

Avoid conflicts with developer prefixes:

```text
docs/state/phase_2.1_checkpoint_dev-a.md    # During parallel work
docs/state/phase_2.1_checkpoint.md          # After consolidation
```

## Communication Patterns

### Async (PR comments)

- Link to checkpoint: "Context: docs/state/phase_2.1_checkpoint.md"
- Tag blockers: "Blocked: waiting for API key"
- Request handoff: "Ready for handoff @dev-b"

### Sync (standup/chat)

- "Taking over auth feature from phase 3"
- "Blocked on email service, switching to search"
- "Merging auth today, will conflict with checkout"

## Merge Strategy

### Feature complete

```bash
# On feature branch
git fetch origin main
git rebase origin/main    # or merge
# Resolve conflicts
# Run tests
git push
# Create PR
```

### Partial handoff

```bash
# Outgoing developer
git commit -m "chore: handoff checkpoint"
git push

# Incoming developer
git fetch
git checkout feature/branch
# Read RESUME.md, then continue
```

## Best Practices

1. **Communicate handoffs explicitly** - Don't assume
2. **Complete phases before handoff** - Clean boundaries
3. **Update RESUME.md before switching** - Context is everything
4. **Use draft PRs for visibility** - Show work in progress
5. **Sync before major merges** - Avoid surprise conflicts
