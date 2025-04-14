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

## 🛠 Requirements

- Python 3.8+
- Dependencies (install via pip):

```bash
pip install sentence-transformers scikit-learn pyyaml tqdm
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

## ⚠️ Notes

- Markdown files must use UTF-8 encoding.
- Wikilinks and tags are only inserted if applicable.
- Make backups before running `--apply-links` or `--apply-tags`.

## 📸 Example Screenshot

![Semantic links in Obsidian](metisem1.png)

## 🧠 Background

This project emerged from the need to structure and explore hundreds of ChatGPT conversations imported to Obsidian via [nexus-ai-chat-importer](https://github.com/Superkikim/nexus-ai-chat-importer). By revealing semantic relationships and tagging notes automatically, it became much easier to surface meaningful connections and themes.

While designed for that use case, it is equally useful for anyone working with a large Obsidian vault or markdown knowledge base—whether notes, research, blog posts, or meeting minutes.

---

Contributions welcome. Feel free to fork and adapt!