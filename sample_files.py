import sqlite3
import os
from pathlib import Path

db_path = Path(r"D:\Obsidian\GPT\GPT2025-12-02\.obsidian_linker_cache\cache.db")
conn = sqlite3.connect(db_path)
cursor = conn.execute('SELECT file_path FROM file_metadata ORDER BY RANDOM() LIMIT 40')

print("Sample filenames from vault:")
for row in cursor.fetchall():
    print(f"  {os.path.basename(row[0])}")

conn.close()
