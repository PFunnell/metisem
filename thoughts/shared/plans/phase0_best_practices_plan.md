# Phase 0: Best Practices & QoL Fixes

**Project:** obsidian-linker
**Date:** 2026-02-01
**Status:** APPROVED
**Prerequisite for:** Enhancement Plan Phase 1

---

## Objective

Address technical debt and compliance gaps before beginning enhancement work. Establishes foundation for safe refactoring and distribution.

**Context:** Repository is public and may receive attention from potential employers reviewing your portfolio.

---

## Phase 0.0: Public Repo Hygiene Audit

**Goal:** Review what's visible on GitHub and ensure professional presentation.

**Audit checklist:**
- [ ] **Commit history:** Review recent commits for quality, clarity, professionalism
- [ ] **Commit messages:** Check for WIP commits, debug messages, unprofessional language
- [ ] **Sensitive data:** Scan history for leaked credentials, API keys, personal paths
- [ ] **Branch hygiene:** Clean up stale/WIP branches visible on remote
- [ ] **README first impression:** Does it clearly explain what this project does?
- [ ] **Issues/PRs:** Any open issues or PRs that look abandoned?
- [ ] **File names:** Any temp files, backup files, or debug scripts visible?
- [ ] **Code comments:** Any TODO/FIXME/HACK comments that look bad?
- [ ] **GitHub profile:** Repo description, topics, website link set?

**Actions to take:**
- Rewrite any problematic commit messages (interactive rebase if needed)
- Remove sensitive data from history (BFG or filter-branch)
- Delete stale remote branches
- Update repo description and topics on GitHub
- Ensure README has professional tone and clear value proposition

**Verification:** Manual review of GitHub repo page as if you're an employer

---

## Phase 0.1: Distribution Blockers

**Files to create:**
- `LICENSE` (MIT)
- `requirements.txt`
- `pyproject.toml`

**requirements.txt contents:**
```
sentence-transformers>=2.2.0
scikit-learn>=1.0.0
numpy>=1.21.0
torch>=1.9.0
pyyaml>=6.0
tqdm>=4.62.0
requests>=2.25.0
```

**pyproject.toml:** Minimal package metadata, no build system yet.

**Verification:** `pip install -r requirements.txt` succeeds in fresh venv

---

## Phase 0.2: Critical Bug Fixes

**Files to modify:**
- `main.py:46` - Replace bare `except:` with `except Exception as e:` + logging
- `main.py:174` - Replace bare `except:` with specific exception handling
- `summariser_ollama.py:2` - Remove unused `import os`

**Verification:** `python -c "import main; import tagger; import summariser_ollama"` - no warnings

---

## Phase 0.3: Configuration & Environment

**Files to modify:**
- `summariser_ollama.py` - Add `OLLAMA_HOST` env var support (default: `localhost:11434`)

**Files to create:**
- `.env.example` - Document available env vars

**Verification:** `OLLAMA_HOST=custom:11434 python summariser_ollama.py --help` respects env var

---

## Phase 0.4: Logging Infrastructure

**Files to modify:**
- `main.py` - Replace `print()` with `logging` module
- `tagger.py` - Replace `print()` with `logging` module
- `summariser_ollama.py` - Replace `print()` with `logging` module

**Pattern:**
```python
import logging
logger = logging.getLogger(__name__)
# Replace print("message") with logger.info("message")
# Replace print("Error:...") with logger.error("...")
```

**CLI addition:** `--verbose` flag sets DEBUG level, default is INFO

**Verification:** Run each tool, confirm structured log output

---

## Phase 0.5: Type Hints (Public API)

**Files to modify:**
- `main.py` - Add type hints to all functions
- `tagger.py` - Add type hints to all functions
- `summariser_ollama.py` - Add type hints to all functions

**Scope:** Function signatures only (parameters + return types), not internal variables

**Verification:** `mypy main.py tagger.py summariser_ollama.py --ignore-missing-imports` passes

---

## Phase 0.6: Documentation & Cleanup

**Files to modify:**
- `README.md` - Add: installation section, dev setup, troubleshooting
- All Python files - Add module docstrings and function docstrings

**Files to delete:**
- `main.bak.py` - Remove from repo

**Files to create:**
- `CONTRIBUTING.md` - Basic contribution guidelines

**Verification:** README covers installation, all public functions have docstrings

---

## Phase 0.7: Developer Tooling

**Files to create:**
- `pyproject.toml` additions: `[tool.ruff]` config for linting
- `.pre-commit-config.yaml` - ruff, trailing whitespace, end-of-file

**Verification:** `pre-commit run --all-files` passes

---

## Summary

| Phase | Scope | Files |
|-------|-------|-------|
| 0.0 | Repo hygiene | Git history, branches, GitHub settings |
| 0.1 | Distribution | LICENSE, requirements.txt, pyproject.toml |
| 0.2 | Bug fixes | main.py |
| 0.3 | Configuration | summariser_ollama.py, .env.example |
| 0.4 | Logging | main.py, tagger.py, summariser_ollama.py |
| 0.5 | Type hints | main.py, tagger.py, summariser_ollama.py |
| 0.6 | Documentation | README.md, CONTRIBUTING.md, all .py |
| 0.7 | Tooling | pyproject.toml, .pre-commit-config.yaml |

---

## Verification Checklist

**Phase 0.0:**
- [ ] Git history reviewed for sensitive data / unprofessional commits
- [ ] Stale branches deleted from remote
- [ ] GitHub repo description and topics set
- [ ] README presents professionally

**Phases 0.1-0.7:**
- [ ] `pip install -r requirements.txt` succeeds
- [ ] All imports work without warnings
- [ ] `OLLAMA_HOST` env var respected
- [ ] Logging output is structured (not print)
- [ ] `mypy` passes on all files
- [ ] `pre-commit run --all-files` passes
- [ ] README has installation + dev setup sections
- [ ] LICENSE file present (MIT)
- [ ] `main.bak.py` removed from repo
