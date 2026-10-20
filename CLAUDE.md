# CLAUDE.md

Metisem: Python CLI tools that link, tag, summarise (local Ollama) and retitle notes in a markdown vault. Usage is in [README.md](README.md) and [docs/CONFIGURATION.md](docs/CONFIGURATION.md); notes index in [docs/index.md](docs/index.md).

## Must-holds

- **The tools rewrite vault files in place.** Run against the test vault or a backup, never the user's live vault, and preview (no `--apply-*` flag) first.
- **Test vault:** `TEST_VAULT_PATH` (last known `D:\Obsidian\GPT\GPT2025-12-02`). Integration tests read it from the process environment, not from `.env`; without it they skip.
- **Generated blocks are delimited by HTML comment markers** (`<!-- AUTO-GENERATED LINKS START -->`, `... SUMMARY START -->`, with matching `END`). Change marker handling only together with `tests/unit/test_markers.py`; a mismatch strands or duplicates blocks across a whole vault.
- **After `title_fixer.py --apply-fixes`, re-link** (`main.py --delete-links`, then `--apply-links`): renames break existing wikilinks.
- **Cache keys in `.metisem/` are vault-relative POSIX paths** so a copied vault (Windows → Mac) keeps its cache; never write absolute paths into the cache. `--force-summaries` overwrites every summary block in the vault.
- **Summariser needs Ollama running** at `localhost:11434`; the default model is `mistral`. A full-vault run takes hours, so don't start one unasked.
- **Target machine is a MacBook Pro 16-inch (2023), M3 Max 16-core CPU / 40-core GPU, 48 GB; embeddings on MPS.** The Windows machine's GPU is broken (CUDA unavailable); there, embeddings run on CPU. Keep code cross-platform: no Windows-only paths or `.bat`-only workflows.
- **Python env:** conda env in `.conda/` (Python 3.11; interpreter `.conda/python.exe` on Windows, `.conda/bin/python` on macOS). Tests: `pytest -m "not integration"` for unit tests, `pytest` for all.
- **UK English** in code, docs and output.
