#!/usr/bin/env python3
"""
TaskAssignment model for Solmar Workflow Automation Platform.
"""
import uuid
from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import Boolean, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskAssignment(Base):
    """
    TaskAssignment entity representing task assignments to users.
    
    Attributes:
        id: Unique identifier (UUID)
        workflow_instance_id: Reference to workflow instance
        step_id: Step ID in workflow definition
        title: Task title
        description: Task description
        status: Current task status
        assigned_to: User assigned to this task
        completed_by: User who completed the task
        due_date: Task due date
        completed_at: When task was completed
        metadata: JSON metadata for the task
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "task_assignment"
    
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
    
    # Task metadata
    step_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Step ID in workflow definition"
    )
    
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Task title"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Task description"
    )
    
    status: Mapped[TaskStatus] = mapped_column(
        String(20),
        nullable=False,
        default=TaskStatus.PENDING,
        comment="Current task status"
    )
    
    # Foreign keys
    assigned_to: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        comment="User assigned to this task"
    )
    
    completed_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who completed the task"
    )
    
    # Dates
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Task due date"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When task was completed"
    )
    
    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB if Base.metadata.bind and Base.metadata.bind.dialect.name == 'postgresql' else Text,
        nullable=True,
        comment="JSON metadata for the task"
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
    
    # Relationships
    workflow_instance: Mapped["WorkflowInstance"] = relationship(
        "WorkflowInstance",
        back_populates="task_assignments",
        foreign_keys=[workflow_instance_id]
    )
    
    assigned_to_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_to],
        back_populates="assigned_tasks"
    )
    
    completed_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[completed_by],
        back_populates="completed_tasks"
    )
    
    def __repr__(self) -> str:
        """String representation of the TaskAssignment."""
        return f"TaskAssignment(id={self.id!r}, title={self.title!r}, status={self.status!r})"
    
    def to_dict(self) -> dict:
        """Convert TaskAssignment to dictionary representation."""
        return {
            "id": self.id,
            "workflow_instance_id": self.workflow_instance_id,
            "step_id": self.step_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "completed_by": self.completed_by,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if self.due_date and self.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return datetime.utcnow() > self.due_date
        return False
    
    @property
    def is_assignable(self) -> bool:
        """Check if task can be assigned."""
        return self.status in [TaskStatus.PENDING, TaskStatus.BLOCKED]


def create_synthetic_task_assignment(
    workflow_instance_id: str,
    step_id: str,
    title: str,
    status: TaskStatus = TaskStatus.PENDING,
    description: Optional[str] = None,
    assigned_to: Optional[str] = None,
    due_date: Optional[datetime] = None
) -> TaskAssignment:
    """
    Create a synthetic task assignment for testing and seeding.
    
    Args:
        workflow_instance_id: Reference to workflow instance
        step_id: Step ID in workflow definition
        title: Task title
        status: Task status
        description: Task description
        assigned_to: User ID assigned to this task
        due_date: Task due date
    
    Returns:
        TaskAssignment instance
    """
    return TaskAssignment(
        workflow_instance_id=workflow_instance_id,
        step_id=step_id,
        title=title,
        description=description,
        status=status,
        assigned_to=assigned_to,
        due_date=due_date,
        created_at=datetime.utcnow()
    )
