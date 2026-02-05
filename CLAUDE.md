# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Metisem: Python toolchain for enhancing markdown vaults using semantic analysis and local LLMs.
Compatible with Obsidian, Logseq, and other markdown-based knowledge bases.

- **Semantic linking** between related notes (Sentence Transformers)
- **Auto-tagging** based on custom tag definitions
- **Summarisation** via Ollama-served local LLMs
- **Title fixing** for files with generic names using summaries

## Commands

### Semantic Link Generator
```bash
# Preview links (no modification)
python main.py /path/to/vault

# Apply links to notes
python main.py /path/to/vault --apply-links

# Delete all auto-generated link blocks
python main.py /path/to/vault --delete-links

# Rebuild embeddings from scratch
python main.py /path/to/vault --apply-links --force-embeddings

# Multi-source linking: weight title, content, and summary similarity
python main.py /path/to/vault --title-weight 0.2 --content-weight 0.5 --summary-weight 0.3
```

Key flags: `--similarity` (threshold, default 0.6), `--min-links`, `--max-links` (default 9), `--model` (Sentence Transformer), `--clusters` (KMeans clustering)

Multi-source linking: `--title-weight`, `--content-weight` (default 1.0), `--summary-weight`. Weights are normalised, so `2:1:1` and `0.5:0.25:0.25` produce equivalent results.

### Auto Tagger
```bash
# Apply tags based on semantic similarity
python tagger.py /path/to/vault --tags-file tags.txt --apply-tags

# Remove all tags from notes
python tagger.py /path/to/vault --remove-tags

# Force rebuild tag embeddings
python tagger.py /path/to/vault --tags-file tags.txt --apply-tags --force-embeddings
```

### Summariser (Ollama)
```bash
# Ensure Ollama is running first: ollama serve

# Generate summaries (incremental by default)
python summariser_ollama.py /path/to/vault --apply-summaries

# Remove existing summaries
python summariser_ollama.py /path/to/vault --delete-summaries

# Force regenerate all summaries (ignore cache)
python summariser_ollama.py /path/to/vault --apply-summaries --force-summaries

# Use specific model
python summariser_ollama.py /path/to/vault --apply-summaries --model mistral
```

### Title Fixer
```bash
# Preview proposed renames (requires summaries)
python title_fixer.py /path/to/vault

# Apply renames to files
python title_fixer.py /path/to/vault --apply-fixes

# Custom pattern and title length
python title_fixer.py /path/to/vault --title-pattern "^Draft.*" --max-length 80
```

Renames files with generic titles (e.g., "New Chat", "Untitled") using descriptive titles extracted from summary blocks. After renaming, run `--delete-links` and re-link to update connections.

## Architecture

### Four Independent Tools
Each tool is a standalone CLI script with its own argparse interface:

1. **main.py** - Semantic linker using cosine similarity on Sentence Transformer embeddings. Supports multi-source linking (title, content, summary) with configurable weights. Inserts `## Related Notes` sections wrapped in HTML comment markers.

2. **tagger.py** - Matches note content to tag descriptions via embedding similarity. Modifies YAML front matter.

3. **summariser_ollama.py** - Calls local Ollama API (`localhost:11434`) to generate summaries. Prepends summary blocks to files.

4. **title_fixer.py** - Renames files with generic titles using descriptive names extracted from summary blocks. Includes conflict detection and preview mode.

### Shared Patterns
- All tools use `Path.rglob('*.md')` or `glob.glob` for file discovery
- Embedding cache stored in `.metisem/` using numpy `.npy`/`.npz` files and SQLite database
- Content modification uses HTML comment markers for section boundaries:
  - Links: `<!-- AUTO-GENERATED LINKS START -->` / `END`
  - Summaries: `<!-- AUTO-GENERATED SUMMARY START -->` / `END`
- Hash-based cache invalidation (SHA256 of file content)

### Tag File Format
`tags.txt` uses `tag_name::description` format per line. The description is embedded for semantic matching.

## Dependencies

Core: `sentence-transformers`, `scikit-learn`, `numpy`, `torch`, `pyyaml`, `tqdm`
Summarizer: `requests` (for Ollama API)

## Environment

Uses conda environment in `.conda/`. CUDA support enabled when available (falls back to CPU).

## Development Workflow

This project uses the Claude Code RPI Plus workflow:

1. **Research**: `/research_codebase` before changes
2. **Plan**: `/create_plan` for non-trivial work (requires approval)
3. **Implement**: `/implement_plan` with phase gates
4. **Verify**: `/phase_complete` before commit
5. **Commit**: `/gitsync` to push

## Testing

Automated test suite covers core functionality:

```bash
# Run all tests
python scripts/test_run_logging.py

# Tests cover:
# - Linker functionality and logging
# - Tagger functionality and logging
# - Query utility and parameter analysis
# - CSV export
# - Cleanup utility
```

Test vault path configured in `.env` (TEST_VAULT_PATH) or `.claude/portable_config.local.yaml` (testing.vault_path).

## Constraints

- Tools modify files in-place - always test on a backup vault first
- Ollama must be running locally for summariser functionality

## Configuration

- `.claude/portable_config.local.yaml` - Project settings (paths, validation)
- `.claude/rules/` - Behavioral constraints (auto-loaded)
- `docs/state/RESUME.md` - Session continuity
