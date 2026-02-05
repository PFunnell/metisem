@echo off
cd /d D:\dev\obsidian-linker
python summariser_ollama.py "D:\Obsidian\GPT\GPT2025-12-02" --apply-summaries --model mistral
pause
