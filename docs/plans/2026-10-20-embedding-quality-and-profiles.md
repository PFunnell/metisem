# Plan: embedding quality, link/tag selection and hardware profiles

Status: proposed, 2026-10-20. Follows PR #1 (summariser `num_ctx`, thinking off) and the embedding cache fix on `fix/embedding-cache-and-text`.

## Decision: one codebase with profiles, not separate releases

Keep a single codebase. Split configuration into two layers with different owners:

| Layer | Lives in | Travels with | Holds |
| --- | --- | --- | --- |
| **Vault config** | `<vault>/.metisem/config.toml` | the vault | Anything that changes *results*: embedding model, text-prep version, link strategy and thresholds, tag file and tag rule, clustering, summary prompt |
| **Machine profile** | `~/.config/metisem/profile.toml` (or `METISEM_PROFILE=<name>`) | the machine | Anything that only changes *speed*: device, batch size, `max_seq_length` cap, precision, Ollama host, LLM tag, `num_ctx`, parallelism |

Precedence: CLI flag > machine profile > vault config > built-in defaults. A machine profile that sets a result-changing key is an error, not an override.

Why not a Mac release and a GTX 1660 Super release:

- The vault moves between machines with its `.metisem/` cache. Two releases with different embedders would rewrite every links block depending on which machine ran last, and each would treat the other's cache as missing.
- Every fix would need landing twice; the branches drift.
- The real differences are compute limits, which a profile expresses in a few lines.

Releases still matter, for a different reason: tag a version whenever a change forces a re-embed or rewrites vault files (as `EMBED_TEXT_VERSION` 2 does), and say so in a changelog.

### Profiles to ship

| Profile | Device | Embedding batch / seq cap | Summariser model (Ollama) | `num_ctx` |
| --- | --- | --- | --- | --- |
| `cpu` (Windows box, GPU broken) | cpu | 8 / 2048 | `mistral` until replaced; small model only | 16384 |
| `gtx1660s` (6 GB VRAM, compute capability 7.5) | cuda, fp16 | 16 / 4096 | a ~4B model at Q4 to stay inside 6 GB with context | 16384 |
| `m3max` (MacBook Pro 16-inch 2023, M3 Max 40-core GPU, 48 GB) | mps | 8 / 8192 | Qwen3.6-35B-A3B, MLX 4-bit DWQ, non-thinking | 32768 |

The embedding model itself is a vault setting, so it must run acceptably on the weakest machine that will touch the vault. Qwen3-Embedding-0.6B fits all three; CPU runs will be slow on a full re-embed but fine incrementally.

## Work items, in order

### 1. Summary placement (bug 3)

- `insert_summary` prepends the block above YAML front matter; Obsidian then ignores the front matter and `add_tag` creates a second block.
- Confirm on the test vault: count notes whose first line is the summary marker and that also contain a later `---` front matter block.
- Fix: insert after front matter; when replacing an existing block that sits above front matter, move it.
- Repair script (`scripts/repair_front_matter.py`, preview by default): move misplaced summary blocks, merge duplicate front matter (union of `tags`, original keys win). Run on a copy of the test vault first.
- Tests alongside `tests/unit/test_markers.py`, per CLAUDE.md.

### 2. Link and tag selection independent of model

- Links: add `--link-strategy mutual-knn` (default once validated): link i→j only if each is in the other's top k. Keep `--similarity` as an optional floor. Suppresses hub notes that link to everything.
- Tags: replace the absolute `--tag-threshold` with a margin rule: tag if score ≥ note's mean tag score + `--tag-margin` (in standard deviations), capped by `--max-tags`.
- Both move into vault config.

### 3. Evaluation set before any model swap

- Hand-judge 40–50 note pairs from the test vault: related / unrelated, plus 20 notes with their correct tags.
- `scripts/eval_links.py`: precision@k for links, precision/recall for tags, per model and strategy. Results logged to `run_logs`.
- Without this, model and threshold changes are judged by eye.

### 4. Embedding model and long notes

- Candidate: Qwen3-Embedding-0.6B (32K context, 1024 dims, Apache 2.0). Alternative: EmbeddingGemma 2 (8K context, 768 dims).
- Long notes: split into ~512-token chunks, embed, average the normalised chunk vectors. Store one vector per note so the cache shape doesn't change.
- Prompts: none for note-to-note linking; a query instruction for tag descriptions (`Instruct: Given a topic description, find notes about it\nQuery: …`), notes as documents.
- Encode with `normalize_embeddings=True`; optionally store float16 and 512 Matryoshka dims.
- Compare against MiniLM on the evaluation set; adopt only if it wins.

### 5. Clustering

- Current: `KMeans` on unnormalised vectors, user-chosen k, used as a hard filter that blocks cross-cluster links.
- Replace with UMAP (cosine) → `sklearn.cluster.HDBSCAN`; no k to guess, outliers labelled as noise.
- Use clusters as a soft signal (small similarity bonus within a cluster), not a filter.
- Add an output mode: name each cluster with the local LLM and write candidate tags and map-of-content notes for review.

### 6. Summariser

- Expose `--max-input-words` and `--num-ctx` (currently hard-coded 6,144 words / 16,384), with defaults from the machine profile.
- One call, structured output: Ollama `format` JSON schema returning summary, title and 3–5 keywords; `title_fixer` uses the title instead of the summary's first sentence.
- Prompt: forbid meta openers ("The conversation discusses…"), which inflate summary-to-summary similarity.
- Record the summarising model per note so summaries from a weaker model can be regenerated selectively.
- Sampling per model family (Qwen non-thinking: temperature 0.7, top_p 0.8, top_k 20, presence_penalty 1.5); A/B against current 0.3.

### 7. Housekeeping

- README drift: `--min-links` default is 1 in code, 0 in README; tagger has `--tag-threshold` (0.4) though README says there is no threshold parameter.
- After the cache fix, old `embeddings_<vault>_<model>.npz` files and embedding-written `file_metadata` rows are unused. Add a `--prune-cache` option rather than deleting automatically.

## Open questions

- Does the test vault's importer write YAML front matter on every note? Decides how much item 1's repair touches.
- Which machines will run full re-embeds, and which only incremental runs? Decides whether the embedder must be fast on CPU.
