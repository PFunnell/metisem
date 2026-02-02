import sqlite3
import hashlib
from pathlib import Path

db_path = Path(r"D:\Obsidian\GPT\GPT2025-12-02\.obsidian_linker_cache\cache.db")
conn = sqlite3.connect(db_path)

cursor = conn.execute('SELECT COUNT(*) FROM file_metadata')
print(f'Files in cache: {cursor.fetchone()[0]}')

# Check all files for matches
cursor = conn.execute('SELECT file_path, content_hash, mtime_ns FROM file_metadata')
mtime_matches = 0
hash_matches = 0
mtime_diff_hash_match = 0
both_diff = 0
missing_files = 0

for file_path, stored_hash, stored_mtime in cursor.fetchall():
    p = Path(file_path)
    if not p.exists():
        missing_files += 1
        continue

    try:
        current_mtime = p.stat().st_mtime_ns
        content = p.read_text(encoding='utf-8')
        current_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        mtime_match = current_mtime == stored_mtime
        hash_match = current_hash == stored_hash

        if mtime_match and hash_match:
            mtime_matches += 1
            hash_matches += 1
        elif not mtime_match and hash_match:
            mtime_diff_hash_match += 1
            hash_matches += 1
        elif not mtime_match and not hash_match:
            both_diff += 1
        elif mtime_match and not hash_match:
            # This shouldn't happen but check anyway
            hash_matches += 0
    except Exception as e:
        missing_files += 1

print(f'\nAnalysis:')
print(f'  Both match (unchanged): {mtime_matches}')
print(f'  Mtime differs, hash matches: {mtime_diff_hash_match}')
print(f'  Both differ (modified): {both_diff}')
print(f'  Missing files: {missing_files}')
print(f'\nTotal truly unchanged: {mtime_matches + mtime_diff_hash_match}')

conn.close()
