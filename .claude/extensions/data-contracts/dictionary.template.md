# Data Dictionary

Canonical reference for all data models in this project.

**Last updated**: YYYY-MM-DD

---

## How to Use This Document

1. **Before coding**: Read the model entry before writing code that uses it
2. **When creating models**: Add entry here first, then implement
3. **When modifying**: Update this document alongside code changes
4. **At phase gates**: Verify dictionary matches implementation

---

## Model Index

| Model | Status | Description |
|-------|--------|-------------|
| [User](#user) | Active | System user accounts |
| [Example](#example) | Template | Copy this for new models |

---

## User

System user accounts.

**Source**: `src/models/user.py`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK | Auto-generated |
| email | string | UNIQUE, NOT NULL, max 255 | Login identifier |
| name | string | NOT NULL, max 255 | Display name |
| created_at | datetime | NOT NULL | UTC timestamp |
| updated_at | datetime | NOT NULL | UTC timestamp, auto-update |

### Relationships

- Has many: (none)
- Belongs to: (none)

### API Representation

```json
{
  "id": "uuid",
  "email": "string",
  "name": "string",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

---

## Example

Copy this template for new models.

**Source**: `src/models/example.py`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK | Auto-generated |
| field_name | type | constraints | description |

### Relationships

- Has many: RelatedModel
- Belongs to: ParentModel

### API Representation

```json
{
  "id": "uuid",
  "field_name": "value"
}
```

### Notes

- Any special behavior or business rules
- Migration history if applicable

---

## Changelog

| Date | Model | Change | Author |
|------|-------|--------|--------|
| YYYY-MM-DD | User | Initial creation | name |
