#!/usr/bin/env python
"""Title fixer for markdown vaults with generic filenames.

Compatible with Obsidian, Logseq, and other markdown-based knowledge bases.
This module renames files with generic titles (e.g., "New Chat", "Untitled")
using descriptive titles extracted from their summary blocks.
"""
import argparse
import logging
import os
import re
from pathlib import Path
from typing import List, Tuple, Optional

import requests

from metisem.core.files import find_markdown_files, extract_summary, generate_title_from_summary
from metisem.core.run_logger import RunLogger

logger = logging.getLogger(__name__)

DEFAULT_TITLE_PATTERN = r'^(New Chat|Untitled)( \(\d+\)| \d+)?$'
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'localhost:11434')


def is_generic_title(filename: str, pattern: str) -> bool:
    """Check if filename matches generic title pattern.

    Args:
        filename: Filename stem (without extension)
        pattern: Regex pattern for generic titles

    Returns:
        True if filename matches pattern
    """
    return bool(re.match(pattern, filename, re.IGNORECASE))


def find_files_with_generic_titles(
    vault_path: str,
    pattern: str = DEFAULT_TITLE_PATTERN
) -> List[Path]:
    """Find markdown files with generic titles.

    Args:
        vault_path: Path to the vault
        pattern: Regex pattern for generic titles

    Returns:
        List of file paths with generic titles
    """
    all_files = find_markdown_files(vault_path)
    generic = [f for f in all_files if is_generic_title(f.stem, pattern)]
    return generic


