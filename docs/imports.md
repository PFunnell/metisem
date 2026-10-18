# Imports

What this repo took from other repos, and what was considered and dropped. Set up by `/setup-repo` on 2026-10-18.

## Taken

| Date | Source | Path | Taken | Changed |
|---|---|---|---|---|
| 2026-10-18 | `D:\dev\obsidian-linker`@e335d6f (same GitHub repo, older clone) | 2 unpushed commits (pytest suite, CI, `docs/EXAMPLES.md`) | pushed to origin from D:, pulled here | none |
| 2026-10-18 | `D:\dev\obsidian-linker`@e335d6f | `thoughts/` (gitignored) | copied whole, stays untracked | none |
| 2026-10-18 | `D:\dev\obsidian-linker`@e335d6f | `docs/research/*.md` (gitignored) | 2 notes copied, stay untracked | none |

Not copied: `D:\dev\obsidian-linker\docs\transcripts\` (marked interview-sensitive in `.gitignore`), `.env`, `.conda/`, `models/`.

## Considered and dropped

- `D:\dev\Obsidian`: the 2024 original of this repo (same remote, 3 commits plus loose experiments). Superseded by everything here.
- `claude-config` / `meta-claude`: used as the standard for the reconfiguration below, nothing copied. User-level config already supplies `/offload`, session-start resume, transcript archiving and git deny rules.

## Retired from the RPI Plus pack (2026-10-18)

Removed in line with claude-config and meta-claude decisions. Reinstate from git history (parent of the setup commit) if a trigger fires.

- `/create_plan`: replaced by plan mode + `plansDirectory: docs/plans`. Reinstate if 2 of the next 5 plans lack test steps or acceptance criteria (meta-claude reconfiguration plan, Step 11).
- `/implement_plan`, `/phase_complete`, `rules/phase-gates.md`: gate commands frozen (meta-claude recommendations c1 1.1, C2).
- `/resume_project`, RESUME.md: replaced by `/offload` checkpoints and the user-level session-start hook.
- `/gitsync`: staged broadly; user-level deny rules and explicit-path commits replace it.
- `rules/command-execution.md` (claimed bash-only; false), `diagnostics.md`, `env-handling.md` (covered by user-level `.env` denies), `hard-constraints.md` (UK English moved to CLAUDE.md).
- `statusline.sh`, `statusline.ps1` and the `statusLine` setting: decision D9 (VS Code GUI). `statusline.py` kept in git as the reinstatement route.
- `scripts/validate-artefacts.py`, `validate-pack.py`: opt-in, ran in 1 of 4 repos (recommendations c1 1.4, C7).
- `scripts/cc-transcript*`: replaced by the user-level transcript archive and `telemetry_query.py`.
- `.claude/extensions/` (ui-smoke, data-contracts, team-workflow), `.claude/README.md`, `settings.local.example.json`, `portable_config.local.example.yaml`: unused or describe the retired pack.

Kept: `/research_codebase`, now writes to `docs/research/` with no config file.
