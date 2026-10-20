# Mac setup (Apple Silicon)

Setting up Metisem on the MacBook Pro 16-inch (2023, M3 Max 16-core CPU / 40-core GPU, 48 GB). On this machine embeddings run on the Apple GPU (MPS) and Ollama runs natively on Metal. Code changes behind this: `dff8ad4` (device selection) and `9e23917` (cache survives moving the vault).

## 1. Prerequisites

```bash
xcode-select --install            # git and build tools, if not already present
brew install --cask miniconda     # or any existing conda install
brew install ollama               # or the Ollama app from ollama.com
```

## 2. Repo and Python environment

```bash
git clone https://github.com/PFunnell/metisem.git
cd metisem
conda create -y -p ./.conda python=3.11
./.conda/bin/python -m pip install torch -r requirements.txt ruff
```

The standard macOS torch wheel includes MPS; no CUDA index URL is needed. `.conda/` is gitignored.

Check torch can see the GPU:

```bash
./.conda/bin/python -c "import torch; print('MPS:', torch.backends.mps.is_available())"
```

Expected: `MPS: True`.

## 3. Ollama

```bash
ollama serve &                    # not needed if the Ollama app is running
ollama pull mistral               # the summariser's default model
```

The summariser expects Ollama at `localhost:11434`; override with `OLLAMA_HOST` in `.env`.

## 4. Move the vault

Copy the **whole vault folder, including `.metisem/`**, and keep the folder name (`GPT2025-12-02`). The cache is keyed by path relative to the vault, and caches written on Windows are converted the first time a tool opens them, using the vault paths in the run logs or else the folder name.

- With `.metisem/`: nothing is re-embedded or re-summarised.
- Without it: embeddings are rebuilt; summaries already in notes are kept (the summariser records them instead of regenerating).
- Never run `--force-summaries` on the copied vault unless you mean to regenerate and overwrite every summary.

Back up the vault before the first run on the Mac; the tools edit notes in place.

## 5. Test vault path

Copy `.env` from the Windows checkout, then set the Mac path:

```bash
# .env
TEST_VAULT_PATH=/Users/<you>/<path>/GPT2025-12-02
```

Integration tests read `TEST_VAULT_PATH` from the process environment, not from `.env`, so also export it when running them:

```bash
export TEST_VAULT_PATH=/Users/<you>/<path>/GPT2025-12-02
```

## 6. Verify

Unit tests (no vault, no Ollama):

```bash
./.conda/bin/python -m pytest -m "not integration"
```

Expected: all pass (185 on Windows at `9e23917`).

First real run, preview only (writes nothing to notes):

```bash
./.conda/bin/python main.py "$TEST_VAULT_PATH"
```

Check the log for:

- `Embedding device: mps`
- `Change detection: 0 new, 0 modified, 0 deleted, <N> unchanged` (or close to it)

If it reports thousands of new files, stop: the cache conversion didn't match the vault. Check the folder name is unchanged and that `.metisem/metisem.db` came across.

Summariser, incremental (should process few or no files):

```bash
./.conda/bin/python summariser_ollama.py "$TEST_VAULT_PATH" --apply-summaries
```

The log line `Cache: ... (<N> existing summaries adopted), <M> need processing` should show `M` near zero.

## Troubleshooting

| Symptom | Check |
|---|---|
| `Embedding device: cpu` | `torch.backends.mps.is_available()`; reinstall torch in `.conda`; force with `--device mps` to see the error |
| MPS error on an operation | Run with `--device cpu` to confirm it's MPS-specific; set `PYTORCH_ENABLE_MPS_FALLBACK=1` to fall back per operation |
| `Cannot connect to Ollama` | `ollama serve` running; `curl localhost:11434/api/version` |
| Integration tests skipped | `TEST_VAULT_PATH` exported in the shell, not only in `.env` |
| Everything looks new after the move | Folder name changed, or `.metisem/` not copied; see step 4 |
