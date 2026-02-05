# Configuration Guide

Comprehensive guide to tuning Metisem for your vault.

---

## Table of Contents

- [Threshold Tuning](#threshold-tuning)
- [Model Selection](#model-selection)
- [Tag Descriptor Authoring](#tag-descriptor-authoring)
- [Performance Optimization](#performance-optimization)
- [Multi-Source Linking](#multi-source-linking)

---

## Threshold Tuning

### Semantic Linker Similarity Threshold

The `--similarity` parameter controls link quality vs quantity trade-off.

**Range:** 0.0 to 1.0 (cosine similarity between embeddings)

**Guidelines:**

| Threshold | Effect | Use Case |
|-----------|--------|----------|
| 0.4-0.5 | Very loose - many links, some noise | Exploratory, discovering distant connections |
| 0.6 | Balanced (default) | General use, good signal-to-noise ratio |
| 0.7 | Conservative - fewer, high-quality links | Technical vaults, precision over recall |
| 0.8+ | Very strict - only very similar notes | Curated vaults, avoiding any false positives |

**Examples:**

```bash
# Academic vault with technical content
python main.py ~/research --apply-links --similarity 0.7

# Personal notes with diverse topics
python main.py ~/notes --apply-links --similarity 0.55

# Exploratory mode for a new vault
python main.py ~/vault --similarity 0.5 --max-links 15
```

**Tuning advice:**

1. Start with default (0.6), run in preview mode without `--apply-links`
2. Review proposed links - are they relevant?
3. Adjust up if too many weak connections, down if missing obvious links
4. Fine-tune in 0.05 increments

**Threshold too high:**
- Few or no links generated
- Missing obvious semantic connections
- Every note feels isolated

**Threshold too low:**
- Links feel tangential or forced
- Noise overwhelms signal
- Graph view becomes cluttered

### Auto-Tagger Threshold

The tagger uses a fixed threshold (0.15-0.30 range) optimised for tag assignment. Unlike linking, tags are categorical, so lower thresholds work well.

**No user-facing threshold parameter** - threshold is tuned internally based on descriptor quality. Focus on writing distinctive tag descriptions (see [Tag Descriptor Authoring](#tag-descriptor-authoring)).

---

## Model Selection

### Hardware-Aware Recommendations

**CPU-only machines:**
- **Best:** `all-MiniLM-L6-v2` (384-dim, ~120MB)
  - Fast inference, good quality
  - Recommended for vaults <5000 notes
- **Alternative:** `paraphrase-MiniLM-L3-v2` (384-dim, ~60MB)
  - Fastest, slightly lower quality
  - Good for very large vaults or low-spec hardware

**GPU-enabled machines (CUDA):**
- **Best:** `all-mpnet-base-v2` (768-dim, ~420MB)
  - Higher quality embeddings
  - Better semantic understanding
  - ~2x slower than MiniLM but GPU accelerates this
- **Alternative:** `all-distilroberta-v1` (768-dim, ~290MB)
  - Good balance of speed and quality

**Multilingual vaults:**
- `paraphrase-multilingual-MiniLM-L12-v2` (384-dim, ~470MB)
- `paraphrase-multilingual-mpnet-base-v2` (768-dim, ~1.1GB)

### Trade-offs

| Aspect | MiniLM-L6 | MPNet-base |
|--------|-----------|------------|
| Speed | Fast (~500 notes/min CPU) | Moderate (~200 notes/min CPU) |
| Quality | Good | Excellent |
| Embedding size | 384-dim | 768-dim |
| Memory usage | Low (~1GB) | Medium (~2GB) |
| Use case | General purpose | Technical/research vaults |

### Switching Models

When switching models, **always** use `--force-embeddings` to regenerate the cache:

```bash
# Switch from default to higher-quality model
python main.py ~/vault --apply-links --model all-mpnet-base-v2 --force-embeddings
```

Cache is model-specific - embeddings from different models are incompatible.

### Verifying CUDA Availability

```bash
# Check if GPU will be used
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Expected output:
# CUDA available: True  (GPU will be used)
# CUDA available: False (CPU fallback)
```

---

## Tag Descriptor Authoring

High-quality tag descriptions are critical for semantic tag matching.

### Format

```
tag_name::description
```

- **tag_name:** Short, snake_case identifier (no spaces, no `#`)
- **description:** 1-3 sentences describing the tag's semantic space

### Guidelines

**1. Be distinctive - avoid overlap between tags**

Good:
```
machine_learning::Neural networks, deep learning architectures, gradient descent, backpropagation, ML model training
data_science::Statistical analysis, data visualization, exploratory data analysis, hypothesis testing, A/B testing
```

Bad (too much overlap):
```
machine_learning::Machine learning and data analysis techniques
data_science::Data analysis and machine learning methods
```

**2. Focus on core concepts, not edge cases**

Good:
```
philosophy::Metaphysics, epistemology, ethics, philosophical arguments, ontology, phenomenology
```

Bad (too specific):
```
philosophy::Kant's categorical imperative and Heidegger's Dasein
```

**3. Include related terms and synonyms**

Good:
```
productivity::Time management, GTD, task organization, Pomodoro technique, efficiency, workflow optimization
```

Bad (too narrow):
```
productivity::Getting things done
```

**4. Use 1-3 sentences (10-30 words)**

- Too short (<10 words): Not enough semantic signal
- Too long (>50 words): Dilutes core concept, increases false positives

**5. Maintain consistent specificity level**

If one tag is very broad (`science`) and another very narrow (`quantum_chromodynamics`), the narrow tag will rarely match. Keep tags at similar abstraction levels within a domain.

### Examples: Good vs Bad

**Good:**
```
software_engineering::Software design patterns, code architecture, refactoring, testing methodologies, CI/CD
project_management::Agile methodologies, Scrum, sprint planning, project coordination, stakeholder management
```

**Bad:**
```
coding::Programming  (too vague)
agile_scrum_ceremonies::Daily standups, sprint retrospectives  (too narrow, should be broader 'project_management')
```

### Testing Tag Quality

1. Run tagger in preview mode: `python tagger.py ~/vault --tags-file tags.txt`
2. Review tag assignments - do they match your intuition?
3. If a tag is never assigned: description too narrow or distinctive
4. If a tag is assigned everywhere: description too broad or overlaps with others
5. Iteratively refine descriptions

---

## Performance Optimization

### Incremental Mode (Default)

Both linker and summariser use incremental processing by default:

- **First run:** Processes all files, generates all embeddings/summaries (~4 hours for 2000 files)
- **Subsequent runs:** Only processes new/modified files (<30 seconds for unchanged vault)
- **Change detection:** SHA256 content hashing + mtime checking

**No flags needed** - incremental mode is automatic.

### Force Mode

Use `--force-embeddings` (linker/tagger) or `--force-summaries` (summariser) to regenerate everything:

**When to use:**
- Switching models
- Testing new parameters
- Suspected cache corruption
- After manual file modifications outside Metisem

**When NOT to use:**
- Normal operations
- Content changes are detected automatically

```bash
# Force regeneration
python main.py ~/vault --apply-links --force-embeddings
python summariser_ollama.py ~/vault --apply-summaries --force-summaries
```

### Batch Size Tuning (GPU Memory)

Default batch size: 32

**Reduce if:**
- Out of memory errors
- GPU memory <4GB
- Processing very large documents

```bash
# Reduce batch size for memory constraints
python main.py ~/vault --apply-links --batch-size 16

# Aggressive reduction for low-memory GPUs
python main.py ~/vault --apply-links --batch-size 8
```

**Increase if:**
- GPU memory >8GB
- Small documents (<2KB average)
- Maximizing throughput

```bash
# Increase batch size for high-memory GPUs
python main.py ~/vault --apply-links --batch-size 64
```

### Cache Location

Cache stored in `.metisem/` directory within vault:

```
vault/
├── .metisem/
│   ├── metisem.db           # SQLite database (metadata)
│   ├── embeddings_*.npz     # Cached embeddings
│   └── run_logs.db          # Execution logs
```

**Cache size:** ~1-5MB per 1000 notes (varies by model)

**To clear cache:**
```bash
rm -rf /path/to/vault/.metisem/
```

### Processing Subsets (Testing)

Use `--max-files` to process a subset:

```bash
# Test on first 100 files
python summariser_ollama.py ~/vault --apply-summaries --max-files 100

# Preview links on subset
python main.py ~/vault --max-links 5 --verbose
```

---

## Multi-Source Linking

Combine title, content, and summary similarity with configurable weights.

### Parameters

- `--title-weight`: Weight for title similarity (default: 0.0)
- `--content-weight`: Weight for content similarity (default: 1.0)
- `--summary-weight`: Weight for summary similarity (default: 0.0)

**Weights are normalised automatically** - only ratios matter.

### Use Cases

**Default (content-only):**
```bash
python main.py ~/vault --apply-links
# Equivalent to: --title-weight 0 --content-weight 1 --summary-weight 0
```

**Balanced multi-source:**
```bash
# Equal weight to all sources
python main.py ~/vault --apply-links --title-weight 1 --content-weight 1 --summary-weight 1

# Normalised to: 0.33 : 0.33 : 0.33
```

**Title-heavy (short notes):**
```bash
# Prioritise title similarity for brief notes
python main.py ~/vault --apply-links --title-weight 3 --content-weight 1 --summary-weight 1

# Normalised to: 0.6 : 0.2 : 0.2
```

**Summary-focused (long documents):**
```bash
# Use summaries for computational efficiency
python main.py ~/vault --apply-links --title-weight 0 --content-weight 0 --summary-weight 1
```

### When to Use Multi-Source Linking

**Title weight >0:**
- Notes with descriptive, meaningful titles
- Short notes where title carries significant semantic content
- Zettelkasten-style vaults with structured naming

**Summary weight >0:**
- Long documents (>5KB) where full content is noisy
- Vaults with high-quality summaries (generated by summariser)
- Computational efficiency (summaries are shorter than full content)

**Content-only (default):**
- General use
- Notes without summaries
- When titles are generic (e.g., timestamps)

### Equivalence

These are equivalent (weights normalised):
```bash
--title-weight 2 --content-weight 1 --summary-weight 1  # Ratio: 2:1:1
--title-weight 0.5 --content-weight 0.25 --summary-weight 0.25  # Normalised
```

### Requirements

- **Title weight:** Requires notes with titles (extracted from `# Heading` or filename)
- **Summary weight:** Requires summaries (generated by `summariser_ollama.py`)
- Missing data: Falls back to available sources (e.g., if no summary, only uses title+content)

---

## Advanced Topics

### Custom Prompts (Summariser)

Edit `summariser_ollama.py` line 85-101 to customize the summary prompt:

```python
prompt = (
    "Your custom prompt here...\n"
    f"{text}\n\n"
    "Instructions for summary format..."
)
```

### Link Section Formatting

Links inserted between HTML comment markers:

```markdown
<!-- AUTO-GENERATED LINKS START -->
## Related Notes
[[Note 1]]
[[Note 2]]
<!-- AUTO-GENERATED LINKS END -->
```

To customize section heading, edit `metisem/core/markers.py`.

### Tag Front Matter Format

Tags added to YAML front matter:

```yaml
---
tags:
  - machine_learning
  - data_science
---
```

Obsidian recognises this format natively. For alternative formats (e.g., inline tags), modify `tagger.py` tag insertion logic.

---

**Questions or need help tuning?** Open an issue on GitHub with:
- Vault size (number of notes)
- Hardware specs (CPU/GPU, RAM)
- Current parameters and observed behaviour
- Example notes showing the issue
