"""Debug script to trace link writing discrepancy."""
from pathlib import Path
import re

vault = Path(r"D:\Obsidian\GPT\GPT2025-12-02")

# Count files by their link count
files_with_links = {}
for md_file in vault.rglob("*.md"):
    try:
        text = md_file.read_text(encoding='utf-8')
        if "AUTO-GENERATED LINKS START" in text:
            match = re.search(r'<!-- AUTO-GENERATED LINKS START -->(.+?)<!-- AUTO-GENERATED LINKS END -->', text, re.DOTALL)
            if match:
                block_content = match.group(1)
                links = re.findall(r'\[\[([^\]]+)\]\]', block_content)
                count = len(links)
                if count not in files_with_links:
                    files_with_links[count] = 0
                files_with_links[count] += 1
    except Exception:
        pass

# Print distribution
print("Actual link distribution in vault:")
total_files = 0
total_links = 0
for count in sorted(files_with_links.keys()):
    num_files = files_with_links[count]
    print(f"  {num_files} files with {count} links")
    total_files += num_files
    total_links += (num_files * count)

print(f"\nTotal: {total_files} files, {total_links} links")
