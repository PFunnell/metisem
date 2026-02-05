"""Test modify_markdown_file to find discrepancy."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from main import modify_markdown_file, MODIFY_DELETED, MODIFY_ERROR

# Create a test file
test_file = Path("test_modify_temp.md")

# Test 1: Add 5 links to clean file
test_file.write_text("# Test\n\nContent here.\n")
links = [Path(f"note{i}.md") for i in range(5)]
result = modify_markdown_file(test_file, links, delete_existing=False)
print(f"Test 1 - Add 5 links to clean file: returned {result}")

# Check what was actually written
text = test_file.read_text()
actual_links = text.count("[[")
print(f"  Actually written: {actual_links} links")
print(f"  Match: {result == actual_links}")

# Test 2: Replace with 3 links (delete_existing=True)
test_file.write_text("# Test\n\nContent.\n<!-- AUTO-GENERATED LINKS START -->\n## Related Notes\n[[old1]]\n[[old2]]\n<!-- AUTO-GENERATED LINKS END -->\n")
links = [Path(f"new{i}.md") for i in range(3)]
result = modify_markdown_file(test_file, links, delete_existing=True)
print(f"\nTest 2 - Replace existing with 3 new links: returned {result}")

text = test_file.read_text()
actual_links = text.count("[[")
print(f"  Actually written: {actual_links} links")
print(f"  Contains 'new0': {'[[new0]]' in text}")
print(f"  Contains 'old1': {'[[old1]]' in text}")
print(f"  Match: {result == actual_links}")

# Test 3: Delete links (no new links to add)
result = modify_markdown_file(test_file, [], delete_existing=True)
print(f"\nTest 3 - Delete links (empty list): returned {result}")

text = test_file.read_text()
actual_links = text.count("[[")
print(f"  Actually written: {actual_links} links")
print(f"  Has link block: {'AUTO-GENERATED LINKS START' in text}")
print(f"  Expected MODIFY_DELETED ({MODIFY_DELETED}): {result == MODIFY_DELETED}")

# Cleanup
test_file.unlink()
print("\n✓ Tests complete")
