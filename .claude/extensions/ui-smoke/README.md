# UI Smoke Extension

Browser-based UI verification for web applications.

## What This Extension Does

- Provides `/ui_smoke` command for manual UI verification
- Integrates with phase gates to require UI verification when UI files change
- Captures screenshots as evidence of UI state
- Blocks commits when UI changes are unverified

## Prerequisites

1. **Chrome browser** installed on your system
2. **Claude Code** started with the `--chrome` flag:
   ```bash
   claude --chrome
   ```
3. **UI dev server** running (e.g., `npm run dev`)

## Installation

### 1. Copy the command file

```bash
cp .claude/extensions/ui-smoke/ui_smoke.md .claude/commands/
```

### 2. Update settings.local.json

Add permission for the skill:

```json
{
  "permissions": {
    "allow": [
      "Skill(ui_smoke)"
    ]
  }
}
```

### 3. Configure portable_config.local.yaml

Enable UI settings:

```yaml
ui:
  enabled: true
  root: "ui/"                    # Your UI source directory
  url: "http://localhost:3000"   # Dev server URL
  dev_command: "npm run dev"     # Command to start dev server
```

### 4. Create verification directory

```bash
mkdir -p docs/verification/ui
```

## Usage

### Manual verification

Run when you want to verify UI state:

```text
/ui_smoke
```

### Automatic verification

When `ui.enabled: true`, the phase gate commands (`/phase_complete`, `/implement_plan`) automatically:
1. Detect if files under `ui.root` have changed
2. Check if Chrome is connected
3. Run `/ui_smoke` if UI changed and Chrome available
4. Block if UI changed but Chrome not connected

## Output

### Screenshots

Saved to: `{verification_dir}/ui/YYYYMMDD/`
- `01_app_loads.png` - Initial page load
- `02_primary_page.png` - Main content area
- `03_interaction.png` - After key interaction (if applicable)

### Log file

Saved to: `{verification_dir}/ui/YYYYMMDD/ui_smoke_HHMM.md`

Contains:
- Timestamp and Chrome connection status
- Journey results table
- Pass/fail verdict

## Troubleshooting

### "Chrome not connected"

1. Ensure Claude Code was started with `--chrome` flag
2. Check Chrome is running and accessible
3. Restart Claude Code: `claude --chrome`

### Screenshots not captured

1. Ensure dev server is running at configured URL
2. Check browser console for errors
3. Verify UI renders without JavaScript errors

### Phase gate blocked on UI changes

This is intentional. Options:
1. Start Chrome and verify UI: `claude --chrome`
2. If UI changes are unrelated to your work, commit separately first
3. Disable UI verification temporarily (not recommended)

## Customization

### Adding journeys

Edit `ui_smoke.md` to add custom verification steps:

```markdown
- **Journey 4: Custom check**
  - Navigate to /custom-page
  - Verify element with selector ".custom-element"
  - Capture screenshot: `04_custom.png`
```

### Different dev server URL

Update `ui.url` in your config for different environments.
