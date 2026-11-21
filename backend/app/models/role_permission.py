#!/usr/bin/env python3
"""
RolePermission model for Solmar Workflow Automation Platform.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base


class RolePermission(Base):
    """
    RolePermission entity representing role-based access control permissions.
    
    Attributes:
        id: Unique identifier (UUID)
        role: RBAC role name (e.g., 'admin', 'manager', 'agent')
        permission: Specific permission string (e.g., 'workflow.create', 'user.read')
        is_granted: Whether permission is granted
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "role_permission"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),  # Using String instead of UUID for SQLite compatibility
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Role and permission fields
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="RBAC role name"
    )
    
    permission: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Specific permission string"
    )
    
    is_granted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether permission is granted"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Record creation timestamp"
    )
    
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
        comment="Last update timestamp"
    )
    
    def __repr__(self) -> str:
        """String representation of the RolePermission."""
        return f"RolePermission(id={self.id!r}, role={self.role!r}, permission={self.permission!r}, is_granted={self.is_granted})"
    
    def to_dict(self) -> dict:
        """Convert RolePermission to dictionary representation."""
        return {
            "id": self.id,
            "role": self.role,
            "permission": self.permission,
            "is_granted": self.is_granted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


def create_default_role_permissions() -> list[RolePermission]:
    """
    Create default role permissions for system roles.
    
    Returns:
        List of RolePermission instances
    """
    default_permissions = [
        # Admin permissions
        ("admin", "user.create", True),
        ("admin", "user.read", True),
        ("admin", "user.update", True),
        ("admin", "user.delete", True),
        ("admin", "workflow.create", True),
        ("admin", "workflow.read", True),
        ("admin", "workflow.update", True),
        ("admin", "workflow.delete", True),
        ("admin", "audit.read", True),
        ("admin", "metrics.read", True),
        ("admin", "system.config", True),
        
        # Manager permissions
        ("manager", "user.read", True),
        ("manager", "workflow.create", True),
        ("manager", "workflow.read", True),
        ("manager", "workflow.update", True),
        ("manager", "audit.read", True),
        ("manager", "metrics.read", True),
        ("manager", "approval.respond", True),
        
        # Agent permissions
        ("agent", "workflow.read", True),
        ("agent", "workflow.create", True),
        ("agent", "task.read", True),
        ("agent", "task.update", True),
        ("agent", "approval.respond", True),
    ]
    
    role_permissions = []
    for role, permission, is_granted in default_permissions:
        role_permission = RolePermission(
            role=role,
            permission=permission,
            is_granted=is_granted,
            created_at=datetime.utcnow()
        )
        role_permissions.append(role_permission)
    
    return role_permissions
