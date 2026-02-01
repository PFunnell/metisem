# Best Practices Review: obsidian-linker

**Date:** 2026-02-01
**Scope:** Code quality, project structure, documentation, developer experience

---

## Critical Issues (Fix First)

### 1. Bare Exception Clauses
| File | Line | Issue |
|------|------|-------|
| `main.py` | 46 | `except:` in `load_embeddings_from_cache()` masks all errors |
| `main.py` | 174 | `except:` in `modify_markdown_file()` silently fails |

**Risk:** Masks keyboard interrupts, system exits, and hides root cause of failures.

### 2. Missing requirements.txt
- README mentions `pip install` but no requirements file exists
- Missing from README: `numpy`, `torch`, `requests`
- No version pinning

### 3. No LICENSE File
- Repository is public on GitHub
- Legally ambiguous for redistribution
- Blocks plugin store submission

### 4. No pyproject.toml / setup.py
- Cannot be installed via `pip install .`
- No version metadata
- No entry points for CLI commands

---

## High Priority Issues

### Type Hints (All 3 main files)
- Zero type annotations across 600+ lines of Python
- Makes IDE support and refactoring difficult
- Example fix:
  ```python
  # Before
  def find_markdown_files(vault_path):
  # After
  def find_markdown_files(vault_path: Path) -> list[Path]:
  ```

### Logging vs Print
- All output uses `print()` statements
- No log levels, timestamps, or file output capability
- 15+ print statements across 3 files

### Docstrings
| File | Functions | Documented |
|------|-----------|------------|
| `main.py` | 9 | 0 |
| `tagger.py` | 12 | 0 |
| `summariser_ollama.py` | 6 | 4 |

### No Test Suite
- CLAUDE.md acknowledges this gap
- Manual verification only
- Blocks safe refactoring

---

## Medium Priority Issues

### Code Duplication
`find_markdown_files()` implemented 3 times:
- `main.py:26` - `glob.glob()`
- `tagger.py:21` - `Path.rglob()`
- `summariser_ollama.py:13` - `glob.glob()`

Cache constants defined 3 times:
- `main.py:18` - `EMBEDDING_CACHE_DIR`
- `tagger.py:14` - `CACHE_DIR`
- `summariser_ollama.py` - hardcoded

### Hardcoded Configuration
- Ollama URL: `http://localhost:11434` (summariser_ollama.py:84)
- No environment variable support
- No config file for user settings

### Unused Imports
- `summariser_ollama.py:2` - `import os` never used
- `tagger.py:1` - `import os` used once, could use `Path.parent`

### Security: Pickle Loading
- `main.py:43` - `np.load(..., allow_pickle=True)`
- `tagger.py:40` - Same pattern
- Cache could execute arbitrary code if compromised

### Backup File in Repo
- `main.bak.py` (20KB) tracked in git
- Should be removed or in `.gitignore`

---

## Low Priority / QoL Issues

### Missing Developer Tooling
- No `.pre-commit-config.yaml`
- No linting config (`pyproject.toml [tool.ruff]`, `flake8.ini`)
- No formatting config (`black`, `isort`)
- No `.editorconfig`

### README Gaps
- No development setup instructions
- No troubleshooting section
- Referenced image `metisem1.png` missing
- No advanced usage examples (clustering, batch tuning)

### Missing Community Files
- No `CONTRIBUTING.md`
- No issue templates
- No PR templates

### Conda Environment
- `.conda/` exists but no `environment.yml`
- Recreation instructions missing

---

## Summary Table

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Error Handling | 2 | - | - | - |
| Project Files | 2 | - | - | - |
| Type Safety | - | 3 files | - | - |
| Documentation | - | 2 files | 1 | 3 |
| Code Quality | - | 1 | 3 | - |
| Security | - | - | 2 | - |
| Tooling | - | - | - | 4 |

---

## Recommended Fix Order

**Phase A: Unblock distribution**
1. Add `LICENSE` (MIT recommended)
2. Create `requirements.txt` with versions
3. Create minimal `pyproject.toml`

**Phase B: Fix critical bugs**
4. Replace bare `except:` with specific exceptions
5. Add error logging to file operations

**Phase C: Code quality baseline**
6. Extract shared module (`obsidian_linker/core/`)
7. Add type hints to public functions
8. Replace `print()` with `logging`
9. Add docstrings to all functions

**Phase D: Developer experience**
10. Add `ruff` linting config
11. Add pre-commit hooks
12. Create basic test suite
13. Update README with dev setup

---

## Quick Wins (< 5 min each)

1. Delete `main.bak.py` from repo
2. Remove unused `import os` from summariser_ollama.py
3. Add `OLLAMA_HOST` env var support (3 lines)
4. Create empty `requirements.txt` and populate from imports
