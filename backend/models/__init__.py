"""
Solmar Workflow Automation Platform - Database Models

This module contains SQLAlchemy Base class and common model mixins.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import declared_attr
from sqlalchemy.sql import expression

# Create base class for SQLAlchemy models
Base: DeclarativeMeta = declarative_base()


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamp fields to models."""

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class BaseModel(Base, TimestampMixin):
    """
    Base model class that all application models should inherit from.
    Provides id, created_at, and updated_at fields.
    """
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


# Export public interface
__all__ = ["Base", "BaseModel", "TimestampMixin"]