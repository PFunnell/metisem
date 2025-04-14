import os
import glob
import argparse
import re
from pathlib import Path
import hashlib
import yaml # For YAML front matter handling
from io import StringIO # To handle string IO for YAML parsing

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import torch
from tqdm import tqdm

# --- Constants ---
EMBEDDING_CACHE_DIR = ".obsidian_linker_cache" # Store cache in a hidden dir
YAML_FRONT_MATTER_SEP = '---'
TAGS_KEY = 'tags' # Standard key for tags in Obsidian YAML

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
        # Read the whole file first
        full_content = filepath.read_text(encoding='utf-8')

        # Basic front matter extraction (doesn't need full parsing here)
        # We only need the main content for embedding
        content_parts = full_content.split(YAML_FRONT_MATTER_SEP)
        if len(content_parts) >= 3 and content_parts[0] == '':
            # Has front matter
            main_content = YAML_FRONT_MATTER_SEP.join(content_parts[2:])
        else:
            # No front matter or improperly formatted
            main_content = full_content

        title = filepath.stem # Filename without extension
        return title, main_content.strip() # Return stripped main content
    except Exception as e:
        print(f"Warning: Could not read file {filepath}: {e}")
        return None, None

def get_file_hash(filepath):
    """Calculates the SHA256 hash of a file's content."""
    hasher = hashlib.sha256()
    try:
        # Hash the *entire* file content including potential front matter
        # This ensures embedding is recalculated if front matter OR content changes
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
        if not embeddings_data:
             print("No embedding data to save.")
             return

        max_path_len = max(len(str(p)) for p in embeddings_data.keys())
        # Use embedding dim from the first item, assume consistency
        embedding_dim = len(next(iter(embeddings_data.values()))['embedding'])
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

