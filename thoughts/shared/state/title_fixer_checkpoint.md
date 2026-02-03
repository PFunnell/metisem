# Phase Checkpoint: Title Fixer

**Date:** 2026-02-03
**Status:** COMPLETE

## Summary

- Created standalone `title_fixer.py` CLI tool to rename files with generic titles
- Added `generate_title_from_summary()` function to `metisem/core/files.py`
- Supports preview mode (default) and apply mode (`--apply-fixes`)

## Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| Detect generic titles (New Chat, Untitled) | PASS |
| Extract titles from summary blocks | PASS |
| Sanitise titles for filename safety | PASS |
| Preview mode shows proposals | PASS |
| Apply mode renames files with conflict detection | PASS |
| Configurable max length and pattern | PASS |

## Files Modified/Created

| File | Changes |
|------|---------|
| `title_fixer.py` (new) | Standalone CLI for renaming files with generic titles |
| `metisem/core/files.py` | Added `generate_title_from_summary()` function |
| `CLAUDE.md` | Updated documentation with title fixer usage |

## Test Results

Test vault: 2,034 files
- Found: 25 files with generic titles
- Generated: 25 valid title proposals
- Examples:
  - "New chat.md" → "The conversation revolves around deploying an application.md"
  - "Untitled.md" → "The conversation revolves around solving a truncation error.md"

## Usage

```bash
# Preview mode (default)
python title_fixer.py /path/to/vault

# Apply renames
python title_fixer.py /path/to/vault --apply-fixes

# Custom pattern and length
python title_fixer.py /path/to/vault --title-pattern "^Draft.*" --max-length 80
```

## Implementation Details

**Title extraction heuristic:**
- Extracts first sentence from summary block
- Removes markdown formatting (bold, italic, code)
- Sanitises invalid filename characters: `<>:"/\|?*`
- Truncates to max length at word boundary
- Default max length: 60 characters

**Generic title pattern (default):**
```regex
^(New Chat|Untitled)( \(\d+\)| \d+)?$
```

**Conflict handling:**
- Checks if target filename already exists
- Skips rename if conflict detected
- Logs warning

**No wiki-link updates:**
- Links are auto-generated
- Workflow: rename → `--delete-links` → re-run linker

## Known Issues

None identified.

## Next Steps

- Consider adding LLM-based title generation (Ollama) as alternative to heuristic
- Could add batch operations (apply to all generic files in one command)

## Artefact Links

- Plan: `thoughts/shared/plans/enhancement_plan.md` (Phase 2)
- Prior checkpoint: `thoughts/shared/state/multi_source_linking_checkpoint.md`
