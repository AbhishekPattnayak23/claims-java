"""
Solmar Workflow Automation Platform - FastAPI Application

This module initializes the FastAPI application with database configuration,
dependency injection, and middleware setup.
"""

import os
from typing import Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./solmar.db")
# Support PostgreSQL with asyncpg for async operations
if DATABASE_URL.startswith("postgresql"):
    # Convert sync URL to async URL if needed
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# SQLAlchemy engine configuration
engine_kwargs: Dict[str, Any] = {
    "echo": False,  # Set to True for SQL logging
    "poolclass": QueuePool,
    "pool_size": 10,
    "max_overflow": 20,
    "pool_recycle": 3600,  # Recycle connections after 1 hour
}

if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
        "poolclass": None,  # SQLite doesn't support connection pooling
    })

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, **engine_kwargs)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base class
Base = declarative_base()

# FastAPI application instance
app = FastAPI(
    title="Solmar Workflow Automation Platform API",
    description="Backend API for Solmar workflow automation platform",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Database dependency
def get_db():
    """
    Database session dependency for FastAPI routes.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Export public interface
__all__ = [
    "app",
    "Base",
    "SessionLocal",
    "get_db",
    "engine",
]