#!/usr/bin/env python3
"""
ApprovalRequest model for Solmar Workflow Automation Platform.
"""
import uuid
from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import Boolean, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base


class ApprovalStatus(str, Enum):
    """Approval request status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class ApprovalRequest(Base):
    """
    ApprovalRequest entity representing approval requests in workflows.
    
    Attributes:
        id: Unique identifier (UUID)
        workflow_instance_id: Reference to workflow instance
        step_id: Step ID in workflow definition
        status: Current approval status
        requested_by: User who requested approval
        assigned_to: User assigned to respond
        responded_by: User who responded
        response_notes: Notes from responder
        response_data: JSON response data
        requested_at: When approval was requested
        responded_at: When approval was responded to
        deadline_at: Deadline for response
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "approval_request"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),  # Using String instead of UUID for SQLite compatibility
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Foreign key to workflow instance
    workflow_instance_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workflow_instance.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to workflow instance"
    )
    
    # Approval metadata
    step_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Step ID in workflow definition"
    )
    
    status: Mapped[ApprovalStatus] = mapped_column(
        String(20),
        nullable=False,
        default=ApprovalStatus.PENDING,
        comment="Current approval status"
    )
    
    # Foreign keys
    requested_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who requested approval"
    )
    
    assigned_to: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        comment="User assigned to respond"
    )
    
    responded_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who responded"
    )
    
    # Response data
    response_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notes from responder"
    )
    
    response_data: Mapped[Optional[dict]] = mapped_column(
        JSONB if Base.metadata.bind and Base.metadata.bind.dialect.name == 'postgresql' else Text,
        nullable=True,
        comment="JSON response data"
    )
    
    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="When approval was requested"
    )
    
    responded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When approval was responded to"
    )
    
    deadline_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Deadline for response"
    )
    
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
    
    # Relationships
    workflow_instance: Mapped["WorkflowInstance"] = relationship(
        "WorkflowInstance",
        back_populates="approval_requests",
        foreign_keys=[workflow_instance_id]
    )
    
    requested_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[requested_by],
        back_populates="assigned_approval_requests"
    )
    
    assigned_to_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_to],
        back_populates="assigned_approval_requests"
    )
    
    responded_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[responded_by],
        back_populates="responded_approval_requests"
    )
    
    def __repr__(self) -> str:
        """String representation of the ApprovalRequest."""
        return f"ApprovalRequest(id={self.id!r}, status={self.status!r}, step_id={self.step_id!r})"
    
    def to_dict(self) -> dict:
        """Convert ApprovalRequest to dictionary representation."""
        return {
            "id": self.id,
            "workflow_instance_id": self.workflow_instance_id,
            "step_id": self.step_id,
            "status": self.status,
            "requested_by": self.requested_by,
            "assigned_to": self.assigned_to,
            "responded_by": self.responded_by,
            "response_notes": self.response_notes,
            "response_data": self.response_data,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "deadline_at": self.deadline_at.isoformat() if self.deadline_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def is_pending(self) -> bool:
        """Check if approval request is pending."""
        return self.status == ApprovalStatus.PENDING
    
    @property
    def is_overdue(self) -> bool:
        """Check if approval request is overdue."""
        if self.deadline_at:
            return datetime.utcnow() > self.deadline_at and self.status == ApprovalStatus.PENDING
        return False


def create_synthetic_approval_request(
    workflow_instance_id: str,
    step_id: str,
    status: ApprovalStatus = ApprovalStatus.PENDING,
    requested_by: Optional[str] = None,
    assigned_to: Optional[str] = None,
    responded_by: Optional[str] = None,
    response_notes: Optional[str] = None,
    deadline_at: Optional[datetime] = None
) -> ApprovalRequest:
    """
    Create a synthetic approval request for testing and seeding.
    
    Args:
        workflow_instance_id: Reference to workflow instance
        step_id: Step ID in workflow definition
        status: Approval status
        requested_by: User ID who requested approval
        assigned_to: User ID assigned to respond
        responded_by: User ID who responded
        response_notes: Notes from responder
        deadline_at: Deadline for response
    
    Returns:
        ApprovalRequest instance
    """
    approval_request = ApprovalRequest(
        workflow_instance_id=workflow_instance_id,
        step_id=step_id,
        status=status,
        requested_by=requested_by,
        assigned_to=assigned_to,
        responded_by=responded_by,
        response_notes=response_notes,
        requested_at=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    if deadline_at:
        approval_request.deadline_at = deadline_at
    
    if status != ApprovalStatus.PENDING:
        approval_request.responded_at = datetime.utcnow()
    
    return approval_request
