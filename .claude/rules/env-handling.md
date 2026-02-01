# Environment File Handling

**CRITICAL**: .env files are unrecoverable. Always backup before modifying.

## Before Modifying .env

```bash
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
```

## Rules

- Never overwrite .env directly
- Never copy .env.example over .env (merge instead)
- Read current file before assuming structure
- Test credentials immediately after changes

## Recovery

1. Check `secrets/` for fragments
2. Check password manager
3. Reconstruct from `.env.example`
