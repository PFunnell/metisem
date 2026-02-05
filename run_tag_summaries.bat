@echo off
cd /d D:\dev\obsidian-linker
echo Removing existing tags...
python tagger.py "D:\Obsidian\GPT\GPT2025-12-02" --remove-tags
echo.
echo Re-tagging based on summaries...
python tagger.py "D:\Obsidian\GPT\GPT2025-12-02" --tags-file tags.txt --apply-tags --tag-summaries --force-embeddings --tag-threshold 0.20 --max-tags 3
pause
