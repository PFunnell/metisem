"""Auto-tagger for markdown vaults.

Compatible with Obsidian, Logseq, and other markdown-based knowledge bases.
This module automatically tags notes based on semantic similarity between note content
and tag descriptions. Tags are added to YAML front matter.
"""
import re
import argparse
import hashlib
import numpy as np
from pathlib import Path
import logging
from typing import List, Dict
import yaml
import torch
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from metisem.core.files import find_markdown_files
from metisem.core.cache import generate_embeddings
from metisem.core.embeddings import encode_texts
from metisem.core.database import CacheDatabase
from metisem.core.run_logger import RunLogger

logger = logging.getLogger(__name__)

# --- Constants ---
YAML_SEP = '---'
TAGS_KEY = 'tags'
TAG_DESC_SEP = '::'

# --- Tag Loading ---

def load_tags(file: str) -> Dict[str, str]:
    """Load tag definitions from file. Format: tag_name::description per line."""
    tags = {}
    for line in Path(file).read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if TAG_DESC_SEP in line:
            name, desc = map(str.strip, line.split(TAG_DESC_SEP, 1))
        else:
            name = desc = line
        if name:
            tags[name] = desc or name
    return tags

# --- Front Matter Manipulation ---

def write_front_matter(path: Path, data: Dict, rest: str) -> None:
    """Write YAML front matter block to file with given data and remaining content."""
    fm = yaml.safe_dump(data, sort_keys=False).strip()
    new = f"{YAML_SEP}\n{fm}\n{YAML_SEP}\n{rest.lstrip()}"
    path.write_text(new, encoding='utf-8')


def remove_tags(path: Path) -> bool:
    """Remove tags section from YAML front matter. Returns True if tags were removed."""
    text = path.read_text(encoding='utf-8')
    # Match the YAML front‑matter block (start and end “---”)
    fm_match = re.match(
        r'^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)',
        text,
        flags=re.MULTILINE
    )
    if not fm_match:
        return False

    fm_content, rest = fm_match.group(1), fm_match.group(2)
    lines = fm_content.splitlines()
    new_lines = []
    skip = False

    for line in lines:
        if skip:
            # skip every “- item” list line under tags:
            if re.match(r'^\s*-\s+\S+', line):
                continue
            skip = False

        # if we hit “tags:” at top level, start skipping its block
        if re.match(rf'^\s*{TAGS_KEY}\s*:\s*$', line):
            skip = True
            continue

        new_lines.append(line)

    # nothing changed: no tags key or empty tags
    if len(new_lines) == len(lines) and not skip:
        return False

    # write back updated front matter or drop it entirely
    if new_lines:
        new_fm = "\n".join(new_lines)
        new_content = f"---\n{new_fm}\n---\n{rest.lstrip()}"
        path.write_text(new_content, encoding='utf-8')
    else:
        path.write_text(rest, encoding='utf-8')

    logger.debug(f"Removed tags in {path.name}")
    return True



def add_tag(path: Path, tag: str) -> bool:
    """Add tag to YAML front matter. Creates front matter if it doesn't exist. Returns True on success."""
    text = path.read_text(encoding='utf-8')
    # Split off the front‑matter block (if any)
    m = re.match(
        r'^\s*---\s*\r?\n'      # opening ---
        r'([\s\S]*?)'           # capture everything inside
        r'\r?\n---\s*\r?\n'     # closing ---
        r'([\s\S]*)',           # rest of file
        text,
        flags=re.MULTILINE
    )
    if m:
        fm_block, rest = m.group(1), m.group(2)
        lines = fm_block.splitlines()
    else:
        # No front matter yet
        lines = []
        rest = text

    new_lines = []
    saw_tags = False
    inserted = False

    for line in lines:
        new_lines.append(line)
        if re.match(rf'^\s*{TAGS_KEY}\s*:\s*$', line):
            saw_tags = True
            # Insert our new tag immediately under 'tags:'
            new_lines.append(f'- {tag}')
            inserted = True
        elif saw_tags:
            # we already inserted, now copy existing list items
            if re.match(r'^\s*-\s+\S+', line):
                # skip duplicates
                if line.strip() == f'- {tag}':
                    continue
                new_lines.append(line)
            else:
                saw_tags = False

    if not inserted:
        # No existing tags key: tack it on at the end of the front matter
        new_lines.append(f'{TAGS_KEY}:')
        new_lines.append(f'- {tag}')

    # Rebuild file
    if lines:
        new_fm = '\n'.join(new_lines)
        new_text = f'---\n{new_fm}\n---\n{rest.lstrip()}'
    else:
        # Create a front matter block from scratch
        new_text = f'---\n{TAGS_KEY}:\n- {tag}\n---\n{rest}'

    path.write_text(new_text, encoding='utf-8')
    logger.debug(f'Applied tag in {path.name}')
    return True


# --- Tag Embedding Cache ---

