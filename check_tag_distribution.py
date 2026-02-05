"""Check tag distribution after summary-based tagging."""
import re
from pathlib import Path
from collections import Counter
import yaml

vault_path = Path(r'D:\Obsidian\GPT\GPT2025-12-02')
tag_counts = Counter()
files_with_tags = 0

for md_file in vault_path.rglob('*.md'):
    if '.metisem' in md_file.parts or '.obsidian' in md_file.parts:
        continue

    try:
        text = md_file.read_text(encoding='utf-8')
        match = re.match(r'^---\s*\n([\s\S]*?)\n---', text, re.MULTILINE)

        if match:
            try:
                fm = yaml.safe_load(match.group(1))
                if fm and 'tags' in fm and fm['tags']:
                    tags = fm['tags'] if isinstance(fm['tags'], list) else [fm['tags']]
                    if tags:
                        files_with_tags += 1
                        for tag in tags:
                            tag_counts[tag] += 1
            except yaml.YAMLError:
                pass
    except Exception:
        pass

print('=== SUMMARY-BASED TAGGING RESULTS ===\n')
print(f'{"Tag":<35} {"Count":>6} {"% of Total":>10}')
print('-' * 54)

total_tags = sum(tag_counts.values())
for tag, count in tag_counts.most_common():
    pct = (count / total_tags * 100) if total_tags > 0 else 0
    print(f'{tag:<35} {count:>6} {pct:>9.1f}%')

print('-' * 54)
print(f'{"TOTAL":<35} {total_tags:>6} {"100.0%":>10}')
print()
print(f'Files with tags: {files_with_tags}')
print(f'Total files: {len(list(vault_path.rglob("*.md")))}')
print(f'Coverage: {files_with_tags / 2034 * 100:.1f}%')
print()

# Compare with previous full-text results
print('=== COMPARISON WITH FULL-TEXT TAGGING ===\n')
print('Previous (full-text @ 0.20):')
print('  ai_tooling_and_models: 985 (40.0%)')
print('  productivity: 326 (13.2%)')
print('  context_engineering: 249 (10.1%)')
print('  Total tags: 2,464')
print('  Coverage: 63.5% (1,291 files)')
print()
print('Current (summary-based @ 0.20):')
if 'ai_tooling_and_models' in tag_counts:
    ai_pct = tag_counts['ai_tooling_and_models'] / total_tags * 100 if total_tags > 0 else 0
    print(f'  ai_tooling_and_models: {tag_counts["ai_tooling_and_models"]} ({ai_pct:.1f}%)')
else:
    print('  ai_tooling_and_models: 0 (0.0%)')
print(f'  Total tags: {total_tags}')
print(f'  Coverage: {files_with_tags / 2034 * 100:.1f}% ({files_with_tags} files)')
