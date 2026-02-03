# Metisem Backlog

**Project:** obsidian-linker (Metisem)
**Last Updated:** 2026-02-03
**Status:** Active

This document tracks all outstanding tasks, enhancements, and future work across the project.

---

## Priority 1: Immediate / High Value

### Validation & Quality Assurance

**Create labeled validation set**
- Sample 100-200 files manually
- Apply ground truth tags based on core topics
- Store in `docs/validation/` with CSV format
- Enable precision/recall measurement
- **Rationale:** Currently optimizing blind without accuracy metrics
- **Related:** Phases 1.8-1.10 critique

**Compute precision/recall metrics**
- Compare configurations:
  - Full-text tagging @ 0.20 threshold
  - Summary-based tagging @ 0.20 threshold
  - Broad descriptors (Phase 1.8) vs narrow descriptors (Phase 1.9)
- Calculate F1 scores
- Identify optimal threshold per configuration
- Document in `docs/research/validation_results.md`
- **Blocks:** Future tag optimization decisions

**False positive audit**
- Sample 50 files tagged with each of top 5 tags
- Manually verify tag appropriateness
- Identify systematic misclassifications
- Update tag descriptors or thresholds based on findings

### Graph Visualization

**Update graph.json for Phase 1.10 usage patterns**
- Current ordering is Phase 1.9 (full-text usage)
- Re-order legend based on summary-based tagging counts:
  1. developer_tooling (3) → 20. ai_tooling_and_models (387)
- Test visual hierarchy in Obsidian
- Verify rare tags not obscured
- **Files:** `D:\Obsidian\GPT\GPT2025-12-02\.obsidian\graph.json`

### Documentation

**Generate transcript for Phases 1.8-1.10**
- Run: `powershell .\scripts\cc-transcript-latest.ps1`
- Archive in `docs/transcripts/2026-02-03/`
- Link from checkpoint files
- **Purpose:** Session archival and knowledge transfer

---

## Priority 2: Enhancement / Medium Value

### Model Improvements

**Upgrade to Qwen2.5 7B for summarization**
- Install: `ollama pull qwen2.5:7b` (~4.7GB)
- Update summariser default model
- Benchmark against mistral on sample files
- Compare summary quality for technical content
- Document results in `docs/research/qwen_vs_mistral_comparison.md`
- **Trade-off:** 20-30% slower, better quality, 128K context vs 32K
- **When:** If Mistral summaries show quality issues

**Adaptive threshold calculation**
- Analyze score distribution per tag
- Calculate optimal threshold from percentiles (e.g., 75th)
- Implement `--adaptive-threshold` flag in tagger
- Compare fixed vs adaptive on validation set
- **Expected:** Better balance between precision and recall

**Per-tag thresholds**
- Some tags more specific (automotive, neurodivergence)
- Some tags more general (productivity, ethics_and_policy)
- Calculate optimal threshold per tag from validation data
- Store in tags.txt: `tag_name::threshold::description`
- Update tagger to use per-tag thresholds
- **Expected:** Reduce false positives on broad tags, improve recall on narrow tags

### Tag System Improvements

**Tag co-occurrence analysis**
- Query database for frequently co-occurring tag pairs
- Identify:
  - Redundant tags (always occur together → merge)
  - Semantic hierarchies (parent/child relationships)
  - Mutually exclusive tags (never occur together → descriptor issue)
- Visualize with network graph
- Document in `docs/research/tag_cooccurrence.md`

**Coverage gap analysis**
- Sample 100 untagged files (743 files with 0 tags remain)
- Manually identify core topics
- Determine if missing tag categories needed
- Or if threshold too strict / descriptors too narrow
- Update tags.txt or thresholds based on findings

**Tag clustering for auto-discovery**
- Extract candidate tags from corpus via:
  - TF-IDF on untagged files
  - Topic modeling (LDA)
  - Named entity recognition
- Cluster similar candidate tags
- Generate descriptors automatically
- Human review before adding to tags.txt
- **Goal:** Discover emergent topics not in initial 20 tags

### Performance & Infrastructure

**Embedding fine-tuning**
- Create domain-specific training set from vault
- Fine-tune sentence-transformers model on corpus
- Compare domain-adapted vs generic model
- Store in `models/` (gitignored)
- Document in `docs/research/fine_tuning.md`
- **Trade-off:** Better accuracy, slower cold start, corpus-specific

**Incremental summary updates**
- Track file modification times in database
- Only re-summarize changed files
- Update summary cache incrementally
- **Expected:** 10x faster re-summarization after initial run

**Batch processing for cloud LLMs**
- Group files into batches for API efficiency
- Implement rate limiting for OpenAI/Anthropic APIs
- Cost estimation before running
- **Related:** Phase 1.5 cloud LLM integration (not yet implemented)

---

## Priority 3: Major Features / Low Urgency

### From Enhancement Plan - Phase 1 Remaining

**Hardware-aware model selection (Phase 1.4)**
- Detect CUDA availability, VRAM, CPU cores
- Recommend embedding model based on profile:
  - CPU-only: `all-MiniLM-L6-v2` (384 dims)
  - GPU limited VRAM: `all-mpnet-base-v2` (768 dims)
  - GPU ample VRAM: larger models
- Display trade-offs (speed vs semantic quality)
- Allow manual override
- **Status:** Currently using all-MiniLM-L6-v2 by default

**Cloud LLM integration for summarization (Phase 1.5)**
- Abstract summarizer behind provider interface
- Implement providers:
  - `OllamaProvider` (existing, complete)
  - `OpenAIProvider` (GPT-4o)
  - `AnthropicProvider` (Claude Sonnet/Opus)
- Config file for API keys and model selection
- Graceful fallback chain (Ollama → cloud)
- Cost estimation UI
- **Status:** Only Ollama implemented

**Expanded test suite (Phase 1.6)**
- Unit tests for core modules
- Integration tests with fixture vault
- Pytest configuration
- CI/CD pipeline (GitHub Actions)
- **Current:** Only manual test script exists (`scripts/test_run_logging.py`)

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
