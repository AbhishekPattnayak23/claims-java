#!/usr/bin/env python3
"""
WorkflowInstance model for Solmar Workflow Automation Platform.
"""
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import Boolean, String, DateTime, Text, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base


class WorkflowStatus(str, Enum):
    """Workflow instance status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class WorkflowInstance(Base):
    """
    WorkflowInstance entity representing a running instance of a workflow.
    
    Attributes:
        id: Unique identifier (UUID)
        definition_id: Reference to workflow definition
        name: Instance name (can override definition name)
        status: Current status of workflow instance
        current_step: Current step identifier
        context_data: JSON context data for workflow execution
        created_by: User who started this workflow instance
        started_at: When the workflow was started
        completed_at: When the workflow was completed
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "workflow_instance"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),  # Using String instead of UUID for SQLite compatibility
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Foreign key to workflow definition
    definition_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workflow_definition.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to workflow definition"
    )
    
    # Instance metadata
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="Instance name (can override definition name)"
    )
    
    status: Mapped[WorkflowStatus] = mapped_column(
        SQLEnum(WorkflowStatus),
        nullable=False,
        default=WorkflowStatus.DRAFT,
        comment="Current status of workflow instance"
    )
    
    current_step: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Current step identifier"
    )
    
    # JSON context data
    context_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB if Base.metadata.bind and Base.metadata.bind.dialect.name == 'postgresql' else Text,
        nullable=False,
        default=lambda: {},
        comment="JSON context data for workflow execution"
    )
    
    # Foreign keys
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who started this workflow instance"
    )
    
    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When the workflow was started"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When the workflow was completed"
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
    definition: Mapped["WorkflowDefinition"] = relationship(
        "WorkflowDefinition",
        back_populates="instances",
        foreign_keys=[definition_id]
    )
    
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_workflow_instances"
    )
    
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(
        "ApprovalRequest",
        back_populates="workflow_instance",
        cascade="all, delete-orphan"
    )
    
    task_assignments: Mapped[list["TaskAssignment"]] = relationship(
        "TaskAssignment",
        back_populates="workflow_instance",
        cascade="all, delete-orphan"
    )
    
    audit_entries: Mapped[list["WorkflowAudit"]] = relationship(
        "WorkflowAudit",
        back_populates="workflow_instance",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of the WorkflowInstance."""
        return f"WorkflowInstance(id={self.id!r}, name={self.name!r}, status={self.status!r}, definition_id={self.definition_id!r})"
    
    def to_dict(self) -> dict:
        """Convert WorkflowInstance to dictionary representation."""
        return {
            "id": self.id,
            "definition_id": self.definition_id,
            "name": self.name,
            "status": self.status.value,
            "current_step": self.current_step,
            "context_data": self.context_data,
            "created_by": self.created_by,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate workflow duration in seconds if completed."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_active(self) -> bool:
        """Check if workflow instance is currently active."""
        return self.status == WorkflowStatus.ACTIVE
    
    @property
    def is_completed(self) -> bool:
        """Check if workflow instance is completed."""
        return self.status == WorkflowStatus.COMPLETED


def create_synthetic_workflow_instance(
    definition_id: str,
    name: str,
    status: WorkflowStatus = WorkflowStatus.ACTIVE,
    current_step: Optional[str] = None,
    context_data: Optional[Dict[str, Any]] = None,
    created_by: Optional[str] = None
) -> WorkflowInstance:
    """
    Create a synthetic workflow instance for testing and seeding.
    
    Args:
        definition_id: Reference to workflow definition
        name: Instance name
        status: Workflow status
        current_step: Current step identifier
        context_data: Context data for workflow execution
        created_by: User ID who started this workflow
    
    Returns:
        WorkflowInstance instance
    """
    if context_data is None:
        context_data = {
            "customer": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "account_type": "premium"
            },
            "order": {
                "id": "ORD-001",
                "total": 1250.00,
                "currency": "USD"
            }
        }
    
    instance = WorkflowInstance(
        definition_id=definition_id,
        name=name,
        status=status,
        current_step=current_step,
        context_data=context_data,
        created_by=created_by,
        created_at=datetime.utcnow()
    )
    
    if status == WorkflowStatus.ACTIVE:
        instance.started_at = datetime.utcnow()
    elif status == WorkflowStatus.COMPLETED:
        instance.started_at = datetime.utcnow()
        instance.completed_at = datetime.utcnow()
    
    return instance