def load_and_embed_tags(
    tags: Dict[str, str],
    model: SentenceTransformer,
    model_name: str,
    batch_size: int,
    device: str,
    vault_path: str,
    force: bool = False
) -> np.ndarray:
    """Load tags and generate/cache embeddings.

    Args:
        tags: Dictionary mapping tag names to descriptions
        model: SentenceTransformer model instance
        model_name: Name of the model (for cache)
        batch_size: Batch size for encoding
        device: Device to use ('cpu' or 'cuda')
        vault_path: Path to the vault (for cache location)
        force: If True, ignore cache and regenerate embeddings

    Returns:
        Array of tag embeddings in original tag order
    """
    cache_dir = Path(vault_path) / ".metisem"
    db = CacheDatabase(cache_dir / "metisem.db")

    to_embed = []
    cached_embeddings = []

    for tag_name, description in tags.items():
        desc_hash = hashlib.sha256(description.encode('utf-8')).hexdigest()

        if not force:
            cached = db.get_tag_embedding(tag_name, model_name)
            if cached and cached['content_hash'] == desc_hash:
                cached_embeddings.append((tag_name, cached['embedding']))
                continue

        # Tag needs embedding
        to_embed.append((tag_name, description, desc_hash))

    # Generate embeddings for new/changed tags
    if to_embed:
        logger.info(f"Generating embeddings for {len(to_embed)} tags...")
        texts = [desc for _, desc, _ in to_embed]
        embs = encode_texts(texts, model, batch_size, device, show_progress=False)

        for (tag_name, desc, desc_hash), emb in zip(to_embed, embs):
            db.set_tag_embedding(tag_name, desc, desc_hash, model_name, emb)
            cached_embeddings.append((tag_name, emb))
    else:
        logger.info(f"Using cached embeddings for {len(cached_embeddings)} tags")

    # Return embeddings in original tag order
    tag_order = list(tags.keys())
    emb_map = dict(cached_embeddings)
    return np.array([emb_map[tag] for tag in tag_order])


# --- Main ---

def main() -> None:
    """Main entry point for auto-tagger."""
    p = argparse.ArgumentParser()
    p.add_argument('vault_path')
    p.add_argument('--tags-file')
    p.add_argument('--apply-tags', action='store_true')
    p.add_argument('--remove-tags', action='store_true')
    p.add_argument('--batch-size', type=int, default=32)
    p.add_argument('--force-embeddings', action='store_true')
    p.add_argument('--model', default='all-MiniLM-L6-v2')
    p.add_argument('--verbose', action='store_true', help='Enable verbose logging (DEBUG level)')
    args = p.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s'
    )

    # Initialize run logger
    run_logger = RunLogger(args.vault_path, 'tagger')
    run_logger.set_parameters({
        'batch_size': args.batch_size,
        'model': args.model,
        'force_embeddings': args.force_embeddings,
        'tags_file': args.tags_file
    })
    run_logger.set_model_info(args.model)

    files = find_markdown_files(args.vault_path)
    if args.remove_tags:
        run_logger.set_operation('remove')
        removed = 0
        for f in tqdm(files, desc='Removing tags'):
            if remove_tags(f):
                removed += 1
        logger.info(f"Removed tags from {removed}/{len(files)} files.")
        run_logger.set_file_stats(total=len(files), modified=removed)
        run_logger.set_tag_stats(removed=removed)
        run_logger.complete()
        return

    if not args.tags_file:
        logger.error("Error: --tags-file required")
        return
    tags = load_tags(args.tags_file)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = SentenceTransformer(args.model, device=device)

    emb_docs, docs, stats = generate_embeddings(
        files, model, args.model, args.batch_size, device,
        args.vault_path, args.force_embeddings
    )

    # Log file embedding stats
    logger.info(
        f"File embeddings: {stats['new']} new, {stats['modified']} modified, "
        f"{stats['unchanged']} unchanged, {stats['deleted']} deleted"
    )

    # Use cached tag embeddings
    emb_tags = load_and_embed_tags(
        tags, model, args.model, args.batch_size, device,
        args.vault_path, args.force_embeddings
    )

    sims = cosine_similarity(emb_docs, emb_tags)
    best = sims.argmax(axis=1)
    mapping = {docs[i]: list(tags.keys())[idx] for i, idx in enumerate(best)}

    if args.apply_tags:
        run_logger.set_operation('apply')
        applied = 0
        for doc, tag in tqdm(mapping.items(), desc='Applying tags'):
            if add_tag(doc, tag):
                applied += 1
        logger.info(f"Applied tags to {applied}/{len(mapping)} files.")
        run_logger.set_file_stats(
            total=len(files),
            modified=applied,
            new=stats.get('new', 0),
            unchanged=stats.get('unchanged', 0),
            deleted=stats.get('deleted', 0)
        )
        run_logger.set_tag_stats(applied=applied)
        run_logger.complete()
    else:
        run_logger.set_operation('preview')
        run_logger.set_file_stats(
            total=len(files),
            new=stats.get('new', 0),
            unchanged=stats.get('unchanged', 0),
            deleted=stats.get('deleted', 0)
        )
        run_logger.complete()

if __name__ == '__main__':
    main()
