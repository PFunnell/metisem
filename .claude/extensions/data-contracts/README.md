# Data Contracts Extension

Schema governance for projects with data models, APIs, or databases.

## What This Extension Does

- Enforces data dictionary consultation before writing model code
- Provides template for documenting data structures
- Integrates with phase gates to track model changes
- Prevents drift between documentation and implementation

## When to Use

**Install if**:
- Project has multiple data models (User, Order, Product, etc.)
- APIs with request/response contracts
- Database schemas that must match code
- Frontend/backend type synchronization needed

**Skip if**:
- Simple scripts without structured data
- Projects with auto-generated documentation
- Single-file utilities

## Installation

### 1. Copy the rule file

```bash
cp .claude/extensions/data-contracts/data-contracts.md .claude/rules/
```

### 2. Create data dictionary

```bash
cp .claude/extensions/data-contracts/dictionary.template.md docs/data_dictionary.md
```

### 3. Update CLAUDE.md (optional)

Add a reference to the data dictionary in your project's CLAUDE.md:

```markdown
## Data Dictionary

Consult `docs/data_dictionary.md` before using models or writing SQL.
```

## Usage

### Before writing model code

1. Read the data dictionary entry for the model
2. Read the model source file to confirm current state
3. Check method signatures and field types
4. Verify documentation matches implementation

### When creating new models

1. Add the model to the data dictionary first
2. Document all fields with types and constraints
3. Then implement the model in code
4. Verify implementation matches documentation

### At phase gates

The `/phase_complete` and `/implement_plan` commands will remind about:
- Updating the data dictionary when models change
- Checking for drift between docs and code

## Dictionary Format

See `dictionary.template.md` for the recommended structure:

```markdown
## ModelName

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK | Auto-generated |
| name | string | NOT NULL, max 255 | Display name |
| created_at | datetime | NOT NULL | UTC timestamp |
```

## Benefits

- **Single source of truth**: Dictionary is canonical reference
- **Prevents drift**: Code must match documentation
- **Onboarding**: New developers understand data model quickly
- **API contracts**: Frontend and backend stay synchronized
