# Chrome Setup for UI Smoke Testing

Guide for configuring Chrome integration with Claude Code.

## Starting Claude Code with Chrome

```bash
claude --chrome
```

This enables Claude Code to:
- Connect to a Chrome browser instance
- Navigate to URLs
- Capture screenshots
- Interact with page elements

## How It Works

1. Claude Code launches or connects to Chrome using the Chrome DevTools Protocol
2. Commands like `/ui_smoke` use this connection to automate browser actions
3. Screenshots are captured and saved to your verification directory

## Verification

After starting with `--chrome`, verify connection:
1. The status should indicate Chrome is connected
2. Try a simple navigation command
3. Check that screenshots are being captured

## Common Issues

### Chrome not found

**Symptom**: Error about Chrome not being available

**Solutions**:
- Ensure Chrome is installed in a standard location
- On Windows: Check `C:\Program Files\Google\Chrome\Application\chrome.exe`
- On macOS: Check `/Applications/Google Chrome.app`
- On Linux: Check `/usr/bin/google-chrome` or `/usr/bin/chromium`

### Connection timeout

**Symptom**: Claude Code hangs when starting with `--chrome`

**Solutions**:
- Close all existing Chrome windows
- Kill any background Chrome processes
- Try again with a fresh Chrome installation

### Permission denied

**Symptom**: Cannot capture screenshots or navigate

**Solutions**:
- Ensure Claude Code has permissions to control Chrome
- On macOS: Grant accessibility permissions in System Preferences
- Try running Claude Code with elevated privileges (if appropriate)

## Headless Mode

For CI environments, Chrome can run headlessly:

```bash
# This is typically handled automatically by Claude Code
# when no display is available
```

## Troubleshooting Checklist

- [ ] Chrome installed and accessible from command line
- [ ] Claude Code started with `--chrome` flag
- [ ] No other Chrome debugging sessions active
- [ ] UI dev server running at configured URL
- [ ] Network allows localhost connections
