# /gitsync

Prepare this work package for closure and upstreaming.

## Configuration

**Before executing any steps**, read `.claude/portable_config.local.yaml` to obtain:
- `tests.command` - test execution command
- `workflow.gitsync.check_ci_status` - whether to check CI (default: true)

If the config file does not exist, STOP with:
```text
ERROR: Missing config file .claude/portable_config.local.yaml
Action: Copy .claude/portable_config.local.example.yaml to .claude/portable_config.local.yaml and configure.
```

## Tasks

1. **Run tests**
   - Execute the command from `tests.command` in config
   - If tests fail, STOP and report failures
   - Do not proceed to staging if any tests fail

2. **Review changes**
   - Run `git diff` and summarise the changes at a functional level.
   - Confirm changes match the intended scope of this work package.
   - Call out anything unexpected or incidental.

3. **Check CI status** (if enabled and `gh` available)
   - Run: `gh run list --limit=1 --json conclusion --jq '.[0].conclusion'`
   - If `failure`: warn "Last CI run failed" and confirm before proceeding
   - If `success` or unavailable: continue

4. **Stage and commit**
   - Stage all relevant changes.
   - Generate a concise, accurate commit message consistent with existing conventions.
   - Do not bundle unrelated changes.

5. **Push**
   - Push the branch to origin.
   - Confirm branch name and commit hash.

6. **Post-push summary**
   - Provide a brief summary including:
     - what was changed,
     - why (one sentence),
     - test results (X passed),
     - any notable follow-ups or deferred items.
     - any untracked or modified items outside the scope of the work package.

## Constraints

- Do not modify code beyond what is already staged.
- Do not squash or rebase unless explicitly instructed.
- Do not push if tests are failing; report instead.
- Do not include "generated with" or "co-authored by" references to Claude Code in commit messages.

## Stop

Stop once the push is complete and the summary is provided.
