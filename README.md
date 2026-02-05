# Metisem - Markdown Semantic Analysis Toolkit

**Automatically discover semantic connections, auto-tag, and summarise your markdown knowledge base**

Transform your markdown notes into an interconnected web of ideas. Metisem analyses note content using state-of-the-art NLP to generate intelligent backlinks, auto-tag notes, and create AI-powered summaries, helping you surface hidden connections and navigate large vaults with ease.

Compatible with Obsidian, Logseq, and other markdown-based knowledge management tools.

Built for researchers, PKM enthusiasts, and anyone managing extensive markdown collections.

---

## Overview

Four specialized tools for enhancing your markdown vault:

- **Semantic Linker** (`main.py`) - Generates contextual backlinks between related notes based on content similarity
- **Auto-Tagger** (`tagger.py`) - Intelligently tags notes by matching content against custom tag descriptions
- **Summariser** (`summariser_ollama.py`) - Creates concise summaries using local LLMs via Ollama
- **Title Fixer** (`title_fixer.py`) - Renames files with generic titles using descriptive names extracted from summaries

All tools leverage [Sentence Transformers](https://www.sbert.net/) for semantic understanding, with intelligent caching that automatically detects content changes via SHA256 hashing.

![Semantic links in Obsidian](docs/images/metisem1.png)

---

## Features

### Semantic Link Generator
- **Content-aware linking** - Uses cosine similarity on embeddings to identify semantically related notes
- **Multi-source linking** - Combines title, content, and summary similarity with configurable weights
- **Customizable thresholds** - Control link quantity and quality with configurable similarity scores
- **Non-invasive** - Links are inserted in clearly marked sections that can be updated or removed anytime
- **Incremental caching** - Only re-processes files whose content has changed
- **GPU acceleration** - Automatically uses CUDA when available for faster embedding generation

### Auto-Tagger
- **Semantic tag matching** -Tags notes based on conceptual similarity to tag descriptions, not just keywords
- **Custom taxonomies** -Define your own tag vocabulary with human-readable descriptions
- **YAML front matter integration** -Seamlessly works with Obsidian's native tag system
- **Batch operations** -Tag entire vaults in one pass

### Summariser (Ollama)
- **Local LLM integration** - Generates summaries using models running on your machine (privacy-first)
- **Incremental processing** - Only regenerates summaries for new or modified files
- **Configurable prompts** - Optimized for conversational content, easily customizable
- **Flexible deployment** - Point to any Ollama instance via environment variable

### Title Fixer
- **Smart renaming** - Replaces generic file names with descriptive titles from summaries
- **Conflict detection** - Prevents overwrites and warns about naming collisions
- **Preview mode** - Review proposed changes before applying
- **Custom patterns** - Configure which file names to target

---

## About the Name

**Metisem** combines "Metis" (Greek goddess of wisdom and counsel) with "semantic" -reflecting the tool's purpose of bringing intelligent semantic understanding to your knowledge base.

---

## Quick Start

### Installation

**Prerequisites:** Python 3.8+, pip

```bash
# Clone repository
git clone https://github.com/PFunnell/metisem.git
cd metisem

# Install dependencies
pip install -r requirements.txt

# Verify installation
python main.py --help
```

### Generate Semantic Links

```bash
# Preview links (dry run)
python main.py /path/to/vault

# Apply links to notes
python main.py /path/to/vault --apply-links

# Customize similarity threshold and link count
python main.py /path/to/vault --apply-links --similarity 0.7 --max-links 5
```

### Auto-Tag Notes

```bash
# Create tags.txt defining your taxonomy
echo "productivity::Time management, GTD, task organisation" > tags.txt
echo "learning::Education, skill development, studying" >> tags.txt

# Apply tags to vault
python tagger.py /path/to/vault --tags-file tags.txt --apply-tags
```

### Generate Summaries

```bash
# Install and start Ollama (one-time setup)
# Visit https://ollama.ai for installation instructions
ollama serve
ollama pull mistral

# Generate summaries
python summariser_ollama.py /path/to/vault --apply-summaries
```

### Fix Generic Titles

```bash
# Preview proposed renames (requires summaries)
python title_fixer.py /path/to/vault

# Apply renames to files
python title_fixer.py /path/to/vault --apply-fixes

# Custom pattern and title length
python title_fixer.py /path/to/vault --title-pattern "^Draft.*" --max-length 80
```

**Note:** After renaming files, run `python main.py /path/to/vault --delete-links --apply-links` to update link connections.

---

## Usage

### Semantic Linker Options

```bash
python main.py <vault_path> [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--apply-links` | False | Write links to files (default is preview mode) |
| `--similarity` | 0.6 | Minimum similarity score (0.0-1.0) for linking |
| `--min-links` | 0 | Minimum links per note (fallback below threshold) |
| `--max-links` | 9 | Maximum links per note |
| `--model` | all-MiniLM-L6-v2 | Sentence Transformer model to use |
| `--title-weight` | 0.0 | Weight for title similarity (multi-source linking) |
| `--content-weight` | 1.0 | Weight for content similarity (multi-source linking) |
| `--summary-weight` | 0.0 | Weight for summary similarity (multi-source linking) |
| `--clusters` | 0 | K-means clusters for intra-cluster linking |
| `--delete-links` | False | Remove existing link sections before adding new |
| `--force-embeddings` | False | Regenerate all embeddings (ignore cache) |
| `--verbose` | False | Enable debug logging |

**Example workflows:**

```bash
# High-quality links only
python main.py ~/vault --apply-links --similarity 0.8 --max-links 3

# Ensure every note has some links
python main.py ~/vault --apply-links --min-links 2 --max-links 10

# Multi-source linking: combine title, content, and summary similarity
python main.py ~/vault --apply-links --title-weight 0.2 --content-weight 0.5 --summary-weight 0.3

# Remove all auto-generated links
python main.py ~/vault --delete-links --apply-links
```

**Multi-source linking:** Weights are normalised automatically, so `--title-weight 2 --content-weight 1 --summary-weight 1` is equivalent to `--title-weight 0.5 --content-weight 0.25 --summary-weight 0.25`. Default: content-only (1.0:0.0:0.0).

### Auto-Tagger Options

```bash
python tagger.py <vault_path> --tags-file <file> [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--tags-file` | Required | Path to tag definitions file |
| `--apply-tags` | False | Write tags to files (default is preview mode) |
| `--remove-tags` | False | Remove all existing tags |
| `--model` | all-MiniLM-L6-v2 | Sentence Transformer model to use |
| `--force-embeddings` | False | Regenerate all embeddings |
| `--verbose` | False | Enable debug logging |

**Tag file format:**

Each line defines a tag using `tag_name::description` syntax:

```
machine_learning::Neural networks, deep learning, ML algorithms and techniques
philosophy::Metaphysics, epistemology, ethics, philosophical inquiry
project_management::Agile, scrum, project planning and execution
```

The description is embedded and compared semantically to note content.

### Summariser Options

```bash
python summariser_ollama.py <vault_path> [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--apply-summaries` | False | Write summaries to files |
| `--delete-summaries` | False | Remove existing summaries |
| `--force-summaries` | False | Regenerate summaries for all files (ignore cache) |
| `--model` | mistral | Ollama model to use |
| `--max-summary-length` | 128 | Maximum tokens per summary |
| `--max-files` | None | Limit number of files to process |
| `--verbose` | False | Enable debug logging |

**Environment variables:**

- `OLLAMA_HOST` - Ollama server address (default: `localhost:11434`)

**Note:** By default, only new or modified files are processed. Use `--force-summaries` to regenerate all summaries (e.g., when switching models or testing new prompts).

### Title Fixer Options

```bash
python title_fixer.py <vault_path> [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--apply-fixes` | False | Apply renames to files (default is preview mode) |
| `--title-pattern` | `^(New Chat\|Untitled\|Draft\|Temp).*` | Regex pattern for generic titles to fix |
| `--max-length` | 60 | Maximum length for generated titles |
| `--verbose` | False | Enable debug logging |

**Requirements:** Files must have summaries (generated by `summariser_ollama.py`) for title extraction.

**Example:**

```bash
# Preview renames for files starting with "Draft"
python title_fixer.py ~/vault --title-pattern "^Draft.*"

# Apply all renames for default generic patterns
python title_fixer.py ~/vault --apply-fixes
```

---

## How It Works

### Intelligent Caching

All tools implement incremental caching:

1. **Content hashing** -Each file's content is SHA256-hashed
2. **Cache lookup** -Existing embeddings are loaded from `.metisem/`
3. **Change detection** -Cached embeddings are used only if hashes match
4. **Selective re-embedding** -Only modified files are re-processed
5. **Cache update** -New embeddings are saved for future runs

This means the first run is slow (generates all embeddings), but subsequent runs are fast (only processes changed files).

### When to Use `--force-embeddings`

Force cache regeneration when:
- Switching transformer models (`--model`)
- Comparing results across different models
- Suspecting cache corruption

**Not needed** for normal operations - content changes are detected automatically.

### Model Selection

Default model: `all-MiniLM-L6-v2` (fast, good quality, 384-dim embeddings)

Alternative models:
- `all-mpnet-base-v2` -Higher quality, slower (768-dim)
- `paraphrase-multilingual-MiniLM-L12-v2` -Multilingual support
- Any [Sentence Transformers](https://www.sbert.net/docs/pretrained_models.html) model

---

## Configuration

### Performance Tuning

**For large vaults (1000+ notes):**
```bash
# Use smaller batch size to reduce memory
python main.py ~/vault --apply-links --batch-size 16

# Process subset for testing
python main.py ~/vault --max-links 5 --verbose
```

**For GPU acceleration:**
- Install PyTorch with CUDA support
- Verify CUDA availability: `python -c "import torch; print(torch.cuda.is_available())"`
- GPU is used automatically when detected

### Customization

**Link section formatting:**
Links are inserted between HTML comment markers for easy identification:
```markdown
<!-- AUTO-GENERATED LINKS START -->
## Related Notes
[[Note 1]]
[[Note 2]]
<!-- AUTO-GENERATED LINKS END -->
```

**Tag integration:**
Tags are added to YAML front matter:
```yaml
---
tags:
- machine_learning
---
```

---

## Development

### Setup

```bash
# Clone and create environment
git clone https://github.com/PFunnell/metisem.git
cd metisem

# Using conda
conda create -n obsidian-linker python=3.8
conda activate obsidian-linker

# Using venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies and dev tools
pip install -r requirements.txt
pip install mypy pre-commit
pre-commit install
```

### Code Quality

- **Type hints** -Full type annotations on all public functions
- **Linting** -Ruff configured in `pyproject.toml`
- **Pre-commit hooks** -Automatic formatting and validation
- **Type checking** -Run `mypy main.py tagger.py summariser_ollama.py --ignore-missing-imports`

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## Troubleshooting

### Common Issues

**"Module not found" errors**
```bash
pip install -r requirements.txt
python --version  # Verify Python 3.8+
```

**Slow first run**
Expected behaviour - embeddings are being generated for all files. Subsequent runs will be much faster (10-100x speedup with caching).

**Out of memory errors**
Reduce batch size: `--batch-size 8` (default: 32)

**Ollama not running (summariser)**
```bash
# Verify Ollama is running
ollama serve

# Check custom host configuration
export OLLAMA_HOST=localhost:11434

# Test connection
curl http://localhost:11434/api/version
```

**CUDA out of memory**
```bash
# Use CPU instead of GPU
export CUDA_VISIBLE_DEVICES=""

# Or reduce batch size
python main.py ~/vault --apply-links --batch-size 8
```

**Conda environment not activated**
```bash
# If using conda environment
conda activate obsidian-linker

# Verify correct Python
which python  # Should point to conda env
```

**Cache issues**
Delete cache directory to force full rebuild:
```bash
rm -rf /path/to/vault/.metisem/
```

### Advanced Debugging

Enable verbose logging to diagnose issues:
```bash
python main.py ~/vault --verbose
```

---

## Background

This toolkit emerged from the challenge of navigating hundreds of ChatGPT conversation exports imported to Obsidian. By automatically discovering semantic relationships between notes, it transformed an overwhelming collection into a navigable knowledge graph.

While originally designed for AI conversation archives (via [nexus-ai-chat-importer](https://github.com/Superkikim/nexus-ai-chat-importer)), the tools work equally well for any markdown collection - research notes, meeting minutes, blog drafts, or personal knowledge bases.

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code style guidelines
- Development workflow
- Pull request process
- Testing procedures

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Questions?** Open an issue or discussion on GitHub.
