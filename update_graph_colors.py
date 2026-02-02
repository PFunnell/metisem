"""Update Obsidian graph.json with colour groups for tags.

Reads tags from a tags file and updates the vault's .obsidian/graph.json to assign
distinct colours to each tag in the graph view.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List


# Colour palette for tags (visually distinct colours)
COLOR_PALETTE = [
    "#e74c3c",  # red
    "#3498db",  # blue
    "#2ecc71",  # green
    "#f39c12",  # orange
    "#9b59b6",  # purple
    "#1abc9c",  # teal
    "#e67e22",  # dark orange
    "#34495e",  # dark blue-grey
    "#16a085",  # dark teal
    "#27ae60",  # dark green
    "#2980b9",  # dark blue
    "#8e44ad",  # dark purple
    "#c0392b",  # dark red
    "#d35400",  # burnt orange
    "#7f8c8d",  # grey
    "#f1c40f",  # yellow
    "#e91e63",  # pink
    "#00bcd4",  # cyan
    "#ff5722",  # deep orange
    "#795548",  # brown
]


def load_tags_from_file(tags_file: Path) -> List[str]:
    """Load tag names from tags file.

    Args:
        tags_file: Path to tags file in format "tag_name::description"

    Returns:
        List of tag names
    """
    tags = []
    for line in tags_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '::' in line:
            tag_name = line.split('::', 1)[0].strip()
            if tag_name:
                tags.append(tag_name)
    return tags


def create_color_groups(tags: List[str]) -> List[Dict]:
    """Create colour groups for tags.

    Args:
        tags: List of tag names

    Returns:
        List of colour group dictionaries for graph.json
    """
    color_groups = []
    for i, tag in enumerate(tags):
        color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
        color_groups.append({
            "query": f"tag:#{tag}",
            "color": {
                "a": 1,
                "rgb": int(color.lstrip('#'), 16)
            }
        })
    return color_groups


def update_graph_json(vault_path: Path, color_groups: List[Dict]) -> None:
    """Update or create .obsidian/graph.json with colour groups.

    Args:
        vault_path: Path to Obsidian vault
        color_groups: List of colour group dictionaries
    """
    obsidian_dir = vault_path / ".obsidian"
    graph_file = obsidian_dir / "graph.json"

    # Read existing graph.json or create default
    if graph_file.exists():
        try:
            config = json.loads(graph_file.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            print(f"Warning: Could not parse existing {graph_file}, creating new config")
            config = {}
    else:
        config = {}

    # Update colour groups
    config['colorGroups'] = color_groups

    # Ensure other common settings exist
    if 'collapse-filter' not in config:
        config['collapse-filter'] = False
    if 'search' not in config:
        config['search'] = ''
    if 'showTags' not in config:
        config['showTags'] = True
    if 'showAttachments' not in config:
        config['showAttachments'] = False
    if 'hideUnresolved' not in config:
        config['hideUnresolved'] = False

    # Write back
    obsidian_dir.mkdir(exist_ok=True)
    graph_file.write_text(json.dumps(config, indent=2), encoding='utf-8')
    print(f"Updated {graph_file} with {len(color_groups)} colour groups")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update Obsidian graph.json with tag colour groups"
    )
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--tags-file', required=True, help='Path to tags file')
    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    tags_file = Path(args.tags_file)

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        return

    if not tags_file.exists():
        print(f"Error: Tags file does not exist: {tags_file}")
        return

    # Load tags
    tags = load_tags_from_file(tags_file)
    print(f"Loaded {len(tags)} tags from {tags_file}")

    # Create colour groups
    color_groups = create_color_groups(tags)

    # Update graph.json
    update_graph_json(vault_path, color_groups)

    print("\nColour assignments:")
    for i, tag in enumerate(tags):
        color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
        print(f"  {tag}: {color}")


if __name__ == '__main__':
    main()
