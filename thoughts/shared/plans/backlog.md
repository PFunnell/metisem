# Metisem Backlog

**Project:** obsidian-linker (Metisem)
**Last Updated:** 2026-02-03
**Status:** Active

This document tracks tool development work. For corpus-specific tuning (validation sets, threshold optimisation), see [Implementation Guidance](#implementation-guidance-user-domain).

---

## Priority 1: Core Tool Quality

### Documentation

**README improvements**
- Clear getting-started guide for new users
- Example workflows for common use cases
- Troubleshooting section for common issues
- Screenshots/examples of output
- **Rationale:** First-time user experience is critical for adoption

**Configuration guide**
- Document all CLI flags and their interactions
- Explain threshold selection trade-offs (precision vs recall)
- Tag descriptor authoring guidance
- Model selection recommendations
- **Blocks:** Users understanding how to tune for their vaults

### Code Quality

**Expanded test suite (Phase 1.6)**
- Unit tests for core modules (embeddings, cache, files, database)
- Integration tests with synthetic fixture vault
- Pytest configuration with coverage reporting
- **Depends on:** Synthetic test fixtures (not user corpus)
- **Current:** Manual test script only (`scripts/test_run_logging.py`)

**CI/CD pipeline**
- GitHub Actions workflow
- Run tests on push/PR
- Lint checking (ruff/flake8)
- **Depends on:** Expanded test suite

### Performance

**Incremental summary updates**
- Track file modification times in database
- Only re-summarise changed files
- Update summary cache incrementally
- **Rationale:** Critical for usability - 4 hours for full re-run is prohibitive
- **Expected:** 10x faster re-summarisation after initial run

---

## Priority 2: Generalizable Features

### Threshold Mechanisms

**Adaptive threshold calculation**
- Analyse score distribution per tag automatically
- Calculate threshold from percentiles (e.g., 75th percentile)
- Implement `--adaptive-threshold` flag in tagger
- **Rationale:** Removes need for manual threshold tuning
- **Depends on:** None (works on any corpus)

**Per-tag threshold support**
- Extend tags.txt format: `tag_name::threshold::description`
- Update tagger to use per-tag thresholds when specified
- Default to global threshold when not specified
- **Rationale:** Mechanism for users who want fine-grained control
- **Depends on:** None (format extension)

### Analysis Tooling

**Tag co-occurrence analysis script**
- Query database for frequently co-occurring tag pairs
- Output: redundant pairs, hierarchies, mutual exclusions
- Generate network graph visualisation
- **Rationale:** Helps users refine their tag vocabularies
- **Output:** `scripts/analyse_cooccurrence.py`

**Coverage gap analysis script**
- Sample untagged files
- Show score distributions for each tag
- Identify threshold sensitivity
- **Rationale:** Helps users understand why files remain untagged
- **Output:** `scripts/analyse_coverage.py`

### Infrastructure

**Hardware-aware model selection (Phase 1.4)**
- Detect CUDA availability, VRAM, CPU cores
- Recommend embedding model based on hardware profile
- Display trade-offs (speed vs semantic quality)
- Allow manual override
- **Depends on:** None
- **Status:** Currently hardcoded to all-MiniLM-L6-v2

**Cloud LLM integration for summarisation (Phase 1.5)**
- Abstract summariser behind provider interface
- Implement providers: Ollama (done), OpenAI, Anthropic
- Config file for API keys and model selection
- Cost estimation before running
- **Depends on:** None
- **Status:** Only Ollama implemented

---

## Priority 3: Major Features

### Web UI (Phase 2)

**FastAPI backend (Phase 2.1)**
- REST API wrapping core functionality
- Background job queue for long operations
- WebSocket for real-time progress
- **Depends on:** Core stability, expanded test suite

**Simple web frontend (Phase 2.2)**
- Minimal HTML/JS dashboard (no framework)
- Vault selection, operation triggers, progress display
- **Depends on:** FastAPI backend

**Async processing (Phase 2.3)**
- Background workers, chunked processing, cancellation
- **Depends on:** FastAPI backend

### Obsidian Plugin (Phase 3)

**Plugin scaffold (Phase 3.1)**
- Obsidian plugin boilerplate, settings, commands
- **Depends on:** Core algorithms stabilised

**Embedding engine with transformers.js (Phase 3.2)**
- Port embedding logic to TypeScript
- IndexedDB cache, Web Worker for non-blocking
- **Depends on:** Plugin scaffold

**Full feature port (Phases 3.3-3.6)**
- Link generation, tag assignment, summarisation
- Large vault support with chunked processing
- **Depends on:** Embedding engine

### Distribution (Phase 4)

**UX refinement (Phase 4.1)**
- Error handling, confirmation dialogs, undo support
- **Depends on:** Plugin complete

**Community plugin submission (Phase 4.3)**
- Follow Obsidian guidelines, security review, submit
- **Depends on:** UX refinement, documentation

---

## Priority 4: Research / Exploratory

These are speculative features - may not be implemented.

**Graph-based link recommendation**
- Consider graph structure, not just pairwise similarity
- Recommend bridges, close triangles
- **Research question:** Does graph-aware linking improve vault navigation?

**Semantic search interface**
- Natural language query → find similar notes
- Use existing embeddings
- **Research question:** Is this valuable vs Obsidian's built-in search?

**Tag hierarchies**
- Parent/child relationships with inheritance
- **Research question:** Do users want managed hierarchies or flat tags?

**Active learning for tagging**
- Present uncertain cases to user for labelling
- Use labels to refine model/descriptors
- **Research question:** Is the interaction overhead worthwhile?

---

## Implementation Guidance (User Domain)

> **Note:** These are not tool development tasks. They are guidance for users tuning Metisem for their specific vaults. The tool provides mechanisms; users apply them to their corpora.

### Validation Set Creation

If you want to measure precision/recall for your vault:
1. Sample 100-200 representative files
2. Manually assign ground truth tags
3. Store in CSV format: `file_path,tag1,tag2,...`
4. Run tagger, compare output to ground truth
5. Calculate precision/recall/F1

**This is corpus-specific work** - your tags, your topics, your judgement of correctness.

### Threshold Tuning

1. Run tagger at various thresholds (0.15, 0.20, 0.25, 0.30)
2. Sample tagged files, assess quality
3. Use coverage gap analysis script to understand trade-offs
4. Choose threshold balancing precision vs recall for your needs

### Tag Vocabulary Refinement

1. Run co-occurrence analysis
2. Merge redundant tags (always co-occur)
3. Split ambiguous tags (cover too much semantic space)
4. Add missing categories (based on untagged file inspection)

### Graph Configuration

- Order tags in graph.json by rarity (rare first due to draw order)
- Choose distinct colours for high-frequency tags
- Re-order when tag distribution changes significantly

---

## Completed (For Reference)

### Phase 1.1: Unified Core Module ✅
- Created `metisem/core/` package
- Modules: embeddings.py, cache.py, markers.py, files.py, database.py

### Phase 1.2: Incremental Processing ✅
- File metadata tracked in SQLite
- Change detection: new, modified, deleted, unchanged

### Phase 1.3: Multi-Tag Support ✅
- `--max-tags`, `--tag-threshold` parameters
- Threshold-filtered selection

### Phase 1.7: Run Logging ✅
- Database renamed, run_logs table, query utilities

### Phase 1.8: Bug Fixes & Optimisation ✅
- Fixed linker Path object mismatch
- Fixed tagger duplicate tags bug
- Coverage improved 25%→63%

### Phase 1.9: Tag Consolidation ✅
- Pruned tags 30→20
- Refined AI tag descriptors

### Phase 1.10: Summary-Based Tagging ✅
- Summary extraction, --tag-summaries flag
- 85.8% coverage, balanced distribution

### Graph.json Update ✅ (2026-02-03)
- Reordered by summary-based distribution (rare first)
- Removed superfluous 'tag:#' prefix from queries

---

## Decision Log

### Why summary-based tagging?
- Full-text embeddings match vocabulary frequency, not topical centrality
- Summaries distill core topics, filtering incidental mentions
- Evidence: ai_tooling_and_models dropped from 40% to 8.4%

### Why 20 tags instead of 30?
- 30 tags exceeded useful colour differentiation in graph
- Removed 8 tags with <10 uses (2.5% of applications)

### Why validation/labelling is not Priority 1?
- Metisem is a generic tool for any markdown vault
- Validation sets are corpus-specific (your topics, your tags)
- Human labelling is implementation work, not tool development
- Tool provides mechanisms; users tune for their corpora

---

## Dependency Graph

```
Documentation ──────────────────────────────────────────┐
     │                                                   │
     v                                                   v
Test Suite ──────> CI/CD                            Users can
     │                                              tune their
     v                                              vaults
Core Stability ─────────────────────┐
     │                              │
     ├──> Adaptive Thresholds       │
     ├──> Per-tag Thresholds        │
     ├──> Analysis Scripts          │
     │                              │
     v                              v
Hardware Selection           Cloud LLM Integration
     │                              │
     └──────────┬───────────────────┘
                │
                v
         Web UI (Phase 2)
                │
                v
      Obsidian Plugin (Phase 3)
                │
                v
       Distribution (Phase 4)
```

---

## Notes

- Priority 1 items improve tool quality for all users
- Priority 2 items add generalizable capabilities
- Priority 3-4 require significant development effort
- Implementation guidance is documentation, not backlog items

---

## Last Review

**Date:** 2026-02-03
**Reviewer:** Claude Opus 4.5
**Changes:** Restructured to separate tool dev from user implementation; added dependency graph; demoted corpus-specific validation work to guidance section

### From Enhancement Plan - Phase 2: Python Web UI

**FastAPI backend (Phase 2.1)**
- REST API wrapping core functionality
- Endpoints:
  - `POST /api/links/generate`
  - `POST /api/tags/apply`
  - `POST /api/summaries/generate`
  - `GET /api/status` (job progress)
  - `GET /api/settings`, `PUT /api/settings`
- Background job queue for long operations
- WebSocket for real-time progress updates

**Simple web frontend (Phase 2.2)**
- Minimal HTML/JS dashboard (no framework)
- Vault selection
- Operation triggers with progress bars
- Settings editor
- Results preview

**Async processing (Phase 2.3)**
- Background workers for embedding generation
- Chunked processing for large vaults
- Cancellation support

**Verification criteria:**
- Web UI can trigger all operations
- Progress updates display in real-time
- Large vault (2000+ notes) processes without timeout
- Settings persist across sessions

### From Enhancement Plan - Phase 3: Obsidian Plugin

**Plugin scaffold (Phase 3.1)**
- Obsidian plugin boilerplate
- Settings tab registration
- Commands registration
- Ribbon icons

**Embedding engine with transformers.js (Phase 3.2)**
- Port embedding logic to TypeScript
- Use transformers.js with `all-MiniLM-L6-v2` ONNX model
- IndexedDB cache for embeddings
- Web Worker for non-blocking embedding

**Link generation (Phase 3.3)**
- Port similarity calculation to TypeScript
- Port two-phase link finding algorithm
- Markdown modification via Obsidian API

**Tag assignment (Phase 3.4)**
- Port tag embedding and matching to TypeScript
- YAML front matter modification via Obsidian API
- Preserve manual tags option

**Summarization (Phase 3.5)**
- Provider abstraction (same as Python)
- Ollama provider (local HTTP)
- OpenAI provider
- Anthropic provider
- Settings for API keys

**Large vault support (Phase 3.6)**
- Chunked processing with progress modal
- Incremental updates (only changed files)
- Background processing via Web Workers
- Notice API for progress feedback

**Verification criteria:**
- Plugin installs in Obsidian
- All three operations work on test vault
- Settings persist
- Large vault handles gracefully
- No UI freezing during processing

### From Enhancement Plan - Phase 4: Distribution

**UX refinement (Phase 4.1)**
- Error handling with user-friendly messages
- Confirmation dialogs for destructive operations
- Undo support (backup before modification)
- Keyboard shortcuts

**Documentation (Phase 4.2)**
- README with screenshots
- Configuration guide
- Troubleshooting FAQ

**Community plugin requirements (Phase 4.3)**
- Follow Obsidian plugin guidelines
- Security review
- License compliance
- Submit to plugin store

---

## Priority 4: Research / Exploratory

### Advanced Features

**Multi-vault support**
- Manage multiple vaults with separate configs
- Switch between vaults in UI
- Shared vs vault-specific tag definitions

**Semantic search interface**
- Natural language query → find similar notes
- Use existing embeddings
- Rank by similarity
- Display as Obsidian search results

**Link quality scoring**
- Not all links equally valuable
- Score based on:
  - Bidirectional vs unidirectional
  - Shared tags
  - Temporal proximity (created at similar times)
  - User interaction (clicked links weighted higher)
- Display confidence scores in link blocks

**Tag hierarchies**
- Parent/child relationships (e.g., `AI_and_automation` parent of `ai_tooling_and_models`)
- Inheritance rules (child implies parent)
- Hierarchical browsing in UI

**Temporal analysis**
- Track tag evolution over time
- Show trending topics
- Identify dormant/stale content
- Time-series visualization of vault growth

### Alternative Approaches

**Graph-based link recommendation**
- Current: Pairwise similarity only
- Enhanced: Consider graph structure
- Recommend links that create useful bridges
- Close triangles (if A→B and B→C, suggest A→C)
- PageRank-like importance scoring

**Active learning for tagging**
- Present uncertain cases to user for labeling
- Files near threshold boundary
- Use labels to refine model/descriptors
- Iterative improvement loop

**Cross-vault knowledge transfer**
- Train embeddings on multiple vaults
- Transfer tag definitions between vaults
- Identify common patterns across user base
- Privacy-preserving (federated learning)

---

## Completed (For Reference)

### Phase 1.1: Unified Core Module ✅
- Created `metisem/core/` package
- Modules: embeddings.py, cache.py, markers.py, files.py, database.py
- All tools use shared module

### Phase 1.2: Incremental Processing ✅
- File metadata tracked in SQLite (mtime, hash, size)
- Change detection: new, modified, deleted, unchanged
- Only re-embed changed files
- Database: `.metisem/metisem.db`

### Phase 1.3: Multi-Tag Support ✅
- `--max-tags` parameter (default 3)
- `--tag-threshold` parameter (default 0.4, now 0.2)
- Threshold-filtered selection (not argmax)
- Tag distribution logging

### Phase 1.7: Run Logging ✅
- Directory renamed `.metisem_cache/` → `.metisem/`
- Database renamed `cache.db` → `metisem.db`
- `run_logs` table tracks all operations
- `RunLogger` class integrated into all tools
- Query utilities: `scripts/query_runs.py`, `scripts/cleanup_logs.py`
- CSV export for analysis

### Phase 1.8: Bug Fixes & Optimization ✅
- Fixed linker Path object mismatch (6,113 links written)
- Fixed tagger duplicate tags bug
- Multi-tag threshold support added
- Tag vocabulary enrichment (20→30 tags)
- Database views for readable timestamps
- Coverage improved 25%→63%

### Phase 1.9: Tag Consolidation ✅
- Pruned tags 30→20 (removed <10 usage tags)
- Refined AI tag descriptors for distinctiveness
- Reordered graph.json legend (rare first)
- Bash syntax rules documented

### Phase 1.10: Summary-Based Tagging ✅
- Summary extraction from markdown blocks
- `--tag-summaries` flag in tagger
- 2,033 summaries generated (mistral, 3h 53m)
- Re-tagged based on summaries
- Results:
  - 85.8% coverage (vs 63.5% full-text)
  - 60% reduction in ai_tooling_and_models false positives
  - Balanced distribution (max 11.4% vs 40%)
- Qwen2.5 7B documented for future upgrade

---

## Decision Log

### Why summary-based tagging?
- **Problem:** Full-text embeddings match vocabulary frequency, not topical centrality
- **Solution:** Summaries distill core topics, filtering incidental mentions
- **Evidence:** ai_tooling_and_models dropped from 40% to 8.4% of tags
- **Trade-off:** Requires summary generation step (3-4 hours for 2K files)

### Why 20 tags instead of 30?
- **Problem:** 30 tags exceeded useful color differentiation in graph
- **Solution:** Removed 8 tags with <10 uses (2.5% of applications)
- **Trade-off:** Lost some granularity, gained visual clarity

### Why Mistral over Qwen2.5 for summaries?
- **Decision:** Use Mistral initially, upgrade to Qwen2.5 if quality issues
- **Rationale:** Mistral already installed, proven for articles, faster
- **Qwen2.5 advantages:** Better technical content, 128K context, but 20-30% slower
- **Review trigger:** If summaries too generic or miss technical nuance

### Why 0.20 threshold for summary-based tagging?
- **Finding:** Narrow descriptors required lower threshold
- **Result:** 85.8% coverage at 0.20 (exceeded >80% target)
- **Previous:** 0.30 threshold with broad descriptors (66% coverage)
- **Trade-off:** Lower threshold may increase false positives (validation needed)

---

## Notes

- Backlog items not prioritized within priority tiers
- Priority 1 items block optimization decisions
- Phases 2-4 require significant development effort (weeks-months)
- Research items exploratory, may not be implemented
- Completed items retained for context/documentation

---

## Last Review

**Date:** 2026-02-03
**Reviewer:** Claude Sonnet 4.5 (automated)
**Next Review:** After Phase 1.10 validation complete