def generate_embeddings(texts_or_paths, model, batch_size, device, cache_dir=None, force_embeddings=False, is_document=True):
    """
    Generates embeddings for file contents (using cache) or simple texts (no cache).

    Args:
        texts_or_paths: List of file paths (if is_document=True) or list of strings (if is_document=False).
        model: The SentenceTransformer model.
        batch_size: Batch size for encoding.
        device: 'cuda' or 'cpu'.
        cache_dir: Directory for caching (only used if is_document=True).
        force_embeddings: Force regeneration even if cache exists (only used if is_document=True).
        is_document: Boolean indicating if input is file paths (True) or raw texts (False).

    Returns:
        Tuple: (numpy array of embeddings, list of valid corresponding paths/texts)
    """
    if is_document:
        # --- Document Embedding with Caching ---
        file_paths = texts_or_paths
        if not file_paths: return np.array([]), []

        vault_path = os.path.commonpath(file_paths) if file_paths else '.'
        # Use a distinct cache file for documents vs tags if needed, but model name differentiates enough
        cache_filename = f"embeddings_{Path(vault_path).name}_{model.config.name_or_path.replace('/', '_')}.npy"
        cache_path = os.path.join(cache_dir, cache_filename)

        cached_embeddings = {}
        if not force_embeddings and cache_dir:
            cached_embeddings = load_embeddings_from_cache(cache_path)

        embeddings_map = {} # path -> {hash, embedding}
        texts_to_embed_map = {} # path -> content
        paths_to_process = []
        hashes_map = {} # path -> hash

        print("Checking file hashes for document embedding cache...")
        for path in tqdm(file_paths, desc="Hashing files"):
            file_hash = get_file_hash(path)
            if file_hash:
                hashes_map[path] = file_hash
                paths_to_process.append(path) # Keep track of files we could hash
                # Check cache
                if path in cached_embeddings and cached_embeddings[path]['hash'] == file_hash:
                    embeddings_map[path] = cached_embeddings[path] # Use cached embedding
                else:
                    # Need to generate embedding for this file, read content later
                    pass # Mark for embedding
            else:
                 print(f"Skipping {path} due to hashing error.")


        print(f"{len(embeddings_map)} document embeddings loaded from cache.")
        # Read content only for files needing embedding
        paths_needing_embedding = [p for p in paths_to_process if p not in embeddings_map]
        print(f"Reading content for {len(paths_needing_embedding)} files needing embedding...")
        for path in tqdm(paths_needing_embedding, desc="Reading files"):
             _, content = read_file_content(path)
             if content is not None:
                 texts_to_embed_map[path] = content
             else:
                 print(f"Skipping {path} due to read error during embedding check.")
                 # Remove from hashes_map if read failed, so it's not saved later
                 if path in hashes_map: del hashes_map[path]


        if not texts_to_embed_map:
            print("All document embeddings up-to-date or loaded from cache.")
        else:
            print(f"Generating embeddings for {len(texts_to_embed_map)} documents...")
            # Ensure order matches for embedding assignment
            paths_to_embed_ordered = list(texts_to_embed_map.keys())
            texts_to_embed_ordered = [texts_to_embed_map[p] for p in paths_to_embed_ordered]

            new_embeddings_list = model.encode(
                texts_to_embed_ordered,
                batch_size=batch_size,
                show_progress_bar=True,
                device=device,
                convert_to_numpy=True
            )

            # Add newly generated embeddings to the map
            for i, path in enumerate(paths_to_embed_ordered):
               if path in hashes_map: # Ensure hash was calculated and read succeeded
                   embeddings_map[path] = {'hash': hashes_map[path], 'embedding': new_embeddings_list[i]}

        # Save updated cache if changes were made or forced
        if texts_to_embed_map or force_embeddings:
           if cache_dir:
               save_embeddings_to_cache(cache_path, embeddings_map)
           else:
               print("Warning: Cache directory not provided, embeddings not saved.")

        # Return embeddings in the original order of file_paths
        final_embeddings = []
        valid_paths = []
        for path in file_paths:
            if path in embeddings_map:
                final_embeddings.append(embeddings_map[path]['embedding'])
                valid_paths.append(path)
            # else:
            #    print(f"Warning: No embedding found or generated for {path}. It might have been skipped due to errors.")

        if not final_embeddings:
            print("Error: No document embeddings were generated or loaded successfully.")
            return np.array([]), []

        return np.array(final_embeddings), valid_paths

    else:
        # --- Simple Text Embedding (No Caching) ---
        texts = texts_or_paths
        if not texts: return np.array([]), []
        print(f"Generating embeddings for {len(texts)} tags...")
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            device=device,
            convert_to_numpy=True
        )
        print("Tag embedding complete.")
        return embeddings, texts # Return embeddings and the original texts

