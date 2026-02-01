# PR Conventions

Standards for pull request titles and descriptions.

## Title Format

Use conventional commit format:

```text
type(scope): brief description
```

### Types

| Type | When to Use |
|------|-------------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `refactor` | Code restructuring without behavior change |
| `test` | Adding or modifying tests |
| `docs` | Documentation only |
| `chore` | Maintenance, dependencies, tooling |

### Scope

- Module or component name: `feat(auth):`
- Feature area: `fix(checkout):`
- Omit if change is broad: `docs: update README`

### Examples

```text
feat(auth): add password reset flow
fix(checkout): handle empty cart edge case
refactor(api): extract validation middleware
test(user): add integration tests for signup
docs(readme): update installation instructions
chore(deps): upgrade react to v19
```

## Description Template

```markdown
## Summary

[2-3 sentences explaining what this PR does and why]

## Changes

- [Bullet list of specific changes]
- [One bullet per logical change]

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass (if applicable)
- [ ] Manual testing completed

## Related

- Plan: [link to plan file]
- Checkpoint: [link to checkpoint]
- Issue: #123 (if applicable)

## Screenshots

[If UI changes, include before/after screenshots]
```

## Linking to Workflow Artefacts

### Reference checkpoints

```markdown
**Checkpoint**: docs/state/phase_2.1_checkpoint.md
```

### Reference plans

```markdown
**Plan**: docs/plans/feature_auth_implementation.md
```

## Review Readiness

Before requesting review:

- [ ] All commits follow conventional format
- [ ] Description is complete
- [ ] Tests pass locally
- [ ] Self-review completed (see review-checklist.md)
- [ ] No debug code or console.logs
- [ ] Documentation updated if needed

## Draft PRs

Use draft PRs for:
- Work in progress that needs early feedback
- Blocking issues that need discussion
- Sharing context before phase completion

Convert to ready when:
- All acceptance criteria met
- Tests pass
- Self-review complete
