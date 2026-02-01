# Phase Gate Protocol

After each implementation phase:

## 1. Checkpoint

Write to `{state_dir}/phase_{X.Y}_checkpoint.md`:
- Date, Status (COMPLETE/IN_PROGRESS/BLOCKED)
- Summary (3 bullets max)
- Acceptance criteria table
- Files modified
- Known issues, Next phase
- Artefact links

## 2. Commit

Format: `feat(scope): phase {X.Y} - brief description`

## 3. Update RESUME.md

Update `{state_dir}/RESUME.md` with:
- Plan path, Latest checkpoint path
- Git branch @ short SHA
- Next actions, Blockers

Leave uncommitted (working file).

## 4. Transcript (Optional)

User generates via `scripts/cc-transcript.*`

**Do not proceed until steps 1-3 complete.**