def load_tags(filepath):
    """Loads tags from a file, one tag per line."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tags = [line.strip() for line in f if line.strip()]
        if not tags:
            print(f"Warning: No tags found in {filepath}")
            return []
        print(f"Loaded {len(tags)} tags from {filepath}")
        return tags
    except FileNotFoundError:
        print(f"Error: Tags file not found at {filepath}")
        return None
    except Exception as e:
        print(f"Error reading tags file {filepath}: {e}")
        return None

def add_tag_to_markdown(filepath, tag_to_add):
    """
    Adds a tag to the YAML front matter of a markdown file.
    Creates front matter if it doesn't exist.
    Ensures the tag is added uniquely to the 'tags' list.
    """
    try:
        content = filepath.read_text(encoding='utf-8')
        # Use regex to properly split front matter (handles different line endings)
        pattern = re.compile(r'^(' + YAML_FRONT_MATTER_SEP + r'\r?\n)(.*?)(\r?\n' + YAML_FRONT_MATTER_SEP + r'\r?\n)(.*)', re.DOTALL | re.MULTILINE)
        match = pattern.match(content)

        front_matter_dict = {}
        main_content = content

        if match:
            # Existing front matter found
            yaml_content = match.group(2)
            main_content = match.group(4) # Content after the second '---'
            try:
                front_matter_dict = yaml.safe_load(StringIO(yaml_content)) # Use StringIO to load from string
                if front_matter_dict is None: # Handle empty front matter
                     front_matter_dict = {}
            except yaml.YAMLError as e:
                print(f"Warning: Could not parse existing YAML front matter in {filepath.name}. Skipping tag addition. Error: {e}")
                return False # Indicate failure/skip
        else:
            # No front matter found, main_content is the whole file content
            print(f"No front matter found in {filepath.name}. Creating new front matter.")
            pass # Keep front_matter_dict empty

        # Ensure 'tags' key exists and is a list
        if TAGS_KEY not in front_matter_dict:
            front_matter_dict[TAGS_KEY] = []
        elif not isinstance(front_matter_dict[TAGS_KEY], list):
            # If tags exists but isn't a list, convert it (might lose original value)
            print(f"Warning: Existing '{TAGS_KEY}' in {filepath.name} is not a list. Converting to list.")
            # Keep existing value(s) if possible, otherwise overwrite
            existing_value = front_matter_dict[TAGS_KEY]
            if isinstance(existing_value, (str, int, float)): # Handle common scalar types
                 front_matter_dict[TAGS_KEY] = [str(existing_value)]
            else:
                 front_matter_dict[TAGS_KEY] = [] # Overwrite if complex type

        # Add the new tag if it's not already present
        if tag_to_add not in front_matter_dict[TAGS_KEY]:
            front_matter_dict[TAGS_KEY].append(tag_to_add)
            front_matter_dict[TAGS_KEY].sort() # Keep tags sorted alphabetically
            modified = True
        else:
            print(f"Tag '{tag_to_add}' already present in {filepath.name}. Skipping addition.")
            modified = False
            return False # Indicate no change made

        # Write back to file
        try:
            # Dump the updated front matter dictionary back to YAML string
            # Use default_flow_style=False for block style, allow_unicode for wider compatibility
            updated_yaml = yaml.dump(front_matter_dict, default_flow_style=False, allow_unicode=True, sort_keys=False)

            # Construct the new full content
            new_content = f"{YAML_FRONT_MATTER_SEP}\n{updated_yaml}{YAML_FRONT_MATTER_SEP}\n{main_content}"

            filepath.write_text(new_content, encoding='utf-8')
            print(f"Added tag '{tag_to_add}' to {filepath.name}")
            return True # Indicate success

        except yaml.YAMLError as e:
             print(f"Error: Could not dump updated YAML for {filepath.name}. Error: {e}")
             return False
        except Exception as e:
             print(f"Error writing updated file {filepath.name}: {e}")
             return False

    except Exception as e:
        print(f"Error processing file {filepath}: {e}")
        return False


# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="Analyze markdown files and assign the best fitting tag from a list based on semantic similarity.")
    parser.add_argument("vault_path", help="Path to the Obsidian vault directory.")
    parser.add_argument("--tags-file", required=True, help="Path to a text file containing possible tags (one per line).")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for embedding generation.")
    parser.add_argument("--apply-tags", action="store_true", help="Actually modify markdown files to insert tags into YAML front matter.")
    parser.add_argument("--force-embeddings", action="store_true", help="Force regeneration of document embeddings, ignoring cache.")
    parser.add_argument("--model", type=str, default="all-MiniLM-L6-v2", help="Sentence Transformer model name.")

    args = parser.parse_args()

    # --- Input Validation ---
    if not os.path.isdir(args.vault_path):
        print(f"Error: Vault path '{args.vault_path}' not found or is not a directory.")
        return
    if not os.path.isfile(args.tags_file):
        print(f"Error: Tags file '{args.tags_file}' not found.")
        return

    # --- Setup ---
    if torch.cuda.is_available():
        device = 'cuda'
        print(f"CUDA available. Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        device = 'cpu'
        print("CUDA not available. Using CPU.")

    cache_dir_path = os.path.join(args.vault_path, EMBEDDING_CACHE_DIR)
    os.makedirs(cache_dir_path, exist_ok=True)

    # --- Core Logic ---
    # 1. Load Tags
    tags = load_tags(args.tags_file)
    if tags is None or not tags:
        print("Could not load tags or tags file is empty. Exiting.")
        return

    # 2. Find Files
    all_files = find_markdown_files(args.vault_path)
    if not all_files:
        print("No markdown files found. Exiting.")
        return

    # 3. Load Model
    print(f"Loading sentence transformer model: {args.model}...")
    try:
        # Store config name for cache path consistency if model loaded differently
        model_instance = SentenceTransformer(args.model, device=device)
        # Hacky way to get consistent name if model loaded from path vs name
        model_instance.config.name_or_path = args.model
    except Exception as e:
        print(f"Error loading model '{args.model}'. Ensure it's valid.")
        print(f"Details: {e}")
        return
    print("Model loaded successfully.")

    # 4. Generate Document Embeddings (using cache)
    doc_embeddings, valid_doc_paths = generate_embeddings(
        all_files, model_instance, args.batch_size, device, cache_dir_path, args.force_embeddings, is_document=True
    )
    if len(valid_doc_paths) == 0:
        print("Stopping due to lack of valid document embeddings.")
        return
    if len(valid_doc_paths) != len(all_files):
         print(f"Warning: Processed {len(valid_doc_paths)} files out of {len(all_files)} due to errors or skips.")

    # 5. Generate Tag Embeddings (no cache needed, usually fast)
    tag_embeddings, valid_tags = generate_embeddings(
        tags, model_instance, args.batch_size, device, is_document=False
    )
    if len(valid_tags) == 0:
        print("Stopping due to lack of valid tag embeddings.")
        return

    # 6. Calculate Document-Tag Similarities
    print("Calculating document-tag similarity matrix...")
    similarity_matrix = cosine_similarity(doc_embeddings, tag_embeddings)
    print(f"Similarity matrix shape: {similarity_matrix.shape}") # Should be (num_docs x num_tags)

    # 7. Find Best Tag for Each Document
    best_tag_indices = np.argmax(similarity_matrix, axis=1) # Find index of max similarity for each row (doc)
    doc_to_best_tag = {doc_path: valid_tags[tag_index] for doc_path, tag_index in zip(valid_doc_paths, best_tag_indices)}

    # 8. Apply Tags (if requested)
    if args.apply_tags:
        print("Applying best fit tags to markdown files...")
        files_modified_count = 0
        files_error_count = 0

        for file_path, best_tag in tqdm(doc_to_best_tag.items(), desc="Applying tags"):
            success = add_tag_to_markdown(file_path, best_tag)
            if success:
                files_modified_count += 1
            # We count errors within the add_tag function via prints, could add counter here if needed

        print("\n--- Tagging Summary ---")
        print(f"Files processed: {len(valid_doc_paths)}")
        print(f"Files modified (tag added/updated): {files_modified_count}")
        # Add error count here if tracked separately
        print("------------------------")

    else:
        print("\n--- Dry Run Summary ---")
        print(f"Files processed: {len(valid_doc_paths)}")
        print(f"Tags considered: {len(valid_tags)}")
        print("Best tag mapping found (not applied):")
        count = 0
        for doc_path, best_tag in doc_to_best_tag.items():
            if count < 10: # Print for first 10 files
                print(f"  - {doc_path.name} -> #{best_tag}")
                count +=1
            elif count == 10:
                 print("  - ... (and potentially many more)")
                 count += 1 # Prevent printing ellipsis repeatedly
        print("\nRun with --apply-tags to modify files.")
        print("------------------------")

    print("Script finished.")

if __name__ == "__main__":
    main()

