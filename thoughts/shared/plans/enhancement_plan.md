# Obsidian-Linker Enhancement Plan

**Project:** obsidian-linker
**Date:** 2026-02-01
**Status:** APPROVED

## Problem Statement

Current: Three independent Python CLI tools (linker, tagger, summariser) that require terminal usage, have no unified interface, and cannot be distributed via Obsidian's community plugin ecosystem.

Goal: Transform obsidian-linker into a polished, distributable Obsidian community plugin with optional cloud LLM support, while preserving local-first operation.

## Current State

- Three standalone Python scripts with argparse CLIs
- Sentence Transformers embeddings (local, CUDA-capable)
- Ollama-only summarization
- No UI, no tests, manual verification
- Hash-based embedding cache in `.obsidian_linker_cache/`
- Single-tag assignment (no multi-tag support)
- Full vault reprocessing (no incremental updates)

## Desired End State

- Native Obsidian community plugin (TypeScript)
- Settings panel for all configuration
- In-app progress feedback for large vaults (2000+ notes)
- Choice of LLM providers (Ollama, OpenAI, Anthropic)
- Incremental updates (only process changed files)
- Multi-tag support with confidence thresholds
- Plugin store distribution ready

## Non-Goals

- Mobile support (embeddings too heavy)
- Real-time linking (on-type suggestions)
- Graph visualization (Obsidian already has this)
- Sync/collaboration features

---

## Phase 1: Foundation & Core Improvements (Python)

**Objective:** Modernize the Python codebase with shared infrastructure and better algorithms before porting.

### 1.1 Unified Core Module

- Extract shared code into `obsidian_linker/` package
  - `core/embeddings.py` - Unified embedding logic
  - `core/cache.py` - Single cache format (SQLite or unified .npz)
  - `core/markers.py` - Shared HTML comment marker handling
  - `core/files.py` - File discovery and hashing
- Standardize all tools to use the shared module

### 1.2 Incremental Processing

- Track file modification times alongside content hashes
- Only re-embed changed files
- Update similarity matrix incrementally (add/remove rows)
- Store file metadata in SQLite for fast lookups

### 1.3 Multi-Tag Support

- Allow configurable number of tags per note (1-N)
- Add confidence threshold (only assign tags above threshold)
- Option to preserve existing manual tags
- Tag sources:
  - Default generic tag list (bundled)
  - User-provided tag file (existing `tags.txt` format)
  - Auto-discovery: extract candidate tags from corpus via clustering/term extraction

### 1.4 Hardware-Aware Model Selection

- Detect hardware profile (CUDA availability, VRAM, CPU cores)
- Recommend embedding model based on profile:
  - CPU-only: `all-MiniLM-L6-v2` (fast, 384 dims)
  - GPU with limited VRAM: `all-mpnet-base-v2` (better quality, 768 dims)
  - GPU with ample VRAM: larger models as options
- Display tradeoff info (speed vs semantic quality)
- Allow manual override

### 1.5 Cloud LLM Integration

- Abstract summarizer behind provider interface
- Implement providers:
  - `OllamaProvider` (existing)
  - `OpenAIProvider` (GPT-4o)
  - `AnthropicProvider` (Claude)
- Config file for API keys and model selection
- Graceful fallback chain (try Ollama first, then cloud)

### 1.6 Test Suite

- Unit tests for core modules
- Integration tests with fixture vault
- Pytest configuration

**Verification:**
- All three CLI tools work via shared module
- Incremental update processes only changed files
- Cloud providers tested with real APIs
- Test suite passes

---

## Phase 2: Python Web UI

**Objective:** Validate UI/UX patterns with a Python-based web interface before TypeScript port.

### 2.1 FastAPI Backend

- REST API wrapping core functionality
  - `POST /api/links/generate`
  - `POST /api/tags/apply`
  - `POST /api/summaries/generate`
  - `GET /api/status` (job progress)
  - `GET /api/settings`
  - `PUT /api/settings`
- Background job queue for long operations
- WebSocket for real-time progress updates

### 2.2 Simple Frontend

