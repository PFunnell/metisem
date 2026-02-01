"""Semantic link generator for Obsidian markdown vaults.

This module generates semantic links between markdown files based on content similarity
using sentence transformers and cosine similarity. Links are added to files as a
'Related Notes' section with Obsidian wikilink format.
"""
import os
import glob
import argparse
import re
from pathlib import Path
import hashlib
import logging
from typing import List, Dict, Tuple, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import torch
from tqdm import tqdm

logger = logging.getLogger(__name__)

# --- Constants ---
LINK_SECTION_START = "<!-- AUTO-GENERATED LINKS START -->"
LINK_SECTION_END = "<!-- AUTO-GENERATED LINKS END -->"
EMBEDDING_CACHE_DIR = ".obsidian_linker_cache"

# Return codes for modify_markdown_file
MODIFY_ERROR = -1
MODIFY_DELETED = -2

# --- Helper Functions ---

def find_markdown_files(vault_path: str) -> List[Path]:
    """Find all markdown files in the vault directory recursively."""
    files = list(glob.glob(os.path.join(vault_path, '**', '*.md'), recursive=True))
    return [Path(f) for f in files]


def read_file_text_and_hash(path: Path) -> Tuple[Optional[str], Optional[str]]:
    """Read file content and compute SHA256 hash. Returns (content, hash) or (None, None) on error."""
    try:
        content = path.read_text(encoding='utf-8')
        hasher = hashlib.sha256()
        hasher.update(content.encode('utf-8'))
        return content, hasher.hexdigest()
    except Exception:
        return None, None


def load_embeddings_from_cache(cache_path: str) -> Dict[Path, Dict[str, any]]:
    """Load cached embeddings from disk. Returns empty dict if cache doesn't exist or is corrupted."""
    try:
        data = np.load(cache_path, allow_pickle=True)
        if data.dtype.names:
            return {Path(item['path']): {'hash': item['hash'], 'embedding': item['embedding']} for item in data}
    except Exception as e:
        # Cache file doesn't exist or is corrupted - will regenerate
        pass
    return {}


def save_embeddings_to_cache(cache_path: str, embeddings_data: Dict[Path, Dict[str, any]]) -> None:
    """Save embeddings to cache file in numpy format."""
    if not embeddings_data:
        return
    str_keys = [str(p) for p in embeddings_data]
    max_path = max(len(p) for p in str_keys)
    dim = len(next(iter(embeddings_data.values()))['embedding'])
    dtype = [('path', f'U{max_path}'), ('hash', 'U64'), ('embedding', f'{dim}f4')]
    arr = np.array([(str(p), data['hash'], data['embedding']) for p, data in embeddings_data.items()], dtype=dtype)
    d = os.path.dirname(cache_path)
    if d:
        os.makedirs(d, exist_ok=True)
    np.save(cache_path, arr, allow_pickle=False)


def generate_embeddings(file_paths: List[Path], model, model_name: str, batch_size: int, device: str, cache_dir: str, force: bool) -> Tuple[np.ndarray, List[Path]]:
    """Generate embeddings for files using sentence transformer model. Uses cache unless force=True."""
    if not file_paths:
        return np.array([]), []
    vault = os.path.commonpath(file_paths)
    safe = os.path.basename(vault).replace('/', '_')
    cache_file = f"embeddings_{safe}_{model_name.replace('/', '_')}.npy"
    cache = os.path.join(cache_dir, cache_file)
    cached = {} if force else load_embeddings_from_cache(cache)
    to_embed = []
    map_hash = {}
    embeddings_map = {}
    for p in file_paths:
        content, h = read_file_text_and_hash(p)
        if not h:
            continue
        map_hash[p] = h
        if p in cached and cached[p]['hash'] == h:
            embeddings_map[p] = cached[p]
        else:
            to_embed.append((p, content))
    if to_embed:
        texts = [c for _, c in to_embed]
        embs = model.encode(texts, batch_size=batch_size, show_progress_bar=True, device=device, convert_to_numpy=True)
        for (p, _), e in zip(to_embed, embs):
            embeddings_map[p] = {'hash': map_hash[p], 'embedding': e}
    save_embeddings_to_cache(cache, embeddings_map)
    final_emb = []
    valid = []
    for p in file_paths:
        if p in embeddings_map:
            final_emb.append(embeddings_map[p]['embedding'])
            valid.append(p)
    return np.array(final_emb), valid


def calculate_similarity(embeddings: np.ndarray) -> np.ndarray:
    """Calculate cosine similarity matrix between embeddings. Diagonal set to 0."""
    emb = embeddings.astype(np.float32)
    norm = np.linalg.norm(emb, axis=1, keepdims=True)
    sim = cosine_similarity(emb / norm, emb / norm)
    np.fill_diagonal(sim, 0)
    return sim


def find_links(similarity_matrix: np.ndarray, paths: List[Path], threshold: float, min_links: int, max_links: int, cluster_labels: Optional[np.ndarray] = None) -> Dict[Path, List[Path]]:
    """Find related files based on similarity scores. Respects cluster boundaries if labels provided."""
    links = {}
    for i, src in enumerate(paths):
        sims = similarity_matrix[i]
        inds = np.argsort(-sims)
        picked = []
        # first, pick those above threshold
        for j in inds:
            if j == i:
                continue
            if sims[j] < threshold:
                break
            if cluster_labels is not None and cluster_labels[i] != cluster_labels[j]:
                continue
            if len(picked) < max_links:
                picked.append(paths[j])
        # fallback to meet min_links by including below-threshold
        if len(picked) < min_links:
            for j in inds:
                if j == i:
                    continue
                if cluster_labels is not None and cluster_labels[i] != cluster_labels[j]:
                    continue
                if sims[j] >= threshold:
                    continue
                if len(picked) < min_links and len(picked) < max_links:
                    picked.append(paths[j])
                else:
                    break
        links[src] = picked if len(picked) >= min_links else []
    return links


