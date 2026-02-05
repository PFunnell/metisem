"""Find files with empty link blocks."""
import re
from pathlib import Path

vault = Path(r"D:\Obsidian\GPT\GPT2025-12-02")

for md_file in vault.rglob("*.md"):
    try:
        text = md_file.read_text(encoding='utf-8')
        if "AUTO-GENERATED LINKS START" in text:
            match = re.search(r'<!-- AUTO-GENERATED LINKS START -->(.+?)<!-- AUTO-GENERATED LINKS END -->', text, re.DOTALL)
            if match:
                block_content = match.group(1)
                links = re.findall(r'\[\[([^\]]+)\]\]', block_content)
                if len(links) == 0:
                    print(f"File with 0 links: {md_file}")
                    print(f"Block content:\n{block_content}")
                    print("="*60)
    except Exception as e:
        pass
