"""Count actual links in auto-generated blocks."""
import re
from pathlib import Path

vault = Path(r"D:\Obsidian\GPT\GPT2025-12-02")
files_with_blocks = 0
total_links = 0

for md_file in vault.rglob("*.md"):
    try:
        text = md_file.read_text(encoding='utf-8')
        if "AUTO-GENERATED LINKS START" in text:
            files_with_blocks += 1
            # Extract content between markers
            match = re.search(r'<!-- AUTO-GENERATED LINKS START -->(.+?)<!-- AUTO-GENERATED LINKS END -->', text, re.DOTALL)
            if match:
                block_content = match.group(1)
                # Count wikilinks
                links = re.findall(r'\[\[([^\]]+)\]\]', block_content)
                total_links += len(links)
    except Exception as e:
        pass

print(f"Files with link blocks: {files_with_blocks}")
print(f"Total wikilinks: {total_links}")
print(f"Average links per file: {total_links/files_with_blocks if files_with_blocks > 0 else 0:.1f}")
