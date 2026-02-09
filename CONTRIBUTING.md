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

All changes should include appropriate tests. The project uses pytest for testing:

**Running Tests:**
```bash
# Run all unit tests (fast, no external dependencies)
pytest tests/unit/ -v

# Run with coverage report
pytest tests/unit/ --cov=metisem --cov-report=html

# Run specific test file
pytest tests/unit/test_database.py -v

# Run integration tests (requires TEST_VAULT_PATH environment variable)
export TEST_VAULT_PATH="/path/to/test/vault"
pytest tests/integration/ -v
```

**Coverage Requirements:**
- New code should maintain or improve overall coverage (~80%)
- Core modules (database, embeddings, markers) should maintain 100% coverage
- Pull requests that significantly reduce coverage may be asked for additional tests

**Writing Tests:**
- Unit tests go in `tests/unit/` and test individual functions/classes
- Integration tests go in `tests/integration/` and test complete workflows
- Use synthetic fixtures from `tests/fixtures/markdown_samples.py`
- Mock external dependencies (Sentence Transformers, Ollama)
- Test edge cases and error conditions

**Test Organization:**
```python
class TestFeatureName:
    """Tests for FeatureName functionality."""

    def test_normal_case(self):
        """Should handle normal input correctly."""
        # Arrange
        input_data = ...

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected_value
```

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
