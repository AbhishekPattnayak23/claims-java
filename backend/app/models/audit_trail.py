#!/usr/bin/env python3
"""
AuditTrail model for Solmar Workflow Automation Platform.
"""
import uuid
from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base


class AuditAction(str, Enum):
    """Audit action enumeration."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"
    COMPLETE = "complete"
    CANCEL = "cancel"
    LOGIN = "login"
    LOGOUT = "logout"


class AuditTrail(Base):
    """
    AuditTrail entity representing system audit logs.
    
    Attributes:
        id: Unique identifier (UUID)
        entity_type: Type of entity audited (e.g., 'user', 'workflow', 'approval')
        entity_id: ID of the audited entity
        action: Action performed
        performed_by: User who performed the action
        performed_at: When the action was performed
        changes: JSON representation of changes
        ip_address: IP address of the requester
        user_agent: User agent string
        created_at: Record creation timestamp
    """
    __tablename__ = "audit_trail"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),  # Using String instead of UUID for SQLite compatibility
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Audit metadata
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of entity audited"
    )
    
    entity_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="ID of the audited entity"
    )
    
    action: Mapped[AuditAction] = mapped_column(
        String(50),
        nullable=False,
        comment="Action performed"
    )
    
    # Foreign key
    performed_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who performed the action"
    )
    
    performed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="When the action was performed"
    )
    
    # Change data
    changes: Mapped[Optional[dict]] = mapped_column(
        JSONB if Base.metadata.bind and Base.metadata.bind.dialect.name == 'postgresql' else Text,
        nullable=True,
        comment="JSON representation of changes"
    )
    
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="IP address of the requester"
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="User agent string"
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Record creation timestamp"
    )
    
    # Relationships
    performed_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[performed_by],
        back_populates="audit_entries"
    )
    
    def __repr__(self) -> str:
        """String representation of the AuditTrail."""
        return f"AuditTrail(id={self.id!r}, entity_type={self.entity_type!r}, entity_id={self.entity_id!r}, action={self.action!r})"
    
    def to_dict(self) -> dict:
        """Convert AuditTrail to dictionary representation."""
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "performed_by": self.performed_by,
            "performed_at": self.performed_at.isoformat() if self.performed_at else None,
            "changes": self.changes,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


def create_synthetic_audit_trail(
    entity_type: str,
    entity_id: str,
    action: AuditAction,
    performed_by: Optional[str] = None,
    changes: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AuditTrail:
    """
    Create a synthetic audit trail entry for testing and seeding.
    
    Args:
        entity_type: Type of entity audited
        entity_id: ID of the audited entity
        action: Action performed
        performed_by: User ID who performed the action
        changes: JSON representation of changes
        ip_address: IP address of the requester
        user_agent: User agent string
    
    Returns:
        AuditTrail instance
    """
    if changes is None:
        changes = {
            "old_values": {"status": "pending"},
            "new_values": {"status": "approved"},
            "changed_fields": ["status"]
        }
    
    return AuditTrail(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        performed_by=performed_by,
        changes=changes,
        ip_address=ip_address or "192.168.1.1",
        user_agent=user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        performed_at=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
