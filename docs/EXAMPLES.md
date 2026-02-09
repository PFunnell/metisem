# Examples

Real-world examples of Metisem commands, outputs, and generated content.

---

## Table of Contents

- [Terminal Output Examples](#terminal-output-examples)
  - [Semantic Linker](#semantic-linker)
  - [Auto-Tagger](#auto-tagger)
  - [Summariser](#summariser)
  - [Title Fixer](#title-fixer)
- [Generated Content Examples](#generated-content-examples)
  - [Link Sections](#link-sections)
  - [YAML Front Matter](#yaml-front-matter)
  - [Summary Blocks](#summary-blocks)
  - [Renamed Files](#renamed-files)
- [Common Workflows](#common-workflows)

---

## Terminal Output Examples

### Semantic Linker

#### Preview Mode (Default)

```bash
$ python main.py ~/vault

INFO - Loading markdown files from /home/user/vault
INFO - Found 247 markdown files
INFO - Loading model: all-MiniLM-L6-v2
INFO - Device: cuda (GPU available)
INFO - Processing files: 100%|████████████████| 247/247 [00:03<00:00, 82.33it/s]
INFO - Cache: 245 hits, 2 new, 0 modified
INFO - Computing similarities...
INFO - Generated 1,834 potential links (similarity >= 0.60)
INFO - Preview mode: No files modified

PREVIEW - Would add 9 links to: machine-learning-basics.md
PREVIEW - Would add 7 links to: neural-networks-intro.md
PREVIEW - Would add 5 links to: deep-learning-architectures.md
...

INFO - Summary:
  - Total files: 247
  - Files with links: 198 (80.2%)
  - Total links: 1,834
  - Avg links per file: 9.3
  - Cache hit rate: 99.2%
INFO - To apply changes, run with --apply-links flag
```

#### Apply Mode

```bash
$ python main.py ~/vault --apply-links

INFO - Loading markdown files from /home/user/vault
INFO - Found 247 markdown files
INFO - Loading model: all-MiniLM-L6-v2
INFO - Device: cpu (GPU not available)
INFO - Processing files: 100%|████████████████| 247/247 [00:12<00:00, 20.58it/s]
INFO - Cache: 247 hits, 0 new, 0 modified
INFO - Computing similarities...
INFO - Generated 1,834 potential links (similarity >= 0.60)
INFO - Writing links to files: 100%|████████| 198/198 [00:01<00:00, 165.42it/s]

INFO - Summary:
  - Total files: 247
  - Files modified: 198
  - Total links: 1,834
  - Avg links per file: 9.3
  - Cache hit rate: 100.0%
INFO - Links successfully applied to vault
```

#### First Run (Building Cache)

```bash
$ python main.py ~/vault --apply-links --similarity 0.7

INFO - Loading markdown files from /home/user/vault
INFO - Found 247 markdown files
INFO - Loading model: all-MiniLM-L6-v2
INFO - Device: cuda (GPU available)
INFO - Processing files: 100%|████████████████| 247/247 [00:45<00:00, 5.49it/s]
INFO - Cache: 0 hits, 247 new, 0 modified
INFO - Embeddings cached to .metisem/embeddings_content.npz
INFO - Computing similarities...
INFO - Generated 1,156 potential links (similarity >= 0.70)
INFO - Writing links to files: 100%|████████| 189/189 [00:01<00:00, 158.23it/s]

INFO - Summary:
  - Total files: 247
  - Files modified: 189
  - Total links: 1,156
  - Avg links per file: 6.1
  - Cache hit rate: 0.0% (first run)
INFO - Subsequent runs will be much faster (cache enabled)
```

#### Multi-Source Linking

```bash
$ python main.py ~/vault --apply-links --title-weight 0.2 --content-weight 0.5 --summary-weight 0.3

INFO - Loading markdown files from /home/user/vault
INFO - Found 247 markdown files
INFO - Multi-source linking enabled: title=0.20, content=0.50, summary=0.30
INFO - Loading model: all-MiniLM-L6-v2
INFO - Device: cuda (GPU available)
INFO - Extracting summaries from notes...
INFO - Summaries found: 231/247 (93.5%)
INFO - Processing files (content): 100%|██| 247/247 [00:03<00:00, 78.91it/s]
INFO - Cache: 247 hits, 0 new, 0 modified
INFO - Processing files (titles): 100%|███| 247/247 [00:01<00:00, 245.12it/s]
INFO - Cache: 247 hits, 0 new, 0 modified
INFO - Processing files (summaries): 100%|█| 231/231 [00:02<00:00, 89.34it/s]
INFO - Cache: 231 hits, 0 new, 0 modified
INFO - Computing weighted similarities...
INFO - Generated 1,672 potential links (weighted similarity >= 0.60)
INFO - Writing links to files: 100%|████████| 195/195 [00:01<00:00, 162.78it/s]

INFO - Summary:
  - Total files: 247
  - Files modified: 195
  - Total links: 1,672
  - Avg links per file: 8.6
  - Cache hit rate: 100.0%
```

### Auto-Tagger

#### Preview Mode

```bash
$ python tagger.py ~/vault --tags-file tags.txt

INFO - Loading markdown files from /home/user/vault
INFO - Found 247 markdown files
INFO - Loading tags from tags.txt
INFO - Loaded 20 tag definitions
INFO - Loading model: all-MiniLM-L6-v2
INFO - Device: cuda (GPU available)
INFO - Processing files: 100%|████████████████| 247/247 [00:03<00:00, 76.54it/s]
INFO - Cache: 247 hits, 0 new, 0 modified
INFO - Processing tag definitions: 100%|████| 20/20 [00:00<00:00, 892.45it/s]
INFO - Matching tags to notes...

PREVIEW - machine-learning-basics.md: Would add tags: [AI_and_automation, data_platforms]
PREVIEW - project-retrospective.md: Would add tags: [productivity, personal_insight]
PREVIEW - council-meeting-notes.md: Would add tags: [local_government, politics]
...

INFO - Tag distribution:
  - productivity: 45 files (18.2%)
  - AI_and_automation: 38 files (15.4%)
  - personal_insight: 32 files (13.0%)
  - data_platforms: 28 files (11.3%)
  - local_government: 24 files (9.7%)
  - cloud_computing: 22 files (8.9%)
  - (14 more tags...)

INFO - Summary:
  - Total files: 247
  - Files with tags: 198 (80.2%)
  - Tags applied: 456
  - Avg tags per file: 2.3
  - Untagged files: 49 (19.8%)
INFO - To apply tags, run with --apply-tags flag
```

#### Apply Mode with Summary-Based Tagging

```bash
$ python tagger.py ~/vault --tags-file tags.txt --apply-tags --tag-summaries

INFO - Loading markdown files from /home/user/vault
INFO - Found 247 markdown files
INFO - Loading tags from tags.txt
INFO - Loaded 20 tag definitions
INFO - Summary-based tagging enabled
INFO - Extracting summaries from notes...
INFO - Summaries found: 231/247 (93.5%)
INFO - Loading model: all-MiniLM-L6-v2
INFO - Device: cuda (GPU available)
INFO - Processing summaries: 100%|███████████| 231/231 [00:02<00:00, 92.18it/s]
INFO - Cache: 231 hits, 0 new, 0 modified
INFO - Processing tag definitions: 100%|████| 20/20 [00:00<00:00, 845.67it/s]
INFO - Matching tags to notes...
INFO - Writing tags to files: 100%|████████| 212/212 [00:00<00:00, 892.34it/s]

INFO - Tag distribution:
  - productivity: 42 files (18.2%)
  - AI_and_automation: 31 files (13.4%)
  - personal_insight: 28 files (12.1%)
  - data_platforms: 25 files (10.8%)
  - local_government: 22 files (9.5%)
  - context_engineering: 19 files (8.2%)
  - (14 more tags...)

INFO - Summary:
  - Total files: 247
  - Files modified: 212 (85.8%)
  - Tags applied: 524
  - Avg tags per file: 2.5
  - Untagged files: 35 (14.2%)
INFO - Tags successfully applied to vault
```

### Summariser

#### Initial Run (Generating Summaries)

```bash
$ python summariser_ollama.py ~/vault --apply-summaries

INFO - Loading markdown files from /home/user/vault
INFO - Found 247 markdown files
INFO - Checking summary status...
INFO - Files needing summaries: 247 (100.0%)
INFO - Summaries to generate: 247
INFO - Using model: mistral
INFO - Ollama host: http://localhost:11434

Generating summaries: 100%|███████████████| 247/247 [42:15<00:00, 10.26s/file]

INFO - Summary generation complete
INFO - Success: 245 files
INFO - Skipped (empty): 2 files
INFO - Failed: 0 files
INFO - Total time: 42m 15s
INFO - Average: 10.3s per file
INFO - Cache hit rate: 0.0% (first run)
```

#### Incremental Update (Fast)

```bash
$ python summariser_ollama.py ~/vault --apply-summaries

INFO - Loading markdown files from /home/user/vault
INFO - Found 247 markdown files
INFO - Checking summary status...
INFO - Files with current summaries: 245 (99.2%)
INFO - Files needing summaries: 2 (0.8%)
INFO - Summaries to generate: 2
INFO - Using model: mistral
INFO - Ollama host: http://localhost:11434

Generating summaries: 100%|███████████████████| 2/2 [00:23<00:00, 11.67s/file]

INFO - Summary generation complete
INFO - Success: 2 files
INFO - Skipped: 0 files
INFO - Failed: 0 files
INFO - Total time: 23s
INFO - Average: 11.7s per file
INFO - Cache hit rate: 99.2%
```

#### Force Regeneration

```bash
$ python summariser_ollama.py ~/vault --apply-summaries --force-summaries

INFO - Loading markdown files from /home/user/vault
INFO - Found 247 markdown files
INFO - Force mode enabled: regenerating all summaries
INFO - Summaries to generate: 247
INFO - Using model: mistral
INFO - Ollama host: http://localhost:11434

Generating summaries: 100%|███████████████| 247/247 [45:32<00:00, 11.07s/file]

INFO - Summary generation complete
INFO - Success: 245 files
INFO - Skipped (empty): 2 files
INFO - Failed: 0 files
INFO - Total time: 45m 32s
INFO - Average: 11.1s per file
INFO - Cache hit rate: 0.0% (forced regeneration)
```

### Title Fixer

#### Preview Mode (Default)

```bash
$ python title_fixer.py ~/vault

INFO - Loading markdown files from /home/user/vault
INFO - Found 247 markdown files
INFO - Scanning for generic titles matching: ^(New Chat|Untitled)( \(\d+\)| \d+)?$
INFO - Found 18 files with generic titles
INFO - Extracting titles from summaries...

PREVIEW - Rename: "New Chat.md"
       -> "Incremental Processing Architecture Design.md"

PREVIEW - Rename: "Untitled 3.md"
       -> "Local Government Digital Transformation Strategy.md"

PREVIEW - Rename: "New Chat (2).md"
       -> "Machine Learning Model Selection Trade-offs.md"

PREVIEW - Rename: "Untitled.md"
       -> "ADHD Medication Dosage Adjustment Notes.md"

...

INFO - Summary:
  - Total files scanned: 247
  - Generic titles found: 18
  - Valid summaries: 18
  - Conflicts detected: 0
INFO - To apply renames, run with --apply-fixes flag
```

#### Apply Mode

```bash
$ python title_fixer.py ~/vault --apply-fixes

INFO - Loading markdown files from /home/user/vault
INFO - Found 247 markdown files
INFO - Scanning for generic titles matching: ^(New Chat|Untitled)( \(\d+\)| \d+)?$
INFO - Found 18 files with generic titles
INFO - Extracting titles from summaries...
INFO - Applying renames: 100%|██████████████████| 18/18 [00:00<00:00, 456.78it/s]

INFO - Renamed: "New Chat.md"
     -> "Incremental Processing Architecture Design.md"

INFO - Renamed: "Untitled 3.md"
     -> "Local Government Digital Transformation Strategy.md"

INFO - Renamed: "New Chat (2).md"
     -> "Machine Learning Model Selection Trade-offs.md"

...

INFO - Summary:
  - Total files scanned: 247
  - Files renamed: 18
  - Conflicts: 0
  - Skipped: 0
INFO - Titles successfully fixed
INFO - Recommendation: Run linker with --delete-links --apply-links to update connections
```

---

## Generated Content Examples

### Link Sections

Links are inserted between HTML comment markers at the end of files.

#### Example: machine-learning-basics.md

```markdown
# Machine Learning Basics

This note covers fundamental concepts in machine learning including
supervised learning, unsupervised learning, and reinforcement learning.

## Key Concepts

- Training data and test data
- Features and labels
- Model evaluation metrics

## Applications

Machine learning is used in recommendation systems, image recognition,
natural language processing, and autonomous systems.

<!-- AUTO-GENERATED LINKS START -->
## Related Notes

[[neural-networks-intro]]
[[supervised-learning-overview]]
[[deep-learning-architectures]]
[[training-validation-test-splits]]
[[model-evaluation-metrics]]
[[backpropagation-explained]]
[[gradient-descent-optimization]]
[[overfitting-and-regularization]]
[[feature-engineering-techniques]]
<!-- AUTO-GENERATED LINKS END -->
```

#### Example: Empty Note (No Links Generated)

```markdown
# Meeting Notes 2024-03-15

Quick reminder: Follow up with Sarah about budget.
```

No link section added (note too short or no similar notes found above threshold).

### YAML Front Matter

Tags are added to YAML front matter at the top of files.

#### Before Tagging

```markdown
# Cloud Migration Strategy

Discussion of moving on-premise infrastructure to Azure...
```

#### After Tagging

```markdown
---
tags:
  - cloud_computing
  - data_platforms
  - public_sector_digital
---

# Cloud Migration Strategy

Discussion of moving on-premise infrastructure to Azure...
```

#### File with Existing Front Matter

**Before:**
```markdown
---
created: 2024-03-15
author: Jane Smith
---

# Machine Learning Pipeline

Designing an end-to-end ML pipeline...
```

**After:**
```markdown
---
created: 2024-03-15
author: Jane Smith
tags:
  - AI_and_automation
  - data_platforms
  - developer_tooling
---

# Machine Learning Pipeline

Designing an end-to-end ML pipeline...
```

### Summary Blocks

Summaries are prepended to files between HTML comment markers.

#### Example: project-retrospective.md

```markdown
<!-- AUTO-GENERATED SUMMARY START -->
**Summary:** Retrospective analysis of the Q1 digital transformation project,
covering successes (early delivery, stakeholder engagement), challenges (resource
constraints, technical debt), and lessons learned for future initiatives. Key
recommendation: invest in automated testing infrastructure.
<!-- AUTO-GENERATED SUMMARY END -->

# Q1 Digital Transformation Project Retrospective

## Overview

This retrospective covers the digital transformation project delivered
in Q1 2024...

## Successes

- Delivered 2 weeks ahead of schedule
- High stakeholder satisfaction (95% approval)
...
```

#### Example: conversation-export.md

```markdown
<!-- AUTO-GENERATED SUMMARY START -->
**Summary:** Discussion about implementing incremental caching for embedding
generation, exploring hash-based change detection vs timestamp comparison,
with final decision to use SHA256 content hashing for reliability across
platforms and file system limitations.
<!-- AUTO-GENERATED SUMMARY END -->

# Embedding Cache Architecture Discussion

**User:** How should we implement caching for embeddings?

**Assistant:** There are several approaches we could consider...
```

### Renamed Files

Title fixer extracts descriptive names from summaries.

#### Example 1: Generic ChatGPT Export

**Before:**
```
New Chat.md
```

**Summary (first few lines):**
```markdown
<!-- AUTO-GENERATED SUMMARY START -->
**Summary:** Technical discussion exploring different approaches for semantic
similarity scoring in knowledge graphs, comparing cosine similarity, Euclidean
distance, and graph-based methods, with implementation examples in Python.
<!-- AUTO-GENERATED SUMMARY END -->
```

**After:**
```
Semantic Similarity Scoring in Knowledge Graphs.md
```

#### Example 2: Untitled Note

**Before:**
```
Untitled 5.md
```

**Summary:**
```markdown
<!-- AUTO-GENERATED SUMMARY START -->
**Summary:** Personal reflection on managing ADHD symptoms during high-stress
work periods, noting effectiveness of medication timing adjustments and
structured break schedules.
<!-- AUTO-GENERATED SUMMARY END -->
```

**After:**
```
Managing ADHD During High-Stress Work Periods.md
```

#### Example 3: Custom Pattern

```bash
$ python title_fixer.py ~/vault --title-pattern "^Draft.*" --max-length 80
```

**Before:**
```
Draft - Meeting Notes.md
```

**Summary:**
```markdown
<!-- AUTO-GENERATED SUMMARY START -->
**Summary:** Detailed notes from the Q2 planning meeting covering budget allocation,
resource priorities, and timeline for the customer portal redesign project.
<!-- AUTO-GENERATED SUMMARY END -->
```

**After:**
```
Q2 Planning Meeting - Customer Portal Redesign Budget and Timeline.md
```

---

## Common Workflows

### Complete Vault Setup

```bash
# 1. Generate summaries (one-time, ~3-4 hours for 2000 files)
python summariser_ollama.py ~/vault --apply-summaries

# 2. Tag notes based on summaries
python tagger.py ~/vault --tags-file tags.txt --apply-tags --tag-summaries

# 3. Generate semantic links
python main.py ~/vault --apply-links

# 4. Fix generic titles (optional)
python title_fixer.py ~/vault --apply-fixes

# 5. Update links after renaming files
python main.py ~/vault --delete-links --apply-links
```

### Daily Maintenance (Incremental Updates)

```bash
# Update summaries for new/modified notes (fast, <30s)
python summariser_ollama.py ~/vault --apply-summaries

# Update tags for changed content
python tagger.py ~/vault --tags-file tags.txt --apply-tags --tag-summaries

# Update links for new connections
python main.py ~/vault --apply-links
```

### Testing Threshold Changes

```bash
# Preview with different thresholds
python main.py ~/vault --similarity 0.5  # Loose
python main.py ~/vault --similarity 0.6  # Balanced (default)
python main.py ~/vault --similarity 0.7  # Conservative
python main.py ~/vault --similarity 0.8  # Strict

# Apply chosen threshold
python main.py ~/vault --apply-links --similarity 0.7
```

### Switching Models

```bash
# Switch to higher-quality model
python main.py ~/vault --model all-mpnet-base-v2 --force-embeddings --apply-links

# Update tagger with same model
python tagger.py ~/vault --tags-file tags.txt --model all-mpnet-base-v2 --force-embeddings --apply-tags
```

### Reset and Rebuild

```bash
# Remove all generated content
python main.py ~/vault --delete-links --apply-links
python tagger.py ~/vault --remove-tags
python summariser_ollama.py ~/vault --delete-summaries

# Clear cache
rm -rf ~/vault/.metisem/

# Rebuild from scratch
python summariser_ollama.py ~/vault --apply-summaries
python tagger.py ~/vault --tags-file tags.txt --apply-tags --tag-summaries
python main.py ~/vault --apply-links
```

### Multi-Source Linking Experiments

```bash
# Content only (default)
python main.py ~/vault --apply-links

# Balanced (title + content + summary)
python main.py ~/vault --apply-links --title-weight 1 --content-weight 1 --summary-weight 1

# Title-heavy (for Zettelkasten)
python main.py ~/vault --apply-links --title-weight 3 --content-weight 1 --summary-weight 1

# Summary-only (for performance)
python main.py ~/vault --apply-links --title-weight 0 --content-weight 0 --summary-weight 1
```

---

## Tips

1. **Always preview first** - Run without `--apply-*` flags to see what would change
2. **Use verbose mode for debugging** - Add `--verbose` to see detailed progress
3. **Test on a backup** - Try on a copy of your vault before running on production
4. **Incremental is default** - Tools automatically detect changes, no flags needed
5. **Check cache location** - Look in `vault/.metisem/` to see cache and logs
6. **Review generated content** - Inspect a few files after each operation to verify quality
7. **Iterate on thresholds** - Start conservative (high threshold) and relax as needed

---

**Questions?** See [CONFIGURATION.md](CONFIGURATION.md) for tuning guidance or [README.md](../README.md) for detailed documentation.