def modify_markdown_file(fp: Path, links: List[Path], delete_existing: bool) -> int:
    """Add or update Related Notes section in markdown file. Returns count of links added, or error code."""
    try:
        text = fp.read_text(encoding='utf-8')
        start = re.escape(LINK_SECTION_START)
        end = re.escape(LINK_SECTION_END)
        pattern = re.compile(
            rf"^[ \t]*{start}[ \t]*$.*?^[ \t]*{end}[ \t]*$\n?",
            flags=re.MULTILINE|re.DOTALL
        )
        has_block = bool(pattern.search(text))
        if delete_existing and not links:
            if has_block:
                new = pattern.sub('', text)
                fp.write_text(new, encoding='utf-8')
                return MODIFY_DELETED
            return 0
        if delete_existing and has_block:
            text = pattern.sub('', text)
        if not links:
            return 0
        items = sorted({f"[[{p.stem}]]" for p in links})
        block = (
            f"\n{LINK_SECTION_START}\n"
            "## Related Notes\n"
            + "\n".join(items)
            + f"\n{LINK_SECTION_END}\n"
        )
        if has_block:
            new = pattern.sub(block, text)
        else:
            new = text.rstrip() + block
        fp.write_text(new, encoding='utf-8')
        return len(items)
    except Exception as e:
        # File read/write error
        return MODIFY_ERROR


def main() -> None:
    """Main entry point for semantic link generator."""
    p = argparse.ArgumentParser()
    p.add_argument('vault_path')
    p.add_argument(
        '--clusters', type=int, default=0,
        help='Number of clusters to enforce intra-cluster links'
    )
    p.add_argument(
        '--similarity', type=float, default=0.6,
        help='Minimum weighted similarity threshold for linking'
    )
    p.add_argument(
        '--min-links', type=int, default=0,
        help='Minimum number of links to force (fallback); 0 for strict threshold'
    )
    p.add_argument(
        '--max-links', type=int, default=9,
        help='Maximum number of links to add per file'
    )
    p.add_argument(
        '--batch-size', type=int, default=32,
        help='Batch size for embedding generation'
    )
    p.add_argument(
        '--delete-links', action='store_true',
        help='Delete existing link sections before adding new ones'
    )
    p.add_argument(
        '--apply-links', action='store_true',
        help='Actually modify markdown files to insert/update links'
    )
    p.add_argument(
        '--force-embeddings', action='store_true',
        help='Force regeneration of embeddings, ignoring cache'
    )
    p.add_argument(
        '--model', type=str, default='all-MiniLM-L6-v2',
        help='Sentence Transformer model name'
    )
    p.add_argument(
        '--verbose', action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )
    args = p.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s'
    )

    vault = args.vault_path
    # deletion-only mode
    if args.delete_links and not args.apply_links and not args.force_embeddings:
        files = find_markdown_files(vault)
        removed = 0
        for f in files:
            r = modify_markdown_file(f, [], True)
            if r == MODIFY_DELETED:
                removed += 1
        logger.info(f"Removed link blocks from {removed}/{len(files)} files.")
        return

    files = find_markdown_files(vault)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = SentenceTransformer(args.model, device=device)
    emb, valid = generate_embeddings(
        files,
        model,
        args.model,
        args.batch_size,
        device,
        os.path.join(vault, EMBEDDING_CACHE_DIR),
        args.force_embeddings
    )
    if args.clusters and len(valid) >= args.clusters:
        km = KMeans(n_clusters=args.clusters, random_state=0).fit(emb)
        labels = km.labels_
    else:
        labels = None
    sim = calculate_similarity(emb)
    total_pairs = sim.size
    above = np.sum(sim >= args.similarity)
    logger.info(f"Threshold={args.similarity}: {above}/{total_pairs} pairs ({above/total_pairs:.2%}) above threshold")

    links = find_links(
        sim,
        valid,
        args.similarity,
        args.min_links,
        args.max_links,
        labels
    )

    dist = {}
    for src, tgt in links.items():
        count = len(tgt)
        dist[count] = dist.get(count, 0) + 1
    logger.info("Link count distribution:")
    for count in range(args.min_links, args.max_links+1):
        num = dist.get(count, 0)
        logger.info(f"  {num} files with {count} links")
    zero = dist.get(0, 0)
    if zero:
        logger.info(f"  {zero} files with 0 links (none above threshold and no fallback configured)")

    total_added = 0
    modified = 0
    errors = 0
    for f in files:
        to_add = links.get(Path(f), [])
        r = modify_markdown_file(Path(f), to_add, args.delete_links)
        if r > 0:
            total_added += r
            modified += 1
        elif r == MODIFY_ERROR:
            errors += 1
    logger.info(
        f"Files modified: {modified}, "
        f"total links added: {total_added}, errors: {errors}"
    )

if __name__ == '__main__':
    main()
