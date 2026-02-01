# Hard Constraints

## Artefact Locations

Read paths from `.claude/portable_config.local.yaml`. Defaults:
- Plans: `docs/plans/`
- Research: `docs/research/`
- State: `docs/state/`
- Verification: `docs/verification/`

Move misplaced artefacts to canonical locations immediately.

**Naming convention** (enforced by validator):
- Plans: `*_plan.md`, `*_implementation.md`
- State: `*_checkpoint.md`, `*_state.md`
- Research: `*_research.md`, `*_analysis.md`, `*.brief.md`
- Verification: `verify_*.md`

## Behavioural Rules

- **Concision**: Bullets over prose. Don't restate the obvious.
- **Uncertainty**: STOP and ask questions rather than guessing.
- **Spec-Driven**: Follow specifications; propose changes explicitly if needed.
- **Markdown**: Always specify language in code blocks. No hard-wrapping.
- **No time estimates**: Focus on what, not how long.
- **Performance claims need data**: No arbitrary SLAs without measurements.
