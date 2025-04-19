#!/usr/bin/env python
import os
import glob
import re
import argparse
from pathlib import Path

import torch
from tqdm import tqdm
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig
)

# --- Constants for summary markers ---
SUMMARY_START = "<!-- AUTO-GENERATED SUMMARY START -->"
SUMMARY_END   = "<!-- AUTO-GENERATED SUMMARY END -->"

def find_markdown_files(vault_path, max_files):
    """Recursively find up to `max_files` .md files under vault_path."""
    all_md = glob.glob(os.path.join(vault_path, '**', '*.md'), recursive=True)
    return [Path(p) for p in all_md[:max_files]]

def remove_summaries(filepath):
    """Strip out any existing summary block from the top of the file."""
    txt = filepath.read_text(encoding='utf-8')
    pattern = re.compile(
        rf"{re.escape(SUMMARY_START)}.*?{re.escape(SUMMARY_END)}\n*",
        re.DOTALL
    )
    new_txt, count = pattern.subn('', txt)
    if count:
        filepath.write_text(new_txt, encoding='utf-8')
    return count > 0

def insert_summary(filepath, summary):
    """Prepend the generated summary block above the rest of the file."""
    txt = filepath.read_text(encoding='utf-8')
    block = f"{SUMMARY_START}\n{summary.strip()}\n{SUMMARY_END}\n\n"
    filepath.write_text(block + txt, encoding='utf-8')

def init_summarizer(model_dir):
    """Load tokenizer + 4‑bit quantized Mistral from a local HF folder."""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Loading model on {device}…")
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    bnb_cfg = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16)
    from transformers import BitsAndBytesConfig  # add at top of file if not already

  
    tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=True)

    # new NF4‐quantized 4‑bit setup:
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",            # switch to NF4 quant
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_dir,
        quantization_config=quant_config,
        device_map="auto",
        trust_remote_code=True,
    )
    # force initialization of the 4‑bit layers on GPU
    model = model.to(device)

    return tokenizer, model


def summarize_text(tokenizer, model, text, max_length):
    """Generate a summary of `text` up to `max_length` new tokens."""
    inputs = tokenizer(
        text,
        return_tensors='pt',
        truncation=True,
        max_length=2048
    ).to(model.device)
    out = model.generate(
        **inputs,
        max_new_tokens=max_length,
        do_sample=False
    )
    # strip off the prompt tokens
    summary = tokenizer.decode(
        out[0][ inputs['input_ids'].shape[-1]: ],
        skip_special_tokens=True
    )
    return summary

def main():
    p = argparse.ArgumentParser(
        description="Batch‑summarise Markdown chats with a local Mistral‑7B model"
    )
    p.add_argument("vault_path", help="Path to your Obsidian vault")
    p.add_argument(
        "--model-dir", required=True,
        help="Local HF model folder (with config.json, pytorch_model.bin, etc.)"
    )
    p.add_argument(
        "--max-summary-length", type=int, default=128,
        help="Max tokens for each summary"
    )
    p.add_argument(
        "--max-files", type=int, default=20,
        help="How many .md files to process in one run"
    )
    p.add_argument(
        "--delete-summaries", action="store_true",
        help="First strip existing summaries before (re‑)applying"
    )
    p.add_argument(
        "--apply-summaries", action="store_true",
        help="Actually insert newly generated summaries"
    )

    args = p.parse_args()

    # Load tokenizer + model
    tokenizer, model = init_summarizer(args.model_dir)

    # Collect files
    files = find_markdown_files(args.vault_path, args.max_files)
    if not files:
        print("No markdown files found.")
        return

    # Optionally clear out old summaries
    if args.delete_summaries:
        print("Clearing old summaries…")
        for f in tqdm(files, desc="Clearing summaries"):
            remove_summaries(f)

    # Generate & insert
    if args.apply_summaries:
        print("Generating and applying summaries…")
        for f in tqdm(files, desc="Summarising"):
            text = f.read_text(encoding='utf-8')
            summary = summarize_text(
                tokenizer, model,
                text, args.max_summary_length
            )
            insert_summary(f, summary)

    print("Done.")

if __name__ == "__main__":
    main()
