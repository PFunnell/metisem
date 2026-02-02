# Contributing to obsidian-linker

Thank you for considering contributing to obsidian-linker! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- A clear, descriptive title
- Steps to reproduce the problem
- Expected vs actual behaviour
- Your environment (OS, Python version, etc.)
- Relevant log output or error messages

### Suggesting Features

Feature suggestions are welcome! Please:
- Check existing issues first to avoid duplicates
- Clearly describe the feature and its use case
- Explain why this feature would be useful to most users

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the code style guidelines below
3. **Test your changes** manually against a test vault
4. **Update documentation** if you've changed functionality
5. **Write clear commit messages** describing what and why
6. **Submit a pull request** with a clear description of the changes

## Code Style Guidelines

### Python Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Write docstrings for all public functions and modules
- Keep functions focused and single-purpose
- Use meaningful variable names

### Type Hints

All functions should have type hints:
```python
def process_file(path: Path, threshold: float) -> List[str]:
    """Process a file and return results."""
    ...
```

### Logging

Use the `logging` module instead of `print()`:
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Processing files...")
logger.error("Failed to process file: %s", filepath)
```

### Documentation

- Add module-level docstrings explaining the module's purpose
- Add function docstrings for all public functions
- Update README.md if adding new features or changing behaviour
- Include examples for new CLI options

## Development Workflow

### Setting Up

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/metisem.git
cd metisem

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install mypy pre-commit
pre-commit install
```

### Testing

Currently, testing is manual:
1. Create or use a test vault with markdown files
2. Run your changes against the test vault
3. Verify expected behaviour
4. Check that no files are corrupted

Future: Automated tests are planned.

### Type Checking

Run mypy before submitting:
```bash
mypy main.py tagger.py summariser_ollama.py --ignore-missing-imports
```

## Project Structure

```
obsidian-linker/
├── main.py              # Semantic link generator
├── tagger.py            # Auto-tagging tool
├── summariser_ollama.py # Summarization tool
├── requirements.txt     # Python dependencies
├── README.md            # User documentation
└── CONTRIBUTING.md      # This file
```

## Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests when relevant

Example:
```
Add support for custom Ollama host via env var

- Add OLLAMA_HOST environment variable
- Update documentation
- Fixes #123
```

## Questions?

If you have questions about contributing, feel free to:
- Open an issue with the "question" label
- Reach out to maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
