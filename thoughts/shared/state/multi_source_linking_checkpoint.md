# Phase Checkpoint: Multi-Source Linking

**Date:** 2026-02-03
**Status:** COMPLETE

## Summary

- Added `--title-weight`, `--content-weight`, `--summary-weight` CLI parameters to `main.py`
- Modified `calculate_similarity()` to compute weighted combination of title, content, and summary similarity matrices
- Updated main() flow to generate embeddings for each enabled source and pass to similarity calculation

## Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| Default behaviour unchanged (content-weight=1.0) | PASS |
| Summary-based linking works | PASS |
| Title matching boosts similar filenames | PASS |
| Balanced weights produce combined results | PASS |
| Weights logged in run_logger | PASS |

## Files Modified

| File | Changes |
|------|---------|
| `main.py` | Added weight params, modified `calculate_similarity()`, updated main() flow |

## Test Results

| Configuration | Threshold | Pairs Above | Link Distribution |
|---------------|-----------|-------------|-------------------|
| Content-only (baseline) | 0.6 | 3.55% | 455×1, 76×2, 1503×3 |
| Title 0.2 + Content 0.8 | 0.6 | 0.63% | 852×1, 143×2, 1039×3 |
| Summary-only | 0.5 | 1.07% | 593×1, 127×2, 1314×3 |
| Balanced (0.2/0.4/0.4) | 0.5 | 0.43% | 898×1, 188×2, 948×3 |

## Known Issues

None identified.

## Next Steps

1. Title Fixer feature (Phase 2 of plan - deferred)
2. Consider adding weighted similarity metrics to run logs

## Artefact Links

- Plan: `thoughts/shared/plans/enhancement_plan.md`
