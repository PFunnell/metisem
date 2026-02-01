"""Auto-tagger for Obsidian markdown vaults.

This module automatically tags notes based on semantic similarity between note content
and tag descriptions. Tags are added to YAML front matter.
"""
import os
import re
import argparse
import hashlib
from pathlib import Path
import logging
from typing import List, Dict, Tuple
import yaml
import numpy as np
import torch
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# --- Constants ---
CACHE_DIR = ".obsidian_linker_cache"
YAML_SEP = '---'
TAGS_KEY = 'tags'
TAG_DESC_SEP = '::'

# --- File Utilities ---

def find_markdown_files(vault: str) -> List[Path]:
    """Find all markdown files in vault recursively."""
    return list(Path(vault).rglob('*.md'))


def read_and_hash(path: Path) -> Tuple[str, str]:
    """Read file and compute SHA256 hash. Returns (content, hash)."""
    text = path.read_text(encoding='utf-8')
    h = hashlib.sha256(text.encode('utf-8')).hexdigest()
    return text, h

# --- Caching ---

def cache_filepath(vault: str, model_name: str) -> Path:
    """Generate cache file path for embeddings based on vault and model name."""
    vault_name = Path(vault).resolve().name.replace('/', '_')
    safe_name = model_name.replace('/', '_')
    return Path(vault) / CACHE_DIR / f'embeddings_{vault_name}_{safe_name}.npz'


def load_cache(cp: Path) -> Dict[Path, Dict[str, any]]:
    """Load cached embeddings from npz file. Returns empty dict if not found."""
    if cp.exists():
        data = np.load(cp, allow_pickle=True)
        return {Path(p): {'hash': h, 'emb': e} for p, h, e in zip(data['paths'], data['hashes'], data['embs'])}
    return {}


def save_cache(cp: Path, mapping: Dict[Path, Dict[str, any]]) -> None:
    """Save embeddings to cache file in npz format."""
    cp.parent.mkdir(exist_ok=True)
    paths = np.array([str(p) for p in mapping])
    hashes = np.array([mapping[p]['hash'] for p in mapping])
    embs = np.stack([mapping[p]['emb'] for p in mapping])
    np.savez(cp, paths=paths, hashes=hashes, embs=embs)

# --- Embedding ---

def embed_texts(texts: List[str], model, batch: int, device: str) -> np.ndarray:
    """Generate embeddings for a list of texts using sentence transformer model."""
    return model.encode(texts, batch_size=batch, show_progress_bar=True, device=device, convert_to_numpy=True)


def embed_documents(files: List[Path], model, model_name: str, batch: int, device: str, vault: str, force: bool) -> Tuple[np.ndarray, List[Path]]:
    """Generate or load cached embeddings for markdown files. Returns (embeddings_array, file_paths)."""
    cp = cache_filepath(vault, model_name)
    cached = {} if force else load_cache(cp)
    to_process = []
    mapping = {}
    for p in files:
        content, h = read_and_hash(p)
        if p in cached and cached[p]['hash'] == h:
            mapping[p] = cached[p]
        else:
            to_process.append((p, content, h))
    if to_process:
        texts = [tpl[1] for tpl in to_process]
        embs = embed_texts(texts, model, batch, device)
        for (p, _, h), e in zip(to_process, embs):
            mapping[p] = {'hash': h, 'emb': e}
        save_cache(cp, mapping)
    paths = list(mapping)
    embs = np.stack([mapping[p]['emb'] for p in paths])
    return embs, paths

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

    files = find_markdown_files(args.vault_path)
    if args.remove_tags:
        removed = 0
        for f in tqdm(files, desc='Removing tags'):
            if remove_tags(f):
                removed += 1
        logger.info(f"Removed tags from {removed}/{len(files)} files.")
        return

    if not args.tags_file:
        logger.error("Error: --tags-file required")
        return
    tags = load_tags(args.tags_file)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = SentenceTransformer(args.model, device=device)

    emb_docs, docs = embed_documents(
        files, model, args.model, args.batch_size, device,
        args.vault_path, args.force_embeddings
    )
    emb_tags = embed_texts(list(tags.values()), model, args.batch_size, device)

    sims = cosine_similarity(emb_docs, emb_tags)
    best = sims.argmax(axis=1)
    mapping = {docs[i]: list(tags.keys())[idx] for i, idx in enumerate(best)}

    if args.apply_tags:
        applied = 0
        for doc, tag in tqdm(mapping.items(), desc='Applying tags'):
            if add_tag(doc, tag):
                applied += 1
        logger.info(f"Applied tags to {applied}/{len(mapping)} files.")

if __name__ == '__main__':
    main()
