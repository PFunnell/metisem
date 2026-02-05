#!/usr/bin/env python
"""Apply Kelly's 22 colours of maximum contrast to Obsidian graph.json.

This script uses Kenneth Kelly's 22 colors of maximum contrast (1965) to provide
optimal visual distinction for tag colour groups in Obsidian's graph view.

References:
- Kelly, K. L. (1965). "Twenty-Two Colors of Maximum Contrast". Color Engineering, 3:26-27.
- GitHub: https://gist.github.com/ollieglass/f6ddd781eeae1d24e391265432297538
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


# Kelly's 22 colours of maximum contrast (Kenneth Kelly, 1965)
# Ordered by perceptual contrast: each colour maximally contrasts with previous colours
# Source: https://gist.github.com/ollieglass/f6ddd781eeae1d24e391265432297538
KELLY_22_PALETTE = {
    'white': '#F2F3F4',          # Near-white
    'black': '#222222',          # Near-black
    'yellow': '#F3C300',         # Vivid yellow
    'purple': '#875692',         # Strong purple
    'orange': '#F38400',         # Vivid orange
    'light_blue': '#A1CAF1',     # Very light blue
    'red': '#BE0032',            # Vivid red
    'buff': '#C2B280',           # Grayish yellow
    'gray': '#848482',           # Medium gray
    'green': '#008856',          # Vivid green
    'purplish_pink': '#E68FAC',  # Strong purplish pink
    'blue': '#0067A5',           # Strong blue
    'yellowish_pink': '#F99379', # Strong yellowish pink
    'violet': '#604E97',         # Strong violet
    'orange_yellow': '#F6A600',  # Vivid orange yellow
    'purplish_red': '#B3446C',   # Strong purplish red
    'greenish_yellow': '#DCD300', # Vivid greenish yellow
    'reddish_brown': '#882D17',  # Strong reddish brown
    'yellow_green': '#8DB600',   # Vivid yellow green
    'yellowish_brown': '#654522', # Deep yellowish brown
    'reddish_orange': '#E25822', # Vivid reddish orange
    'olive_green': '#2B3D26'     # Dark olive green
}


def detect_theme(vault_path: Path, theme_flag: str = None) -> str:
    """Detect Obsidian theme (light or dark).

    Checks in order:
    1. --theme flag if provided
    2. .obsidian/appearance.json for theme setting
    3. Defaults to 'dark' if uncertain (safer for black omission)

    Args:
        vault_path: Path to Obsidian vault
        theme_flag: Optional theme override from CLI

    Returns:
        'light' or 'dark'
    """
    if theme_flag:
        return theme_flag

    appearance_file = vault_path / '.obsidian' / 'appearance.json'
    if appearance_file.exists():
        try:
            config = json.loads(appearance_file.read_text(encoding='utf-8'))
            # Obsidian: 'default' theme is light, everything else is dark
            theme = config.get('theme', 'obsidian')
            return 'light' if theme == 'default' else 'dark'
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not parse appearance.json: {e}")

    logger.info("Theme not detected, defaulting to 'dark'")
    return 'dark'


def load_tags_from_file(tags_file: Path) -> List[str]:
    """Load tag names from tags file.

    Args:
        tags_file: Path to tags file in format "tag_name::description"

    Returns:
        List of tag names sorted alphabetically
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

    # Sort alphabetically for predictable, reproducible colour assignment
    return sorted(tags)


def create_color_groups(tags: List[str], theme: str, preview: bool = False) -> List[Dict]:
    """Create colour groups for tags using Kelly's palette.

    Args:
        tags: List of tag names (should be sorted)
        theme: 'light' or 'dark' (determines which colour to omit)
        preview: If True, print colour assignments

    Returns:
        List of colour group dictionaries for graph.json
    """
    # Omit black or white based on theme
    palette = KELLY_22_PALETTE.copy()
    if theme == 'dark':
        del palette['black']
        omitted = 'black (#222222)'
    else:
        del palette['white']
        omitted = 'white (#F2F3F4)'

    colors = list(palette.values())  # 21 colours remaining

    logger.info(f"Theme: {theme} - Omitting {omitted}")
    logger.info(f"Using {len(colors)} colours from Kelly's palette")

    # Warn if more tags than colours
    if len(tags) > len(colors):
        logger.warning(f"{len(tags)} tags exceed Kelly's {len(colors)} colours. Colours will repeat.")

    # Create colour groups
    color_groups = []
    for i, tag in enumerate(tags):
        color_hex = colors[i % len(colors)]  # Cycle if >21 tags
        color_int = int(color_hex.lstrip('#'), 16)

        color_groups.append({
            'query': f'tag:#{tag}',
            'color': {
                'a': 1,
                'rgb': color_int
            }
        })

        if preview:
            # Get colour name for preview
            color_name = [k for k, v in palette.items() if v == color_hex][0]
            print(f"  {tag}: {color_hex} ({color_name})")

    return color_groups


def update_graph_json(vault_path: Path, color_groups: List[Dict], backup: bool = True) -> None:
    """Update or create .obsidian/graph.json with colour groups.

    Args:
        vault_path: Path to Obsidian vault
        color_groups: List of colour group dictionaries
        backup: If True, create backup of existing graph.json
    """
    obsidian_dir = vault_path / '.obsidian'
    graph_file = obsidian_dir / 'graph.json'

    # Backup existing file
    if backup and graph_file.exists():
        backup_file = graph_file.with_suffix('.json.backup')
        backup_file.write_text(graph_file.read_text(encoding='utf-8'), encoding='utf-8')
        logger.info(f"Backed up existing graph.json to {backup_file.name}")

    # Read existing graph.json or create default
    if graph_file.exists():
        try:
            config = json.loads(graph_file.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            logger.warning(f"Could not parse existing {graph_file}, creating new config")
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
    logger.info(f"Updated {graph_file} with {len(color_groups)} colour groups")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Apply Kelly's 22 colours of maximum contrast to Obsidian graph.json"
    )
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--tags-file', required=True, help='Path to tags file')
    parser.add_argument('--theme', choices=['light', 'dark'],
                        help='Theme override (light or dark). Auto-detected from appearance.json if not specified.')
    parser.add_argument('--preview', action='store_true',
                        help='Preview colour assignments without modifying graph.json')
    parser.add_argument('--no-backup', action='store_true',
                        help='Skip backup of existing graph.json')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s'
    )

    vault_path = Path(args.vault_path)
    tags_file = Path(args.tags_file)

    if not vault_path.exists():
        logger.error(f"Vault path does not exist: {vault_path}")
        return

    if not tags_file.exists():
        logger.error(f"Tags file does not exist: {tags_file}")
        return

    # Detect theme
    theme = detect_theme(vault_path, args.theme)

    # Load tags
    tags = load_tags_from_file(tags_file)
    logger.info(f"Loaded {len(tags)} tags from {tags_file}")

    if not tags:
        logger.error("No tags found in tags file")
        return

    # Create colour groups
    logger.info("\nColour assignments:")
    color_groups = create_color_groups(tags, theme, preview=True)

    # Update graph.json unless preview mode
    if args.preview:
        logger.info("\n[PREVIEW MODE] No changes made to graph.json")
    else:
        update_graph_json(vault_path, color_groups, backup=not args.no_backup)
        logger.info("\nDone! Reload Obsidian to see the new colours in graph view.")


if __name__ == '__main__':
    main()
