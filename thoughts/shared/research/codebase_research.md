# Obsidian-Linker Codebase Research

**Date:** 2026-02-01
**Project:** obsidian-linker

## Overview

Python toolchain for enhancing Obsidian markdown vaults using semantic analysis and local LLMs. Three independent CLI tools operate on the same vault structure.

## File Structure

| File | Purpose |
|------|---------|
| `main.py` | Semantic link generator (cosine similarity) |
| `tagger.py` | Auto-tagger (YAML front matter) |
| `summariser_ollama.py` | Ollama-based summarizer |
| `main.bak.py` | Backup of earlier linker version |
| `tags.txt` | Tag definitions for tagger |
| `scripts/validate-artefacts.py` | Project artifact validator |

## Tool Details

### 1. main.py - Semantic Linker

**Purpose:** Generate backlinks between related notes using embedding similarity.

**Key Functions:**
- `find_markdown_files()` - Glob `**/*.md`
- `read_file_text_and_hash()` - UTF-8 read + SHA256
- `load/save_embeddings_from_cache()` - `.npy` structured array
- `generate_embeddings()` - Sentence Transformers with batch encode
- `calculate_similarity()` - L2-normalized cosine similarity matrix
- `find_links()` - Two-phase: threshold + fallback to min-links
- `modify_markdown_file()` - Insert/remove `## Related Notes` block

**Markers:**
```
<!-- AUTO-GENERATED LINKS START -->
## Related Notes
[[file1]]
[[file2]]
<!-- AUTO-GENERATED LINKS END -->
```

**CLI:**
```bash
python main.py /vault --apply-links --similarity 0.6 --max-links 9
python main.py /vault --delete-links
python main.py /vault --apply-links --force-embeddings
```

### 2. tagger.py - Auto-Tagger

**Purpose:** Assign single best-matching tag per note based on semantic similarity to tag descriptions.

**Key Functions:**
- `find_markdown_files()` - `Path.rglob('*.md')`
- `load_tags()` - Parses `tag_name::description` format
- `embed_documents()` - Cached embeddings (`.npz` format)
- `add_tag()` - Modifies YAML front matter `tags:` key
- `remove_tags()` - Strips all tags from notes

**Tag File Format (`tags.txt`):**
```
local_government::Topics related to city councils...
AI_and_automation::Discussions about AI, ML...
```

**CLI:**
```bash
python tagger.py /vault --tags-file tags.txt --apply-tags
python tagger.py /vault --remove-tags
```

### 3. summariser_ollama.py - Summarizer

**Purpose:** Generate summaries via local Ollama API, prepend to files.

**Key Functions:**
- `find_markdown_files()` - Glob `**/*.md`
- `summarize_text()` - HTTP POST to `localhost:11434/api/generate`
- `insert_summary()` - Prepend summary block
- `remove_summaries()` - Regex removal

**Markers:**
```
<!-- AUTO-GENERATED SUMMARY START -->
Summary text here
<!-- AUTO-GENERATED SUMMARY END -->
```

**Ollama API Options:**
- Temperature: 0.3
- Context window: 8192
- Input limit: ~6K words
- Model: mistral (default)

**CLI:**
```bash
ollama serve  # Must be running first
python summariser_ollama.py /vault --apply-summaries --model mistral
python summariser_ollama.py /vault --delete-summaries
```

## Shared Patterns

### Caching
- Location: `.obsidian_linker_cache/` at vault root
- Filename: `embeddings_{vault_name}_{model_name}.npy` or `.npz`
- Invalidation: SHA256 hash of file content
- Reuse: unchanged files skip re-embedding

### File Discovery
- `glob.glob(**/*.md, recursive=True)` (main.py, summariser)
- `Path.rglob('*.md')` (tagger.py)

### Content Markers
- HTML comments with regex matching
- Multiline patterns with `re.DOTALL`
- Whitespace-tolerant: `^[ \t]*marker[ \t]*$`

### Device Detection
- Auto-detects CUDA, falls back to CPU
- `device = 'cuda' if torch.cuda.is_available() else 'cpu'`

### Embedding Model
- Default: `all-MiniLM-L6-v2` (384 dimensions)
- Configurable via `--model` flag

## Dependencies

**Required:**
- `sentence-transformers` - Semantic embeddings
- `scikit-learn` - Cosine similarity, KMeans
- `numpy` - Array operations
- `torch` - Backend for transformers
- `pyyaml` - YAML parsing (tagger)
- `tqdm` - Progress bars
- `requests` - Ollama API (summariser only)

**Environment:** Conda at `.conda/`

## Architecture Diagram

```
┌─────────────────────────────────────┐
│     Obsidian Vault (*.md files)     │
└──────────────────┬──────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌────────┐    ┌────────┐    ┌──────────┐
│main.py │    │tagger  │    │summariser│
│ Links  │    │ Tags   │    │ Ollama   │
└───┬────┘    └───┬────┘    └────┬─────┘
    │             │              │
    └──────┬──────┴──────────────┘
           │
    ┌──────▼──────┐
    │ Sentence    │
    │ Transformers│
    └──────┬──────┘
           │
    ┌──────▼──────────────────┐
    │ .obsidian_linker_cache/ │
    │ (embeddings .npy/.npz)  │
    └─────────────────────────┘
```

## Key Implementation Notes

- **Link Generation:** Two-phase algorithm (threshold-based + fallback)
- **Tag Assignment:** One-best (argmax), no threshold
- **Summary Generation:** Ollama streaming disabled, temperature 0.3
- **No Test Suite:** Manual verification against test vault required
- **Cluster Linking:** Optional KMeans for intra-cluster links only

## Configuration

**Project config:** `.claude/portable_config.local.yaml`
```yaml
project:
  name: "obsidian-linker"
paths:
  python: ".conda/python.exe"
```

**Tag definitions:** `tags.txt`
- Format: `tag_name::description`
- One per line, `#` comments, empty lines ignored
