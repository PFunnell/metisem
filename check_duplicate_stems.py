"""Check for duplicate filename stems in vault."""
from pathlib import Path
from collections import defaultdict

vault = Path(r"D:\Obsidian\GPT\GPT2025-12-02")

stems = defaultdict(list)
for md_file in vault.rglob("*.md"):
    stems[md_file.stem].append(md_file)

duplicates = {stem: paths for stem, paths in stems.items() if len(paths) > 1}

print(f"Total unique stems: {len(stems)}")
print(f"Duplicate stems: {len(duplicates)}")
print(f"Affected files: {sum(len(paths) for paths in duplicates.values())}")

if duplicates:
    print("\nTop 10 most common duplicates:")
    sorted_dupes = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
    for stem, paths in sorted_dupes[:10]:
        print(f"  '{stem}': {len(paths)} files")
        for p in paths[:3]:
            print(f"    - {p.relative_to(vault)}")
        if len(paths) > 3:
            print(f"    ... and {len(paths) - 3} more")
