# Data Contracts

**Canonical reference**: `docs/data_dictionary.md`

ALWAYS consult the data dictionary before writing code that uses models, makes API calls, or writes SQL.

## Protocol

Before writing code that uses models:

1. Read the data dictionary entry for the model
2. Read the model definition source file to confirm current state
3. Check method signatures for parameter names
4. Verify API response models match frontend types
5. Check database column names if writing SQL
6. Follow field names, types, and structures exactly as documented

When creating or modifying models:

- Extend the dictionary without changing frozen entries
- If the dictionary is missing coverage, add it
- Once documented, the dictionary is the canonical reference

## Phase Gate Integration

At checkpoints, verify:
- [ ] Data dictionary updated if models created/modified
- [ ] New fields documented with types and constraints
- [ ] API contracts match implementation

## Freeze Protocol

Models can be marked as "frozen" to prevent breaking changes:

```markdown
## User [FROZEN]
```

Frozen models:
- Cannot have fields removed
- Cannot have field types changed
- Can have new optional fields added
- Require explicit migration plan for breaking changes
