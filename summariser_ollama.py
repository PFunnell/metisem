#!/usr/bin/env python
import os
import glob
import re
import argparse
from pathlib import Path
import requests
from tqdm import tqdm

SUMMARY_START = "<!-- AUTO-GENERATED SUMMARY START -->"
SUMMARY_END = "<!-- AUTO-GENERATED SUMMARY END -->"

def find_markdown_files(vault_path, max_files):
    """Find markdown files in vault, optionally limited to max_files."""
    all_md = glob.glob(os.path.join(vault_path, '**', '*.md'), recursive=True)
    files = [Path(p) for p in all_md]
    if max_files:
        print(f"Limiting to {max_files} files out of {len(files)} total files found")
        return files[:max_files]
    return files

def remove_summaries(filepath):
    """Strip out any existing summary block from the top of the file."""
    try:
        txt = filepath.read_text(encoding='utf-8')
        pattern = re.compile(
            rf"{re.escape(SUMMARY_START)}.*?{re.escape(SUMMARY_END)}\n*",
            re.DOTALL
        )
        new_txt, count = pattern.subn('', txt)
        if count:
            filepath.write_text(new_txt, encoding='utf-8')
        return count > 0
    except Exception as e:
        print(f"Error removing summaries from {filepath}: {e}")
        return False

def insert_summary(filepath, summary):
    """Prepend the generated summary block above the rest of the file."""
    try:
        txt = filepath.read_text(encoding='utf-8')
        block = f"{SUMMARY_START}\n{summary.strip()}\n{SUMMARY_END}\n\n"
        filepath.write_text(block + txt, encoding='utf-8')
        # Verify summary was written
        new_txt = filepath.read_text(encoding='utf-8')
        if SUMMARY_START not in new_txt:
            print(f"Warning: Summary may not have been written to {filepath}")
    except Exception as e:
        print(f"Error inserting summary into {filepath}: {e}")

def summarize_text(text, model_name, max_length):
    """Generate a summary using Ollama's API."""
    try:
        # Truncate input text if too long (approximate token count)
        # Increased from 2048 to 6144 to allow for longer context
        words = text.split()
        max_words = 6144  # approximately 6K tokens
        if len(words) > max_words:
            print(f"Warning: Input text truncated to ~{max_words} tokens.")
            text = ' '.join(words[:max_words])

        # Enhanced prompt for better summaries
        prompt = (
            "Act as an expert summarizer. Analyze the following conversation and create "
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
            "Text to summarize:\n"
            f"{text}\n\n"
            "Write a single-paragraph summary that flows naturally and captures the depth "
            "and nuance of the discussion:"
        )

        # Call Ollama API with adjusted parameters
        response = requests.post(
            'http://localhost:11434/api/generate',
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
            print(f"Error from Ollama API: {response.text}")
            return ""

        return response.json()['response'].strip()

    except Exception as e:
        print(f"Error during summarization: {e}")
        return ""

def main():
    p = argparse.ArgumentParser(description="Batch-summarise Markdown files using Ollama")
    p.add_argument("vault_path", help="Obsidian vault path")
    p.add_argument("--model", default="mistral", help="Ollama model name (default: mistral)")
    p.add_argument("--max-summary-length", type=int, default=128, help="Max tokens per summary")
    p.add_argument("--max-files", type=int, default=None, help="Max files to process (default: all files)")
    p.add_argument("--delete-summaries", action="store_true", help="Remove existing summaries")
    p.add_argument("--apply-summaries", action="store_true", help="Insert new summaries")
    p.add_argument("--verbose", action="store_true", help="Show detailed progress")
    args = p.parse_args()

    # Verify Ollama is running
    try:
        requests.get('http://localhost:11434/api/version')
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to Ollama. Is it running?")
        print("Start Ollama with: ollama serve")
        return

    files = find_markdown_files(args.vault_path, args.max_files)
    if not files:
        print("No Markdown files found. Ensure the vault path is correct and contains .md files.")
        return

    total_files = len(files)
    print(f"Found {total_files} markdown files in {args.vault_path}")

    if args.delete_summaries:
        print("Removing old summaries...")
        removed = 0
        for f in tqdm(files, desc="Clearing"):
            if remove_summaries(f):
                removed += 1
        print(f"Removed summaries from {removed} files")
        if not args.apply_summaries:
            return

    if args.apply_summaries:
        print("Generating and applying summaries...")
        successful = 0
        for f in tqdm(files, desc="Summarising"):
            try:
                if args.verbose:
                    print(f"\nProcessing: {f}")
                text = f.read_text(encoding='utf-8')
                if len(text.strip()) == 0:
                    if args.verbose:
                        print(f"Skipping empty file: {f}")
                    continue
                
                summary = summarize_text(text, args.model, args.max_summary_length)
                if summary:
                    insert_summary(f, summary)
                    successful += 1
                    if args.verbose:
                        print(f"Added summary to: {f}")
                        print(f"Summary: {summary[:100]}...")
            except Exception as e:
                print(f"Error processing {f}: {e}")

        print(f"\nSummary Generation Complete:")
        print(f"- Successfully processed: {successful}/{total_files} files")
        print(f"- Failed/Skipped: {total_files - successful} files")

if __name__ == '__main__':
    main()