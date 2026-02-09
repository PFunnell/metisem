"""Synthetic markdown test fixtures.

Provides reusable test data without dependency on user vaults.
"""

from pathlib import Path
from typing import List, Tuple
import pytest


def sample_markdown_files() -> List[Tuple[str, str]]:
    """Return list of (filename, content) tuples for various test cases.

    Returns:
        List of tuples containing filename and markdown content
    """
    return [
        # Short note (50 words)
        ("short_note.md", """# Short Note

This is a brief note with minimal content. It contains just enough text
to test basic functionality without overwhelming the embedding model.
Useful for testing quick operations and edge cases with small inputs.
"""),

        # Medium note with YAML front matter (300 words)
        ("medium_with_frontmatter.md", """---
tags:
  - python
  - testing
  - automation
created: 2026-02-09
---

# Medium Note with Tags

This note demonstrates a typical knowledge base entry with YAML front matter.
The content is substantial enough to generate meaningful embeddings while
remaining manageable for test execution speed.

## Section 1: Introduction

Knowledge management systems benefit from structured metadata. Tags enable
quick filtering and categorisation. The YAML front matter format is widely
supported across markdown processors.

## Section 2: Implementation

When implementing markdown processing tools, handling front matter correctly
is critical. The parser must distinguish between YAML blocks and regular
content. This ensures metadata is processed separately from body text.

## Section 3: Best Practices

- Always validate YAML syntax before parsing
- Preserve front matter during content modifications
- Use consistent tag formatting (lowercase, hyphenated)
- Include creation dates for temporal analysis
- Consider supporting both list and inline tag formats

## Conclusion

Structured notes with front matter enable powerful automation while
maintaining human readability. This balance is essential for sustainable
knowledge management practices.
"""),

        # Long note (1000+ words)
        ("long_detailed.md", """# Comprehensive Guide to Test Fixtures

## Introduction

Test fixtures are a fundamental concept in software testing, providing
consistent, reusable test data that enables reliable and repeatable test
execution. This comprehensive guide explores fixture design, implementation,
and best practices for modern Python testing frameworks.

## Why Fixtures Matter

In complex software systems, tests often require elaborate setup and teardown
procedures. Without proper fixtures, tests become brittle, slow, and difficult
to maintain. Fixtures solve these problems by encapsulating setup logic and
providing clean interfaces for test functions.

### Benefits of Fixtures

1. **Consistency**: Every test starts with known state
2. **Reusability**: Setup code is written once, used everywhere
3. **Maintainability**: Changes to test data happen in one place
4. **Isolation**: Tests don't interfere with each other
5. **Speed**: Setup can be optimised and cached

## Fixture Design Patterns

### Factory Fixtures

Factory fixtures generate test data on demand, allowing tests to specify
exactly what they need. This approach provides flexibility while maintaining
consistency.

### Builder Fixtures

Builder fixtures construct complex objects incrementally, making tests more
readable by expressing intent rather than mechanics.

### Parametrised Fixtures

Parametrised fixtures generate multiple test cases from a single fixture
definition, reducing code duplication while expanding test coverage.

## Implementation Strategies

When implementing fixtures, consider scope, lifetime, and dependencies. Fixtures
can be scoped to functions, classes, modules, or entire test sessions. Choose
the appropriate scope based on setup cost and isolation requirements.

### Function Scope

Function-scoped fixtures run before each test function. This provides maximum
isolation but can be slow if setup is expensive. Use for fixtures that must
be fresh for each test.

### Module Scope

Module-scoped fixtures run once per test module. This improves speed for
expensive setup operations while maintaining reasonable isolation.

### Session Scope

Session-scoped fixtures run once for the entire test session. Use sparingly,
only for truly expensive operations like database migrations or model loading.

## Best Practices

1. Keep fixtures focused and single-purpose
2. Use descriptive fixture names that indicate what they provide
3. Document fixture behaviour and dependencies
4. Avoid fixture interdependencies when possible
5. Clean up resources properly in teardown
6. Use temporary directories and files for file system tests
7. Mock external services to avoid network dependencies
8. Parametrise fixtures to cover multiple scenarios

## Testing Markdown Processing

For markdown processing tools, fixtures should provide diverse content samples:
- Various lengths (short, medium, long)
- Different structures (headings, lists, code blocks)
- Front matter variations (present, absent, malformed)
- Special cases (empty files, Unicode characters, links)

## Conclusion

Well-designed fixtures are the foundation of maintainable test suites. They
enable confident refactoring, catch regressions early, and document expected
behaviour. Invest time in fixture design to reap long-term benefits in test
quality and development velocity.
"""),

        # Note with existing link section
        ("note_with_links.md", """# Note with Existing Links

This note already has an auto-generated links section that should be handled
correctly during updates.

## Related Notes

<!-- AUTO-GENERATED LINKS START -->
- [[short_note]] - Related concept
- [[medium_with_frontmatter]] - Implementation details
<!-- AUTO-GENERATED LINKS END -->

The links above were generated previously and should be replaced or removed
as needed during test execution.
"""),

        # Note with summary block
        ("note_with_summary.md", """# Note with Summary

<!-- AUTO-GENERATED SUMMARY START -->
## Summary

This note demonstrates summary block handling. The summary was generated
by an LLM-based summarisation tool and should be preserved or updated
according to test requirements.
<!-- AUTO-GENERATED SUMMARY END -->

## Content

The actual note content follows the summary block. Processing tools must
correctly handle the presence of existing summary sections.
"""),

        # Empty note (edge case)
        ("empty.md", ""),

        # Malformed YAML front matter
        ("malformed_frontmatter.md", """---
tags: [python, testing
created: 2026-02-09
---

# Malformed Front Matter

This note has invalid YAML (unclosed bracket). Parsers should handle this
gracefully without crashing.
"""),

        # Note without front matter
        ("no_frontmatter.md", """# Simple Note

Just plain markdown content without any YAML front matter. This is a valid
and common note format that should be supported.

## Subsection

Content continues here with normal markdown formatting.
"""),

        # Note with Unicode characters
        ("unicode_content.md", """# Unicode Test Note

This note contains various Unicode characters to test encoding handling:

- Emoji: 🚀 🎉 💡 ✅
- Accented: café, naïve, résumé
- Mathematical: ∑ ∫ √ ∞ ≠
- Arrows: → ← ↑ ↓ ↔
- Currency: £ € ¥ ₹

Proper Unicode handling is essential for international knowledge bases.
"""),
    ]


@pytest.fixture
def temp_vault(tmp_path: Path) -> Path:
    """Create temporary vault directory with sample markdown files.

    Args:
        tmp_path: Pytest's temporary directory fixture

    Returns:
        Path to temporary vault directory
    """
    vault_dir = tmp_path / "test_vault"
    vault_dir.mkdir()

    # Create sample files
    for filename, content in sample_markdown_files():
        file_path = vault_dir / filename
        file_path.write_text(content, encoding="utf-8")

    # Create subdirectory with additional file
    subdir = vault_dir / "subfolder"
    subdir.mkdir()
    (subdir / "nested_note.md").write_text("# Nested Note\n\nContent in subfolder.", encoding="utf-8")

    # Create .metisem directory (should be ignored by file discovery)
    metisem_dir = vault_dir / ".metisem"
    metisem_dir.mkdir()
    (metisem_dir / "cache.npz").write_text("", encoding="utf-8")

    return vault_dir


@pytest.fixture
def sample_files_dict() -> dict:
    """Return dictionary mapping filenames to content for flexible access.

    Returns:
        Dictionary with filename keys and content values
    """
    return dict(sample_markdown_files())
