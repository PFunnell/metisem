import os
import glob
import argparse
import re
from pathlib import Path
import hashlib

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import torch
from tqdm import tqdm

# --- Constants ---
LINK_SECTION_START = "<!-- AUTO-GENERATED LINKS START -->"
LINK_SECTION_END = "<!-- AUTO-GENERATED LINKS END -->"
EMBEDDING_CACHE_DIR = ".obsidian_linker_cache" # Store cache in a hidden dir

# --- Helper Functions ---

def find_markdown_files(vault_path):
    """Recursively finds all markdown files in the vault path."""
    print(f"Searching for Markdown files in: {vault_path}")
    files = list(glob.glob(os.path.join(vault_path, '**', '*.md'), recursive=True))
    print(f"Found {len(files)} markdown files.")
    return [Path(f) for f in files]

def read_file_content(filepath):
    """Reads content and extracts a title (filename) from a file."""
    try:
        content = filepath.read_text(encoding='utf-8')
        title = filepath.stem # Filename without extension
        return title, content
    except Exception as e:
        print(f"Warning: Could not read file {filepath}: {e}")
        return None, None

def get_file_hash(filepath):
    """Calculates the SHA256 hash of a file's content."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"Warning: Could not calculate hash for {filepath}: {e}")
        return None

def load_embeddings_from_cache(cache_path):
    """Loads embeddings and corresponding file info from cache."""
    try:
        data = np.load(cache_path, allow_pickle=True)
        # Convert structured array back to dictionary
        # Handle potential loading issues if format changes
        if data.dtype.names:
             # Using structured array for path, hash, embedding
            cached_data = {item['path']: {'hash': item['hash'], 'embedding': item['embedding']} for item in data}
        else:
             # Older format fallback (less robust)
             cached_data = data.item() # Assumes it was saved as a dict originally
        print(f"Loaded {len(cached_data)} embeddings from cache: {cache_path}")
        return cached_data
    except FileNotFoundError:
        print("Embedding cache not found.")
        return {}
    except Exception as e:
        print(f"Warning: Could not load embedding cache from {cache_path}: {e}")
        return {}

def save_embeddings_to_cache(cache_path, embeddings_data):
    """Saves embeddings and file info to cache using a structured NumPy array."""
    try:
        # Prepare data for structured array: path (string), hash (string), embedding (object/float array)
        # Determine max path length and embedding dimension
        max_path_len = max(len(str(p)) for p in embeddings_data.keys()) if embeddings_data else 100
        embedding_dim = len(next(iter(embeddings_data.values()))['embedding']) if embeddings_data else 768 # Default fallback dim
        dtype = [('path', f'U{max_path_len}'), ('hash', 'U64'), ('embedding', f'{embedding_dim}f4')] # f4=float32

        structured_data = np.array(
            [(str(path), data['hash'], data['embedding']) for path, data in embeddings_data.items()],
            dtype=dtype
        )
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        np.save(cache_path, structured_data, allow_pickle=False) # Prefer non-pickle format
        print(f"Saved {len(embeddings_data)} embeddings to cache: {cache_path}")
    except Exception as e:
        print(f"Error: Could not save embedding cache to {cache_path}: {e}")


def generate_embeddings(file_paths, contents, model, batch_size, device, cache_dir, force_embeddings, model_name):
    """Generates embeddings for file contents, using caching."""
    vault_path = os.path.commonpath(file_paths) if file_paths else '.'
    cache_filename = f"embeddings_{Path(vault_path).name}_{model_name.replace('/', '_')}.npy"
    cache_path = os.path.join(cache_dir, cache_filename)

    cached_embeddings = {}
    if not force_embeddings:
        cached_embeddings = load_embeddings_from_cache(cache_path)

    embeddings_map = {} # path -> {hash, embedding}
    texts_to_embed = []
    paths_to_embed = []
    hashes_map = {} # path -> hash

    print("Checking file hashes for embedding cache...")
    for path in tqdm(file_paths, desc="Hashing files"):
        file_hash = get_file_hash(path)
        if file_hash:
            hashes_map[path] = file_hash
            # Check cache
            if path in cached_embeddings and cached_embeddings[path]['hash'] == file_hash:
                embeddings_map[path] = cached_embeddings[path] # Use cached embedding
            else:
                # Need to generate embedding for this file
                _, content = read_file_content(path) # Read content only if needed
                if content is not None:
                   texts_to_embed.append(content)
                   paths_to_embed.append(path)
                else:
                    print(f"Skipping {path} due to read error during embedding check.")


    print(f"{len(embeddings_map)} embeddings loaded from cache.")
    if not texts_to_embed:
        print("All embeddings up-to-date or loaded from cache.")
    else:
        print(f"Generating embeddings for {len(texts_to_embed)} files...")
        new_embeddings_list = model.encode(
            texts_to_embed,
            batch_size=batch_size,
            show_progress_bar=True,
            device=device,
            convert_to_numpy=True # Easier handling
        )

        # Add newly generated embeddings to the map
        for i, path in enumerate(paths_to_embed):
           if path in hashes_map: # Ensure hash was calculated
               embeddings_map[path] = {'hash': hashes_map[path], 'embedding': new_embeddings_list[i]}

    # Save updated cache if changes were made or forced
    if texts_to_embed or force_embeddings:
       save_embeddings_to_cache(cache_path, embeddings_map)

    # Return embeddings in the original order of file_paths
    final_embeddings = []
    valid_paths = []
    for path in file_paths:
        if path in embeddings_map:
            final_embeddings.append(embeddings_map[path]['embedding'])
            valid_paths.append(path)
        else:
            print(f"Warning: No embedding found or generated for {path}. It might have been skipped due to errors.")

    if not final_embeddings:
        print("Error: No embeddings were generated or loaded successfully.")
        return [], []

    return np.array(final_embeddings), valid_paths


def calculate_similarity(embeddings):
    """Calculates the cosine similarity matrix."""
    print("Calculating similarity matrix...")
    # Normalize embeddings for efficient cosine similarity calculation
    # Ensure embeddings are float32 for performance
    embeddings = embeddings.astype(np.float32)
    norm = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized_embeddings = embeddings / norm
    similarity_matrix = cosine_similarity(normalized_embeddings)
    # Zero out diagonal (self-similarity)
    np.fill_diagonal(similarity_matrix, 0)
    print("Similarity calculation complete.")
    return similarity_matrix

def find_links(similarity_matrix, file_paths, threshold, min_links, max_links):
    """Determines which files should link to which based on similarity."""
    print(f"Finding links with similarity >= {threshold} (min: {min_links}, max: {max_links})...")
    links = {path: [] for path in file_paths} # {source_path: [target_path1, target_path2...]}

    for i, source_path in enumerate(file_paths):
        # Get similarities for the current file
        similarities = similarity_matrix[i]

        # Find indices of files above the threshold
        candidate_indices = np.where(similarities >= threshold)[0]

        # Sort candidates by similarity score (descending)
        sorted_candidates = sorted(candidate_indices, key=lambda idx: similarities[idx], reverse=True)

        # Select top candidates within min/max limits
        selected_indices = sorted_candidates[:max_links]

        # Ensure minimum links if possible (add lower similarity items if needed)
        # This part is tricky - adding items below threshold might not be desired.
        # Let's stick to only adding items >= threshold up to max_links.
        # If fewer than min_links are found *above threshold*, we only link those.
        # The user might want *at least* min_links even if below threshold - clarifying this would be good.
        # Current interpretation: Find all >= threshold, sort, take top N up to max_links. Check if count >= min_links.
        # Alternative interpretation: Take top N up to max_links. If count < min_links, *still* add them.
        # Let's go with the first interpretation (quality over quantity).

        linked_targets = [file_paths[idx] for idx in selected_indices]

        # Optional: Enforce minimum links strictly (comment out if not desired)
        # if len(linked_targets) < min_links:
        #    print(f"Note: Found only {len(linked_targets)} links >= {threshold} for {source_path.name} (min requested: {min_links}). Adding only those found.")
        #    pass # Or potentially add the next best even if below threshold - needs clarification

        links[source_path] = linked_targets

    print("Link determination complete.")
    return links


# filepath: d:\dev\obsidian-linker\main.py
def modify_markdown_file(filepath, links_to_add, delete_existing):
    """Adds or updates a list of wikilinks in a specified section of a markdown file."""
    try:
        content = filepath.read_text(encoding='utf-8')
        filename = filepath.stem
        relative_links = []
        for target_path in links_to_add:
            # Create relative paths if possible, otherwise just filename
            try:
                relative_path = os.path.relpath(target_path, filepath.parent)
                # Obsidian prefers links without the .md extension
                link_target = Path(relative_path).stem
                relative_links.append(f"[[{link_target}]]")
            except ValueError:  # Happens if paths are on different drives on Windows
                relative_links.append(f"[[{target_path.stem}]]")

        link_block = f"\n{LINK_SECTION_START}\n## Related Notes\n"
        link_block += "\n".join(sorted(list(set(relative_links))))  # Sort and ensure unique
        link_block += f"\n{LINK_SECTION_END}\n"

        # Use regex to find existing block, accounting for potential whitespace variations
        pattern = re.compile(
            rf"{re.escape(LINK_SECTION_START)}.*?{re.escape(LINK_SECTION_END)}",
            re.DOTALL,
        )
        existing_block_match = pattern.search(content)

        if delete_existing and existing_block_match:
            # Remove existing block completely before adding the new one
            content = pattern.sub("", content)
            print(f"Removed existing link block from {filepath.name}")

        if not links_to_add:
            # If no links to add and we deleted the block, we're done.
            if delete_existing and existing_block_match:
                filepath.write_text(content, encoding='utf-8')
                print(f"Removed link block (no new links) in {filepath.name}")
            else:
                print(f"No links to add or modify for {filepath.name}")
            return 0  # No links added

        if existing_block_match:
            # Replace existing block
            new_content = pattern.sub(link_block, content)
            if new_content != content:
                filepath.write_text(new_content, encoding='utf-8')
                print(f"Updated links in {filepath.name}")
                return len(relative_links)
            else:
                print(f"Links unchanged in {filepath.name}")
                return 0
        else:
            # Append new block
            new_content = content.rstrip() + "\n\n" + link_block
            filepath.write_text(new_content, encoding='utf-8')
            print(f"Added new link block to {filepath.name}")
            return len(relative_links)

    except Exception as e:
        print(f"Error: Could not modify file {filepath}: {e}")
        return -1  # Indicate error

# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="Analyze and link markdown files in an Obsidian vault based on semantic similarity.")
    parser.add_argument("vault_path", help="Path to the Obsidian vault directory.")
    parser.add_argument("--clusters", type=int, default=40, help="Number of clusters (currently informational, not used for linking).")
    parser.add_argument("--similarity", type=float, default=0.6, help="Minimum cosine similarity threshold for linking.")
    parser.add_argument("--title-weight", type=float, default=0.4, help="Weight for title similarity (currently ignored).")
    parser.add_argument("--content-weight", type=float, default=0.6, help="Weight for content similarity (currently effectively 1.0).")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for embedding generation.")
    parser.add_argument("--min-links", type=int, default=1, help="Minimum number of links desired per file (best effort based on threshold).")
    parser.add_argument("--max-links", type=int, default=9, help="Maximum number of links to add per file.")
    parser.add_argument("--delete-links", action="store_true", help="Delete previously auto-generated link sections before applying new ones.")
    parser.add_argument("--apply-links", action="store_true", help="Actually modify markdown files to insert links.")
    parser.add_argument("--force-embeddings", action="store_true", help="Force regeneration of embeddings, ignoring cache.")
    parser.add_argument("--model", type=str, default="all-MiniLM-L6-v2", help="Sentence Transformer model name (e.g., 'gtr-t5-large', 'all-mpnet-base-v2', 'gtr-x5-l' - ensure model exists).") # Changed default to a common one

    args = parser.parse_args()

    # --- Input Validation ---
    if not os.path.isdir(args.vault_path):
        print(f"Error: Vault path '{args.vault_path}' not found or is not a directory.")
        return

    if not 0.0 <= args.similarity <= 1.0:
        print("Error: Similarity threshold must be between 0.0 and 1.0.")
        return
    # Basic check for weights (though not used in this simple implementation)
    # if args.title_weight + args.content_weight != 1.0:
    #    print("Warning: Title and Content weights do not sum to 1.0. This implementation currently only uses content.")
    #    pass

    if args.min_links < 0 or args.max_links < 0 or args.min_links > args.max_links:
        print("Error: Invalid min/max links configuration.")
        return

    # --- Setup ---
    # Check for CUDA availability
    if torch.cuda.is_available():
        device = 'cuda'
        print(f"CUDA available. Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        device = 'cpu'
        print("CUDA not available. Using CPU.")

    # Ensure cache directory exists
    cache_dir_path = os.path.join(args.vault_path, EMBEDDING_CACHE_DIR)
    os.makedirs(cache_dir_path, exist_ok=True)


    # --- Core Logic ---
    # 1. Find Files
    all_files = find_markdown_files(args.vault_path)
    if not all_files:
        print("No markdown files found. Exiting.")
        return

    # 2. Load Model
    print(f"Loading sentence transformer model: {args.model}...")
    try:
        model = SentenceTransformer(args.model, device=device)
    except Exception as e:
        print(f"Error loading model '{args.model}'. Ensure it's a valid Sentence Transformer name and installed/downloadable.")
        print(f"Details: {e}")
        print("Common models: 'all-MiniLM-L6-v2', 'all-mpnet-base-v2', 'multi-qa-mpnet-base-dot-v1'")
        print("For 'gtr-...' models, you might need to install sentence-transformers[transformers] or ensure internet connection.")
        return
    print("Model loaded successfully.")


    # 3. Generate/Load Embeddings (handles caching)
    # Read contents lazily only if needed for embedding generation inside the function
    # We pass paths and let the function handle reading/caching
    embeddings, valid_file_paths = generate_embeddings(
    all_files, None, model, args.batch_size, device, cache_dir_path, args.force_embeddings, args.model
    )

    if len(valid_file_paths) == 0:
        print("Stopping due to lack of valid embeddings.")
        return
    if len(valid_file_paths) != len(all_files):
         print(f"Warning: Processed {len(valid_file_paths)} files out of {len(all_files)} due to errors or skips.")


    # 4. Calculate Similarity
    similarity_matrix = calculate_similarity(embeddings)

    # 5. Find Links
    potential_links = find_links(similarity_matrix, valid_file_paths, args.similarity, args.min_links, args.max_links)

    # 6. Apply Links (if requested)
    if args.apply_links:
        print("Applying links to markdown files...")
        total_links_added = 0
        files_modified = 0
        files_with_errors = 0

        for file_path, targets in tqdm(potential_links.items(), desc="Modifying files"):
            # Check if the file_path is still valid (it should be from valid_file_paths)
            if file_path in valid_file_paths:
                 result = modify_markdown_file(file_path, targets, args.delete_links)
                 if result > 0:
                     total_links_added += result
                     files_modified += 1
                 elif result < 0:
                      files_with_errors += 1
            else:
                # This shouldn't happen if logic is correct, but good to check
                print(f"Warning: Skipping modification for {file_path} as it was not in the valid processed list.")


        print("\n--- Linking Summary ---")
        print(f"Files processed: {len(valid_file_paths)}")
        print(f"Files modified: {files_modified}")
        print(f"Total wikilinks added/updated: {total_links_added}")
        if files_with_errors > 0:
            print(f"Errors modifying files: {files_with_errors}")
        print("------------------------")
        if not args.delete_links:
            print("Note: Existing auto-link sections were not deleted (--delete-links not used).")

    else:
        print("\n--- Dry Run Summary ---")
        print(f"Files processed: {len(valid_file_paths)}")
        print(f"Similarity threshold: {args.similarity}")
        print(f"Link limits per file: min={args.min_links}, max={args.max_links}")
        print("Potential links identified (not applied):")
        # Optionally print some example links found
        count = 0
        for source, targets in potential_links.items():
            if targets and count < 5: # Print for first 5 files with links
                print(f"  - {source.name} -> {[t.stem for t in targets]}")
                count +=1
            elif count >= 5:
                 print("  - ... (and potentially many more)")
                 break
        if count == 0:
             print("  (No links found meeting the criteria)")
        print("\nRun with --apply-links to modify files.")
        print("------------------------")

    print("Script finished.")

if __name__ == "__main__":
    main()