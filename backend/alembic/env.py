#!/usr/bin/env python3
"""
Alembic environment configuration for Solmar Workflow Automation Platform.
Handles database migrations with SQLAlchemy 2.0 async support.
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import context

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database models
from app.db.database import Base
from app.models.user import User
from app.models.role_permission import RolePermission
from app.models.workflow_definition import WorkflowDefinition
from app.models.workflow_instance import WorkflowInstance
from app.models.audit_trail import AuditTrail
from app.models.approval_request import ApprovalRequest
from app.models.task_assignment import TaskAssignment

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for auto-generation
target_metadata = Base.metadata


def get_url() -> str:
    """
    Get database URL from environment or default to SQLite.
    
    Returns:
        Database connection URL
    """
    # First check environment variable
    database_url = os.environ.get("DATABASE_URL")
    
    if database_url:
        return database_url
    
    # Default to SQLite for development
    return "sqlite+aiosqlite:///./solmar.db"


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        configuration = {}
    
    # Override sqlalchemy.url with our dynamic URL
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = AsyncEngine(
        engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection):
    """
    Run migrations synchronously on the given connection.
    
    Args:
        connection: SQLAlchemy connection
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Enable batch mode for SQLite
        render_as_batch=True,
        # Generate include_object function to control which objects are included
        include_object=include_object,
        # Compare type, server_default, and constraints
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def include_object(object, name, type_, reflected, compare_to):
    """
    Include or exclude objects from migration generation.
    
    Args:
        object: SQLAlchemy object
        name: Object name
        type_: Object type ('table', 'column', 'index', 'unique_constraint', 'foreign_key_constraint')
        reflected: Whether object is reflected from database
        compare_to: Object to compare against
        
    Returns:
        True to include object, False to exclude
    """
    # Include all objects by default
    return True


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio
    asyncio.run(run_migrations_online())