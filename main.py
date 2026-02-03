"""Semantic link generator for markdown vaults.

Compatible with Obsidian, Logseq, and other markdown-based knowledge bases.
This module generates semantic links between markdown files based on content similarity
using sentence transformers and cosine similarity. Links are added to files as a
'Related Notes' section with wikilink format.
"""
import argparse
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import torch

from metisem.core.files import find_markdown_files
from metisem.core.cache import generate_embeddings
from metisem.core.markers import (
    LINK_SECTION_START,
    LINK_SECTION_END,
    has_marker_block,
    remove_marker_block,
    replace_marker_block,
    append_marker_block,
    get_marker_pattern
)
from metisem.core.run_logger import RunLogger

logger = logging.getLogger(__name__)

# Return codes for modify_markdown_file
MODIFY_ERROR = -1
MODIFY_DELETED = -2

# --- Helper Functions ---


def calculate_similarity(
    embeddings: np.ndarray,
    title_embeddings: Optional[np.ndarray] = None,
    summary_embeddings: Optional[np.ndarray] = None,
    title_weight: float = 0.0,
    content_weight: float = 1.0,
    summary_weight: float = 0.0
) -> np.ndarray:
    """Calculate weighted combined similarity matrix from multiple sources.

    Args:
        embeddings: Content embeddings (always required)
        title_embeddings: Optional title embeddings
        summary_embeddings: Optional summary embeddings
        title_weight: Weight for title similarity
        content_weight: Weight for content similarity
        summary_weight: Weight for summary similarity

    Returns:
        Combined similarity matrix with diagonal set to 0
    """
    # Normalise weights
    total = title_weight + content_weight + summary_weight
    if total == 0:
        total = 1.0
        content_weight = 1.0

    combined = np.zeros((len(embeddings), len(embeddings)), dtype=np.float32)

    if content_weight > 0:
        emb = embeddings.astype(np.float32)
        norm = np.linalg.norm(emb, axis=1, keepdims=True)
        norm = np.where(norm == 0, 1, norm)  # Avoid division by zero
        content_sim = cosine_similarity(emb / norm, emb / norm)
        combined += (content_weight / total) * content_sim

    if title_weight > 0 and title_embeddings is not None:
        emb = title_embeddings.astype(np.float32)
        norm = np.linalg.norm(emb, axis=1, keepdims=True)
        norm = np.where(norm == 0, 1, norm)
        title_sim = cosine_similarity(emb / norm, emb / norm)
        combined += (title_weight / total) * title_sim

    if summary_weight > 0 and summary_embeddings is not None:
        emb = summary_embeddings.astype(np.float32)
        norm = np.linalg.norm(emb, axis=1, keepdims=True)
        norm = np.where(norm == 0, 1, norm)
        summary_sim = cosine_similarity(emb / norm, emb / norm)
        combined += (summary_weight / total) * summary_sim

    np.fill_diagonal(combined, 0)
    return combined


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
        has_block = has_marker_block(text, LINK_SECTION_START, LINK_SECTION_END)

        if delete_existing and not links:
            if has_block:
                new = remove_marker_block(text, LINK_SECTION_START, LINK_SECTION_END)
                fp.write_text(new, encoding='utf-8')
                return MODIFY_DELETED
            return 0

        if delete_existing and has_block:
            text = remove_marker_block(text, LINK_SECTION_START, LINK_SECTION_END)

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
            new = replace_marker_block(text, LINK_SECTION_START, LINK_SECTION_END, block)
        else:
            new = append_marker_block(text, block)

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
        '--min-links', type=int, default=1,
        help='Minimum number of links per file (fallback if threshold not met); 0 for strict threshold only'
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

    # Initialize run logger
    run_logger = RunLogger(vault, 'linker')
    run_logger.set_parameters({
        'similarity': args.similarity,
        'min_links': args.min_links,
        'max_links': args.max_links,
        'batch_size': args.batch_size,
        'model': args.model,
        'clusters': args.clusters,
        'force_embeddings': args.force_embeddings
    })
    run_logger.set_model_info(args.model)

    # deletion-only mode
    if args.delete_links and not args.apply_links and not args.force_embeddings:
        run_logger.set_operation('delete')
        files = find_markdown_files(vault)
        removed = 0
        for f in files:
            r = modify_markdown_file(f, [], True)
            if r == MODIFY_DELETED:
                removed += 1
        logger.info(f"Removed link blocks from {removed}/{len(files)} files.")
        run_logger.set_file_stats(total=len(files), modified=removed)
        run_logger.set_link_stats(removed=removed)
        run_logger.complete()
        return

    files = find_markdown_files(vault)
    logger.info(f"Scanning {len(files)} markdown files...")

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = SentenceTransformer(args.model, device=device)
    emb, valid, stats = generate_embeddings(
        files,
        model,
        args.model,
        args.batch_size,
        device,
        vault,
        args.force_embeddings
    )

    # Log change summary
    if not args.force_embeddings:
        logger.info(
            f"Change detection: {stats['new']} new, {stats['modified']} modified, "
            f"{stats['deleted']} deleted, {stats['unchanged']} unchanged"
        )
    if args.clusters and len(valid) >= args.clusters:
        km = KMeans(n_clusters=args.clusters, random_state=0).fit(emb)
        labels = km.labels_
    else:
        labels = None

    logger.info(f"Computing similarity matrix ({len(valid)} files)...")
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

    if args.apply_links or args.delete_links:
        # Actually modify files
        run_logger.set_operation('apply' if args.apply_links else 'delete')
        for f in files:
            to_add = links.get(f, [])
            r = modify_markdown_file(f, to_add, args.delete_links)
            if r > 0:
                total_added += r
                modified += 1
            elif r == MODIFY_ERROR:
                errors += 1
        logger.info(
            f"Files modified: {modified}, "
            f"total links added: {total_added}, errors: {errors}"
        )
    else:
        # Preview mode: report what would be done without modifying files
        run_logger.set_operation('preview')
        for f in files:
            to_add = links.get(f, [])
            if to_add:
                total_added += len(to_add)
                modified += 1
        logger.info(
            f"Preview: {modified} files would be modified, "
            f"{total_added} links would be added. Use --apply-links to modify files."
        )

    # Log run metrics
    run_logger.set_file_stats(
        total=len(files),
        modified=modified,
        new=stats.get('new', 0),
        unchanged=stats.get('unchanged', 0),
        deleted=stats.get('deleted', 0)
    )
    run_logger.set_link_stats(added=total_added)
    if errors > 0:
        run_logger.add_error(f"{errors} files had errors during processing")
        run_logger.complete(status='partial' if modified > 0 else 'error')
    else:
        run_logger.complete()

if __name__ == '__main__':
    main()
