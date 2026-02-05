#!/usr/bin/env python
"""Summariser for markdown vaults using Ollama local LLM.

Compatible with Obsidian, Logseq, and other markdown-based knowledge bases.
This module generates summaries for markdown files using a local Ollama instance.
Summaries are prepended to files as HTML-comment-wrapped blocks.
"""
import os
import argparse
import logging
from pathlib import Path
from typing import List, Optional
import requests
from tqdm import tqdm

from metisem.core.files import find_markdown_files as _find_all_md, compute_file_hash, extract_summary, ChangeSet
from metisem.core.markers import (
    SUMMARY_START,
    SUMMARY_END,
    has_marker_block,
    remove_marker_block,
    replace_marker_block
)
from metisem.core.run_logger import RunLogger
from metisem.core.database import CacheDatabase
import hashlib

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'localhost:11434')

def find_markdown_files(vault_path: str, max_files: Optional[int]) -> List[Path]:
    """Find markdown files in vault, optionally limited to max_files."""
    files = _find_all_md(vault_path)
    if max_files:
        logger.info(f"Limiting to {max_files} files out of {len(files)} total files found")
        return files[:max_files]
    return files

def remove_summaries(filepath: Path) -> bool:
    """Strip out any existing summary block from the file."""
    try:
        txt = filepath.read_text(encoding='utf-8')
        if has_marker_block(txt, SUMMARY_START, SUMMARY_END):
            new_txt = remove_marker_block(txt, SUMMARY_START, SUMMARY_END)
            filepath.write_text(new_txt, encoding='utf-8')
            return True
        return False
    except Exception as e:
        logger.error(f"Error removing summaries from {filepath}: {e}")
        return False

def insert_summary(filepath: Path, summary: str) -> None:
    """Insert or replace the summary block at the top of the file."""
    try:
        txt = filepath.read_text(encoding='utf-8')
        summary_content = summary.strip()

        if has_marker_block(txt, SUMMARY_START, SUMMARY_END):
            # Replace existing summary to prevent duplicates
            new_txt = replace_marker_block(txt, SUMMARY_START, SUMMARY_END, summary_content)
            filepath.write_text(new_txt, encoding='utf-8')
        else:
            # No existing summary - prepend new block
            block = f"{SUMMARY_START}\n{summary_content}\n{SUMMARY_END}\n\n"
            filepath.write_text(block + txt, encoding='utf-8')

        # Verify summary was written
        final_txt = filepath.read_text(encoding='utf-8')
        if not has_marker_block(final_txt, SUMMARY_START, SUMMARY_END):
            logger.warning(f"Warning: Summary may not have been written to {filepath}")
    except Exception as e:
        logger.error(f"Error inserting summary into {filepath}: {e}")