def generate_title_with_llm(summary: str, model_name: str, max_length: int) -> Optional[str]:
    """Generate a concise title using Ollama LLM.

    Args:
        summary: Summary text to generate title from
        model_name: Ollama model name
        max_length: Maximum title length

    Returns:
        Generated title or None if failed
    """
    try:
        # Truncate summary to first 200 words for speed
        words = summary.split()
        if len(words) > 200:
            summary = ' '.join(words[:200])

        prompt = (
            f"Create a short title (max {max_length} chars) for this summary:\n\n"
            f"{summary}\n\n"
            f"Title:"
        )

        response = requests.post(
            f'http://{OLLAMA_HOST}/api/generate',
            json={
                'model': model_name,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.3,
                    'num_predict': 20,
                    'top_p': 0.9
                }
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            title = result.get('response', '').strip()

            # Sanitize filename
            title = re.sub(r'[<>:"/\\|?*]', '', title)
            title = re.sub(r'\s+', ' ', title).strip()

            # Remove quotes if present
            title = title.strip('"\'')

            # Truncate at word boundary if needed
            if len(title) > max_length:
                title = title[:max_length].rsplit(' ', 1)[0]

            return title if title else None
        else:
            logger.error(f"Ollama API error: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Error generating LLM title: {e}")
        return None


def generate_rename_proposals(
    files: List[Path],
    max_length: int = 60,
    use_llm: bool = False,
    model_name: str = 'mistral'
) -> List[Tuple[Path, Optional[str]]]:
    """Generate rename proposals for files with generic titles.

    Args:
        files: List of files to process
        max_length: Maximum length for generated titles
        use_llm: Use LLM for title generation instead of heuristic
        model_name: Ollama model name if use_llm is True

    Returns:
        List of tuples (original_path, proposed_title)
        proposed_title is None if no valid title could be generated
    """
    proposals = []

    for file_path in files:
        try:
            content = file_path.read_text(encoding='utf-8')
            summary = extract_summary(content)

            if summary:
                if use_llm:
                    logger.info(f"Generating LLM title for: {file_path.name}")
                    new_title = generate_title_with_llm(summary, model_name, max_length)
                else:
                    new_title = generate_title_from_summary(summary, max_length)

                proposals.append((file_path, new_title))
            else:
                # No summary found
                logger.warning(f"No summary found for: {file_path.name}")
                proposals.append((file_path, None))

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            proposals.append((file_path, None))

    return proposals


def apply_renames(proposals: List[Tuple[Path, Optional[str]]]) -> Tuple[int, int, int]:
    """Apply rename proposals to files.

    Args:
        proposals: List of (original_path, proposed_title) tuples

    Returns:
        Tuple of (renamed_count, skipped_count, error_count)
    """
    renamed = 0
    skipped = 0
    errors = 0

    for file_path, new_title in proposals:
        if not new_title:
            logger.info(f"Skipping {file_path.name}: No valid title generated")
            skipped += 1
            continue

        # Construct new path
        new_path = file_path.parent / f"{new_title}.md"

        # Check for conflicts
        if new_path.exists():
            logger.warning(f"Skipping {file_path.name}: {new_path.name} already exists")
            skipped += 1
            continue

        try:
            file_path.rename(new_path)
            logger.info(f"Renamed: {file_path.name} → {new_path.name}")
            renamed += 1
        except Exception as e:
            logger.error(f"Error renaming {file_path.name}: {e}")
            errors += 1

    return renamed, skipped, errors


def main() -> None:
    """Main entry point for title fixer."""
    p = argparse.ArgumentParser(
        description='Fix generic titles in markdown files using summaries'
    )
    p.add_argument('vault_path', help='Path to the markdown vault')
    p.add_argument(
        '--apply-fixes',
        action='store_true',
        help='Actually rename files (default is preview mode)'
    )
    p.add_argument(
        '--title-pattern',
        type=str,
        default=DEFAULT_TITLE_PATTERN,
        help=f'Regex pattern for generic titles (default: {DEFAULT_TITLE_PATTERN})'
    )
    p.add_argument(
        '--max-length',
        type=int,
        default=60,
        help='Maximum length for generated titles (default: 60)'
    )
    p.add_argument(
        '--use-llm',
        action='store_true',
        help='Use Ollama LLM for title generation instead of heuristic extraction'
    )
    p.add_argument(
        '--model',
        type=str,
        default='mistral',
        help='Ollama model to use for title generation (default: mistral)'
    )
    p.add_argument(
        '--verbose',
        action='store_true',
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
    run_logger = RunLogger(vault, 'title_fixer')
    run_logger.set_parameters({
        'title_pattern': args.title_pattern,
        'max_length': args.max_length,
        'apply_fixes': args.apply_fixes,
        'use_llm': args.use_llm,
        'model': args.model if args.use_llm else None
    })

    # Find files with generic titles
    logger.info(f"Scanning vault for files with generic titles...")
    generic_files = find_files_with_generic_titles(vault, args.title_pattern)
    logger.info(f"Found {len(generic_files)} files with generic titles")

    if not generic_files:
        logger.info("No files to process.")
        run_logger.set_file_stats(total=0, modified=0)
        run_logger.complete()
        return

    # Generate rename proposals
    if args.use_llm:
        logger.info(f"Generating title proposals using LLM ({args.model})...")
    else:
        logger.info("Generating title proposals using heuristic extraction...")
    proposals = generate_rename_proposals(
        generic_files,
        args.max_length,
        use_llm=args.use_llm,
        model_name=args.model
    )

    # Count proposals
    valid_proposals = sum(1 for _, title in proposals if title is not None)
    logger.info(f"Generated {valid_proposals} valid title proposals")

    # Show proposals
    if not args.apply_fixes:
        run_logger.set_operation('preview')
        logger.info("\nProposed renames (preview mode):")
        for file_path, new_title in proposals:
            if new_title:
                logger.info(f"  {file_path.name} → {new_title}.md")
            else:
                logger.info(f"  {file_path.name} → [No summary or invalid title]")

        logger.info(
            f"\n{valid_proposals} files would be renamed. "
            f"Use --apply-fixes to perform renames."
        )

        run_logger.set_file_stats(
            total=len(generic_files),
            modified=0
        )
        run_logger.complete()
    else:
        # Apply renames
        run_logger.set_operation('apply')
        logger.info("\nApplying renames...")
        renamed, skipped, errors = apply_renames(proposals)

        logger.info(
            f"\nResults: {renamed} renamed, {skipped} skipped, {errors} errors"
        )

        run_logger.set_file_stats(
            total=len(generic_files),
            modified=renamed
        )

        if errors > 0:
            run_logger.add_error(f"{errors} files had errors during renaming")
            run_logger.complete(status='partial' if renamed > 0 else 'error')
        else:
            run_logger.complete()


if __name__ == '__main__':
    main()