- Minimal HTML/JS dashboard (no framework)
- Vault selection
- Operation triggers with progress bars
- Settings editor
- Results preview

### 2.3 Async Processing

- Background workers for embedding generation
- Chunked processing for large vaults
- Cancellation support

**Verification:**
- Web UI can trigger all operations
- Progress updates display in real-time
- Large vault (2000+ notes) processes without timeout
- Settings persist across sessions

---

## Phase 3: Obsidian Plugin (TypeScript)

**Objective:** Build native Obsidian plugin using transformers.js for embeddings.

### 3.1 Plugin Scaffold

- Obsidian plugin boilerplate
- Settings tab registration
- Commands registration
- Ribbon icons

### 3.2 Embedding Engine (transformers.js)

- Port embedding logic to TypeScript
- Use transformers.js with `all-MiniLM-L6-v2` ONNX model
- IndexedDB cache for embeddings
- Web Worker for non-blocking embedding

### 3.3 Link Generation

- Port similarity calculation
- Port two-phase link finding algorithm
- Markdown modification via Obsidian API

### 3.4 Tag Assignment

- Port tag embedding and matching
- YAML front matter modification via Obsidian API
- Preserve manual tags option

### 3.5 Summarization

- Provider abstraction (same as Python)
- Ollama provider (local HTTP)
- OpenAI provider
- Anthropic provider
- Settings for API keys

### 3.6 Large Vault Support

- Chunked processing with progress modal
- Incremental updates (only changed files)
- Background processing via Web Workers
- Notice API for progress feedback

**Verification:**
- Plugin installs in Obsidian
- All three operations work on test vault
- Settings persist
- Large vault handles gracefully
- No UI freezing during processing

---

## Phase 4: Polish & Distribution

**Objective:** Prepare for Obsidian community plugin submission.

### 4.1 UX Refinement

- Error handling with user-friendly messages
- Confirmation dialogs for destructive operations
- Undo support (backup before modification)
- Keyboard shortcuts

### 4.2 Documentation

- README with screenshots
- Configuration guide
- Troubleshooting FAQ

### 4.3 Community Plugin Requirements

- `manifest.json` with proper metadata
- `versions.json` for version compatibility
- No external network calls without user consent
- BRAT compatibility for beta testing
- License (MIT or similar)

### 4.4 Submission

- GitHub release workflow
- Submit PR to obsidian-releases repo
- Address review feedback

**Verification:**
- Passes Obsidian plugin guidelines checklist
- BRAT install works
- Community plugin submission accepted

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| transformers.js model quality differs from Python | Test embedding similarity parity early in Phase 3 |
| Large vault performance in browser | Web Workers, chunking, IndexedDB caching |
| Obsidian API limitations | Prototype markdown modification early |
| Cloud API costs | Default to local, require explicit opt-in |
| Plugin review rejection | Review guidelines thoroughly in Phase 4.3 |

---

## Dependencies

**Phase 1-2 (Python):**
- FastAPI, uvicorn (web server)
- SQLite (cache upgrade)
- openai, anthropic SDKs

**Phase 3-4 (TypeScript):**
- @xenova/transformers (transformers.js)
- Obsidian API types
- esbuild (bundling)

---

## Design Decisions

1. **Python CLI:** Maintain alongside plugin (power users, automation, CI pipelines)
2. **Tag definitions:** Three sources
   - Default generic tag list shipped with tool
   - User-provided custom tag file
   - Auto-discovery from corpus (cluster labels, frequent terms)
3. **Embedding model:** User choice with hardware-aware recommendations
   - Detect CUDA/CPU, available VRAM
   - Suggest appropriate model (smaller for CPU, larger for GPU)
   - Show tradeoffs (speed vs quality)

---

## Summary

Four-phase approach:
1. **Foundation** - Modernize Python with shared core, incremental updates, cloud LLMs
2. **Web UI** - Validate UX patterns with FastAPI dashboard
3. **Plugin** - Port to TypeScript using transformers.js
4. **Distribution** - Polish and submit to community plugins

Each phase builds on the previous, allowing validation before major rewrites.