def summarise_text(text: str, model_name: str, max_length: int) -> str:
    """Generate a summary using Ollama's API."""
    try:
        # Truncate input text if too long (approximate token count)
        # Increased from 2048 to 6144 to allow for longer context
        words = text.split()
        max_words = 6144  # approximately 6K tokens
        if len(words) > max_words:
            logger.warning(f"Input text truncated to ~{max_words} tokens.")
            text = ' '.join(words[:max_words])

        # Enhanced prompt for better summaries
        prompt = (
            "Act as an expert summariser. Analyse the following conversation and create "
            "a comprehensive summary that:\n"
            "1. Identifies the core discussion topics and their interconnections\n"
            "2. Captures key questions raised and significant responses\n"
            "3. Notes any philosophical or technical concepts discussed\n"
            "4. Preserves important examples and analogies used\n\n"
            "Guidelines:\n"
            "- Focus on the substantive content rather than conversation mechanics\n"
            "- Maintain objectivity and balance when presenting different viewpoints\n"
            "- Include specific examples and references mentioned\n"
            "- Connect related ideas across the discussion\n"
            "- Keep technical accuracy while remaining accessible\n\n"
            "Text to summarise:\n"
            f"{text}\n\n"
            "Write a single-paragraph summary that flows naturally and captures the depth "
            "and nuance of the discussion:"
        )

        # Call Ollama API with adjusted parameters
        response = requests.post(
            f'http://{OLLAMA_HOST}/api/generate',
            json={
                'model': model_name,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'num_predict': max(512, max_length),  # Ensure enough tokens for complete summary
                    'stop': ['\n\n'],  # Stop on double newline
                    'temperature': 0.3,  # Lower temperature for more focused summaries
                    'top_k': 50,        # Reasonable top-k for coherent output
                    'top_p': 0.9,       # Reasonable nucleus sampling
                    'context_window': 8192  # Maximum context window
                }
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Error from Ollama API: {response.text}")
            return ""

        return response.json()['response'].strip()

    except Exception as e:
        logger.error(f"Error during summarisation: {e}")
        return ""

def detect_summary_changes(file_paths: List[Path], db: CacheDatabase) -> ChangeSet:
    """Detect which files need summaries generated.

    Categorizes files into:
    - new_files: Files not in database
    - modified_files: Files with changed content_hash
    - needs_summary: Files in database without has_summary flag (treated as new for summary purposes)
    - unchanged_files: Files with valid cached summaries

    Args:
        file_paths: List of markdown files to check
        db: CacheDatabase instance

    Returns:
        ChangeSet with categorized file lists
    """
    new_files = []
    modified_files = []
    needs_summary = []
    unchanged_files = []

    for path in file_paths:
        cached = db.get_file_metadata(path)

        if not cached:
            # Not in database -> new file
            new_files.append(path)
        else:
            # Compute current content hash
            current_hash = compute_file_hash(path)
            if not current_hash:
                # Can't read file -> treat as modified to attempt processing
                modified_files.append(path)
                continue

            if current_hash != cached.get('content_hash'):
                # Content changed -> needs regeneration
                modified_files.append(path)
            elif not cached.get('has_summary'):
                # Content unchanged but no summary flag -> needs summary
                needs_summary.append(path)
            else:
                # Content unchanged and has summary -> skip
                unchanged_files.append(path)

    return ChangeSet(
        new_files=new_files,
        modified_files=modified_files,
        deleted_files=needs_summary,  # Reusing deleted_files slot for needs_summary
        unchanged_files=unchanged_files
    )

def main() -> None:
    p = argparse.ArgumentParser(description="Batch-summarise Markdown files using Ollama")
    p.add_argument("vault_path", help="Obsidian vault path")
    p.add_argument("--model", default="mistral", help="Ollama model name (default: mistral)")
    p.add_argument("--max-summary-length", type=int, default=128, help="Max tokens per summary")
    p.add_argument("--max-files", type=int, default=None, help="Max files to process (default: all files)")
    p.add_argument("--delete-summaries", action="store_true", help="Remove existing summaries")
    p.add_argument("--apply-summaries", action="store_true", help="Insert new summaries")
    p.add_argument("--force-summaries", action="store_true", help="Regenerate summaries even for unchanged files")
    p.add_argument("--verbose", action="store_true", help="Enable verbose logging (DEBUG level)")
    args = p.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s'
    )

    # Verify Ollama is running
    try:
        requests.get(f'http://{OLLAMA_HOST}/api/version')
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to Ollama at {OLLAMA_HOST}. Is it running?")
        logger.error("Start Ollama with: ollama serve")
        return

    files = find_markdown_files(args.vault_path, args.max_files)
    if not files:
        logger.error("No Markdown files found. Ensure the vault path is correct and contains .md files.")
        return

    total_files = len(files)
    logger.info(f"Found {total_files} markdown files in {args.vault_path}")

    # Initialize cache database
    vault_path = Path(args.vault_path)
    cache_db = CacheDatabase(vault_path / '.metisem' / 'metisem.db')
    cache_db.migrate_summary_schema()  # Idempotent migration

    # Determine which files need processing
    if args.apply_summaries and not args.force_summaries:
        changes = detect_summary_changes(files, cache_db)
        files_to_process = changes.new_files + changes.modified_files + changes.deleted_files  # deleted_files = needs_summary
        files_with_summary = changes.unchanged_files
        logger.info(f"Cache: {len(files_with_summary)} files with summaries, {len(files_to_process)} need processing")
        logger.debug(f"  New: {len(changes.new_files)}, Modified: {len(changes.modified_files)}, Needs summary: {len(changes.deleted_files)}")
    else:
        files_to_process = files
        files_with_summary = []

    # Initialize run logger
    run_logger = RunLogger(args.vault_path, 'summariser')
    run_logger.set_parameters({
        'model': args.model,
        'max_summary_length': args.max_summary_length,
        'max_files': args.max_files,
        'ollama_host': OLLAMA_HOST
    })
    run_logger.set_model_info(args.model)

    if args.delete_summaries:
        run_logger.set_operation('delete')
        logger.info("Removing old summaries...")
        removed = 0
        for f in tqdm(files, desc="Clearing"):
            if remove_summaries(f):
                removed += 1
        logger.info(f"Removed summaries from {removed} files")
        if not args.apply_summaries:
            run_logger.set_file_stats(total=total_files, modified=removed)
            run_logger.set_summary_stats(removed=removed)
            run_logger.complete()
            return

    if args.apply_summaries:
        run_logger.set_operation('apply')
        logger.info("Generating and applying summaries...")
        successful = 0
        errors = 0
        for f in tqdm(files_to_process, desc="Summarising"):
            try:
                logger.debug(f"Processing: {f}")
                text = f.read_text(encoding='utf-8')
                if len(text.strip()) == 0:
                    logger.debug(f"Skipping empty file: {f}")
                    continue

                summary = summarise_text(text, args.model, args.max_summary_length)
                if summary:
                    insert_summary(f, summary)

                    # Update cache database
                    content_hash = compute_file_hash(f)
                    if content_hash:
                        summary_hash = hashlib.sha256(summary.encode('utf-8')).hexdigest()
                        cache_db.set_summary_metadata(f, content_hash, summary_hash, summary)

                    successful += 1
                    logger.debug(f"Added summary to: {f}")
                    logger.debug(f"Summary: {summary[:100]}...")
            except Exception as e:
                logger.error(f"Error processing {f}: {e}")
                errors += 1
                run_logger.add_error(f"Error processing {f.name}: {str(e)}")

        # Calculate metrics including cache hits
        total_vault_files = len(files_to_process) + len(files_with_summary)
        cache_hit_ratio = len(files_with_summary) / total_vault_files if total_vault_files > 0 else 0.0

        logger.info(f"\nSummary Generation Complete:")
        logger.info(f"- Successfully processed: {successful}/{len(files_to_process)} files")
        logger.info(f"- Cache hits: {len(files_with_summary)} files")
        logger.info(f"- Failed/Skipped: {len(files_to_process) - successful} files")
        if cache_hit_ratio > 0:
            logger.info(f"- Cache hit ratio: {cache_hit_ratio:.1%}")

        # Log metrics
        run_logger.set_file_stats(
            total=total_vault_files,
            modified=successful,
            unchanged=len(files_with_summary)
        )
        run_logger.set_summary_stats(added=successful)

        # Set cache hit ratio in run logger
        if hasattr(run_logger, '_run_data'):
            run_logger._run_data['cache_hit_ratio'] = cache_hit_ratio

        if errors > 0:
            run_logger.complete(status='partial' if successful > 0 else 'error')
        else:
            run_logger.complete()

        cache_db.close()

if __name__ == '__main__':
    main()