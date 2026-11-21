"""
Solmar Workflow Automation Platform - User Model

This module contains the User model for authentication and user management.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, String, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from . import BaseModel


class UserRole(enum.Enum):
    """Enumeration of user roles in the system."""
    
    ADMIN = "admin"
    SALES_AGENT = "sales_agent"
    OPERATIONS_MANAGER = "operations_manager"
    SYSTEM_ADMINISTRATOR = "system_administrator"


class User(BaseModel):
    """
    User model representing system users with authentication capabilities.
    
    Attributes:
        id: Primary key identifier
        email: Unique email address
        username: Unique username for display
        password_hash: Hashed password (bcrypt/argon2)
        role: User role (enum)
        is_active: Whether the user account is active
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
    """
    
    __tablename__ = "users"
    
    # Core user fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.SALES_AGENT)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Optional fields
    full_name = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)
    department = Column(String(100), nullable=True)
    
    # Relationships will be added later
    # workflow_instances = relationship("WorkflowInstance", back_populates="owner")
    # audit_trails = relationship("AuditTrail", back_populates="user")
    
    def __repr__(self) -> str:
        """Return string representation of the User."""
        return f"<User(id={self.id}, email={self.email}, role={self.role.value})>"
    
    def to_dict(self) -> dict:
        """Convert user instance to dictionary excluding sensitive information."""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "role": self.role.value,
            "is_active": self.is_active,
            "full_name": self.full_name,
            "phone_number": self.phone_number,
            "department": self.department,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Export UserRole for use in schemas and API
__all__ = ["User", "UserRole"]