# /ui_smoke

Perform minimal UI smoke verification using Chrome integration.

## Configuration

**Before executing any steps**, read `.claude/portable_config.local.yaml` to obtain:
- `ui.url` - UI dev server URL to navigate to
- `ui.dev_command` - command to start UI dev server (for prerequisites note)
- `artefacts.verification_dir` - where to save screenshots and logs

If the config file does not exist, STOP with:
```text
ERROR: Missing config file .claude/portable_config.local.yaml
Action: Copy .claude/portable_config.local.example.yaml to .claude/portable_config.local.yaml and configure.
```

## Prerequisites

- Claude Code session started with `--chrome` flag
- Chrome browser open and connected
- UI dev server running (typically via command in `ui.dev_command`)

## Execution Steps

1. **Check Chrome connection**
   - Verify Chrome integration is available
   - If NOT connected: STOP immediately with message:
     ```text
     BLOCKED: Chrome not connected.
     Action: Restart Claude Code with `claude --chrome` and rerun /ui_smoke.
     ```

2. **Prepare output directory**
   - Create `{artefacts.verification_dir}/ui/<YYYYMMDD>/` if not exists
   - Use today's date in YYYYMMDD format

3. **Execute UI journeys** (minimal, deterministic)
   - **Journey 1: App loads**
     - Navigate to URL from `ui.url`
     - Wait for page load
     - Capture screenshot: `01_app_loads.png`
     - Pass if page renders without error
   - **Journey 2: Primary page renders**
     - Verify main content area is visible
     - Capture screenshot: `02_primary_page.png`
     - Pass if expected elements present
   - **Journey 3: Key interaction** (if applicable)
     - Perform one representative interaction (e.g., navigation, search)
     - Capture screenshot: `03_interaction.png`
     - Pass if interaction completes

4. **Write results log**
   - Create `{artefacts.verification_dir}/ui/<YYYYMMDD>/ui_smoke_<HHMM>.md`
   - Format:
     ```markdown
     # UI Smoke Results

     **Date**: YYYY-MM-DD HH:MM
     **Chrome**: Connected

     ---

     ## Journeys

     | # | Journey | Result | Screenshot |
     |---|---------|--------|------------|
     | 1 | App loads | PASS/FAIL | 01_app_loads.png |
     | 2 | Primary page | PASS/FAIL | 02_primary_page.png |
     | 3 | Key interaction | PASS/FAIL/SKIPPED | 03_interaction.png |

     ---

     ## Verdict

     PASS: All journeys completed successfully
     - or -
     FAIL: [first failure reason]
     ```

5. **Return result**
   - Report PASS/FAIL with pointer to log file
   - If FAIL: include first failure reason

## Constraints

- Keep journeys minimal and deterministic
- Do not add new journeys without explicit approval
- Screenshots must be saved before reporting result
- Do not proceed past Chrome check if not connected

## Output

- Screenshots: `{artefacts.verification_dir}/ui/<YYYYMMDD>/*.png`
- Log: `{artefacts.verification_dir}/ui/<YYYYMMDD>/ui_smoke_<HHMM>.md`
- Console: PASS/FAIL with log path
