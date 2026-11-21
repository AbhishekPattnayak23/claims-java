# Alembic Migrations for Solmar Workflow Automation Platform

This directory contains database migration scripts managed by Alembic for SQLAlchemy.

## Overview

Alembic is a database migration tool for SQLAlchemy that handles schema changes and data migrations.

## Migration Commands

### Generating a New Migration
```bash
# Generate a new migration from model changes
alembic revision --autogenerate -m "Add new table"

# Generate a new empty migration
alembic revision -m "Add new table"
```

### Applying Migrations
```bash
# Apply all pending migrations
alembic upgrade head

# Apply up to a specific revision
alembic upgrade ae10dc94a5c3

# Downgrade one revision
alembic downgrade -1

# Downgrade to a specific revision
alembic downgrade ae10dc94a5c3
```

### Migration Status
```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show available revisions
alembic heads
```

## Migration Structure

### Directory Layout
```
alembic/
├── README.md          # This file
├── env.py             # Alembic environment configuration
├── script.py.mako     # Migration template
└── versions/          # Migration scripts
    ├── 001_initial_schema.py
    └── 002_add_workflow_audit.py
```

### Version Naming Convention
Migration files follow the pattern:
```
YYYYMMDD_HHMMSS_description.py
```

Example: `20240115_143000_initial_schema.py`

## Development Workflow

1. **Make model changes**: Update SQLAlchemy models in `app/models/`
2. **Generate migration**: `alembic revision --autogenerate -m "Description"`
3. **Review migration**: Check the generated migration file in `versions/`
4. **Apply migration**: `alembic upgrade head`
5. **Test**: Verify the changes work correctly

## Production Deployment

1. **Generate migrations** in development environment
2. **Test migrations** against a staging database
3. **Bundle migrations** with application code
4. **Apply migrations** during deployment using `alembic upgrade head`
5. **Verify** migration success with `alembic current`

## Migration Best Practices

### Data Safety
1. Always backup database before running migrations
2. Test migrations on a copy of production data
3. Include rollback steps in `downgrade()` function

### Performance
1. Use batch operations for large data migrations
2. Add appropriate indexes for performance
3. Consider migration timeouts for large databases

### Version Control
1. Commit migration files to version control
2. Keep migration files in chronological order
3. Document breaking changes in migration comments

## Environment Configuration

The `alembic.ini` and `env.py` files configure:
- Database connection URL
- Migration target metadata
- Logging configuration
- Custom migration options

## Common Issues

### `Target database is not up to date`
Solution: Run `alembic upgrade head`

### `Can't locate revision identified by...`
Solution: Check migration versions and fix with `alembic stamp`

### `No changes detected`
Solution: Ensure models are imported in metadata and alembic can access them

## See Also
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy ORM Documentation](https://docs.sqlalchemy.org/)
- [Project Database Documentation](../docs/database.md)