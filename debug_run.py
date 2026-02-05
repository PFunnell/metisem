"""Debug actual linker run to find discrepancy."""
import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Check the actual vault after the last run
vault = Path(r"D:\Obsidian\GPT\GPT2025-12-02")

# Count what was CLAIMED vs ACTUAL
claimed_counts = {}
actual_counts = {}

for md_file in vault.rglob("*.md"):
    try:
        text = md_file.read_text(encoding='utf-8')

        # Check if file has a link block
        has_block = "AUTO-GENERATED LINKS START" in text

        if has_block:
            # Count actual links in block
            match = re.search(r'<!-- AUTO-GENERATED LINKS START -->(.+?)<!-- AUTO-GENERATED LINKS END -->', text, re.DOTALL)
            if match:
                block_content = match.group(1)
                links = re.findall(r'\[\[([^\]]+)\]\]', block_content)
                count = len(links)
                actual_counts[count] = actual_counts.get(count, 0) + 1
    except Exception:
        pass

# From last run log
print("Script CLAIMED:")
print("  60 files with 1 links")
print("  27 files with 2 links")
print("  21 files with 3 links")
print("  21 files with 4 links")
print("  1905 files with 5 links")
print("  Total: 2034 files, 9784 links")

print("\nVault ACTUALLY has:")
for count in sorted(actual_counts.keys()):
    print(f"  {actual_counts[count]} files with {count} links")

total_files = sum(actual_counts.values())
total_links = sum(count * num for count, num in actual_counts.items())
print(f"  Total: {total_files} files, {total_links} links")

# Find files that might have been "claimed" but not written
print("\n=== Discrepancy Analysis ===")
print(f"Missing files: {2034 - total_files}")
print(f"Missing links: {9784 - total_links}")
