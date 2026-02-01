# Obsidian Semantic Linker & Auto-Tagger

This project provides two powerful command-line tools to enhance your Obsidian markdown vault:
- `main.py`: Automatically generates semantic **backlinks** between related notes.
- `tagger.py`: Applies intelligent **tags** to notes based on their content using a custom tag list.

Both tools use [Sentence Transformers](https://www.sbert.net/) to identify semantic similarity between notes and offer robust caching for performance.

> 🧠 Originally designed to process ChatGPT export files imported into Obsidian using [nexus-ai-chat-importer](https://github.com/Superkikim/nexus-ai-chat-importer), this project works equally well on any collection of markdown files—making it ideal for researchers, PKM enthusiasts, or anyone managing a large markdown knowledge base.

## 🔗 Features

### `main.py` – Semantic Link Generator
- Scans your vault and embeds markdown note content.
- Computes cosine similarity to identify related files.
- Adds or updates a `## Related Notes` section in each file using Obsidian `[[wikilinks]]`.
- Caches embeddings to `.obsidian_linker_cache/` for performance.
- Customizable similarity thresholds, link count, and model choice.

### `tagger.py` – Auto Tagger
- Uses a `tags.txt` file with tag::description format.
- Embeds both note content and tag descriptions.
- Finds the best-matching tag for each note based on semantic similarity.
- Inserts the best tag into YAML front matter (`tags:`).
- Optionally supports removing all tags from notes.

## 🛠 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- (Optional) CUDA-capable GPU for faster embedding generation

### Install from Source

1. Clone the repository:
```bash
git clone https://github.com/PFunnell/metisem.git
cd metisem
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Verify installation:
```bash
python main.py --help
python tagger.py --help
```

### For Summarizer

The summarizer requires [Ollama](https://ollama.ai/) running locally:

1. Install Ollama from https://ollama.ai/
2. Start the Ollama service:
```bash
ollama serve
```
3. Pull a model (e.g., mistral):
```bash
ollama pull mistral
```

## 🚀 Usage

### Generate Semantic Links

```bash
python main.py /path/to/your/vault --apply-links
```

**Options:**
- `--similarity 0.6` – similarity threshold
- `--min-links 1 --max-links 5` – control number of links per note
- `--model all-MiniLM-L6-v2` – transformer model to use
- `--delete-links` – removes old link blocks before writing
- `--force-embeddings` – regenerate all embeddings

### Auto-Tag Notes

```bash
python tagger.py /path/to/your/vault --tags-file tags.txt --apply-tags
```

**Options:**
- `--tags-file tags.txt` – path to tag file (see format below)
- `--remove-tags` – clears all existing `tags:` entries
- `--model all-MiniLM-L6-v2` – transformer model
- `--force-embeddings` – ignore cache and regenerate

## 🏷 Tag File Format (`tags.txt`)

Each line must be:

```
tag_name::A short description used for semantic matching
```

Example:

```
local_government::Topics related to city councils, county administration...
AI_and_automation::Discussions about artificial intelligence, machine learning...
```

## 📁 Caching

Embeddings are stored in `.obsidian_linker_cache/` using a model-specific cache file. This significantly speeds up repeated runs.

## ⚠️ Important Notes

- **Always backup your vault before running with `--apply-links`, `--apply-tags`, or `--apply-summaries`**
- Markdown files must use UTF-8 encoding
- The first run will be slow as it generates embeddings; subsequent runs use cached embeddings
- GPU acceleration (CUDA) is automatically used if available

## 🛠 Development Setup

### Setting Up Development Environment

1. Fork and clone the repository
2. Create a virtual environment (venv or conda):
```bash
# Using venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using conda
conda create -n obsidian-linker python=3.8
conda activate obsidian-linker
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Install development tools (optional):
```bash
pip install mypy pre-commit
pre-commit install
```

### Running Tests

Currently, this project uses manual verification against test vaults. Automated testing is planned for future releases.

### Code Quality

- Type hints are used throughout the codebase
- Run `mypy` for type checking:
```bash
mypy main.py tagger.py summariser_ollama.py --ignore-missing-imports
```

## 🐛 Troubleshooting

### "Cannot connect to Ollama" error
- Ensure Ollama is running: `ollama serve`
- Check Ollama is listening on localhost:11434
- Set custom host: `OLLAMA_HOST=custom:port python summariser_ollama.py ...`

### Slow embedding generation
- First run always generates embeddings from scratch
- Consider using a smaller model for faster processing
- GPU acceleration requires CUDA-compatible GPU and drivers

### When to use `--force-embeddings`
Use this flag to regenerate embeddings when:
- You've changed the transformer model (`--model`)
- You suspect cached embeddings are corrupted
- You want to use a different embedding model for comparison

**Note:** This rebuilds all embeddings from scratch and can be slow on large vaults. The cache automatically detects file content changes via SHA256 hashing, so you typically don't need this flag for normal operations.

### "Module not found" errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check you're using Python 3.8 or higher: `python --version`

### Out of memory errors
- Reduce `--batch-size` (default: 32)
- Use a smaller transformer model
- Process fewer files at once with `--max-files`

### Cache invalidation
- Delete `.obsidian_linker_cache/` to rebuild all embeddings
- Use `--force-embeddings` to regenerate on next run

## 📸 Example Screenshot

![Semantic links in Obsidian](docs/images/metisem1.png)

## 🧠 Background

This project emerged from the need to structure and explore hundreds of ChatGPT conversations imported to Obsidian via [nexus-ai-chat-importer](https://github.com/Superkikim/nexus-ai-chat-importer). By revealing semantic relationships and tagging notes automatically, it became much easier to surface meaningful connections and themes.

While designed for that use case, it is equally useful for anyone working with a large Obsidian vault or markdown knowledge base—whether notes, research, blog posts, or meeting minutes.

---

Contributions welcome. Feel free to fork and adapt!