# Diagnostic Protocol

Before fixes: STOP -> Diagnose -> Fix root cause.

## Steps

1. Check existing solutions in scripts/, docs/
2. Verify assumptions (shell type, .env, Python path)
3. Root cause vs symptom
4. Principled fix (no workarounds)

## Quick Reference

| Symptom | Check |
|---------|-------|
| DATABASE_URL not set | load_dotenv() missing |
| Command not found | Full path in config |
| Shell syntax error | bash vs PowerShell |
| Module not found | Correct Python env |
