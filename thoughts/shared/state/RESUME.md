# RESUME

- Plan: N/A (iterative optimisation)
- Latest checkpoint: thoughts/shared/state/phase_1.10_checkpoint.md
- Research: docs/research/ (gitignored)
- Git: main @ 421c5f0 (local, needs push)
- Backlog: thoughts/shared/plans/backlog.md

- Configuration:
  - Test vault: D:\Obsidian\GPT\GPT2025-12-02
  - Tagging: 20 narrow-descriptor tags, 0.20 threshold, max 3 tags, summary-based
  - Linking: mpnet model, 0.75 similarity, max 5 links
  - Summarisation: mistral:latest, 6K token limit
  - Automated test suite: `python scripts/test_run_logging.py`
  - Transcript generation: `powershell .\scripts\cc-transcript-latest.ps1`

- Phase 1.8 Status: ✅ COMPLETE
  - Fixed linker bug (Path object mismatch) - 6,113 links written
  - Fixed tagger bug (duplicate tags) - clean deduplication
  - Enhanced tagger with multi-tag threshold support
  - Optimised tags (20 → 30, vocabulary-enriched descriptions)
  - Improved coverage 25% → 63% (1,289 files tagged)
  - Created research artefact documenting learnings
  - Database views for readable timestamps
  - Committed: 51e8203

- Phase 1.9 Status: ✅ COMPLETE
  - Pruned tags (30 → 20, removed low-usage tags <10 uses)
  - Refined descriptors to reduce semantic overlap (AI tags separated by role)
  - Reordered graph.json legend (rare tags first to avoid obscuring)
  - Fixed bash shell syntax errors in command-execution.md
  - Re-tagged vault with narrow descriptors at 0.20 threshold
  - Coverage: 63.5% (1,291 files, 2,464 tags applied)
  - Committed: 41c19b7, 537ac59, be77f37

- Phase 1.10 Status: ✅ COMPLETE
  - Identified problem: Vocabulary frequency ≠ topical centrality
  - Generated summaries for 2,033 files (mistral:latest, 3h 53m)
  - Added summary extraction to core files module
  - Added --tag-summaries flag to tagger
  - Re-tagged based on summaries: 85.8% coverage (1,745 files)
  - Key result: 60% reduction in ai_tooling_and_models false positives (985→387)
  - Improved tag balance: max 11.4% vs 40% previously
  - Documented Qwen2.5 7B for future model upgrade
  - Committed: ed51111, 87b5893

- Uncommitted changes:
  - thoughts/shared/state/RESUME.md - git status update

- Next actions:
  - Optional: Update graph.json legend ordering for new usage patterns
  - Optional: Generate transcript for Phases 1.8-1.10
  - Future: Consider Qwen2.5 7B upgrade for better summarisation quality
  - Future: Create validation set to measure precision/recall

- Blockers: None
