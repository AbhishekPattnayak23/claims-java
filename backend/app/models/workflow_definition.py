#!/usr/bin/env python3
"""
WorkflowDefinition model for Solmar Workflow Automation Platform.
"""
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Boolean, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base


class WorkflowDefinition(Base):
    """
    WorkflowDefinition entity representing workflow templates.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Workflow name
        description: Detailed workflow description
        version: Version number (starting at 1)
        status: Current status ('draft', 'active', 'archived')
        steps: JSON configuration of workflow steps
        triggers: JSON configuration of workflow triggers
        rules: JSON configuration of business rules
        created_by: User who created this workflow
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "workflow_definition"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),  # Using String instead of UUID for SQLite compatibility
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Workflow metadata
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="Workflow name"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed workflow description"
    )
    
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Version number"
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        comment="Current status ('draft', 'active', 'archived')"
    )
    
    # JSON configuration fields
    steps: Mapped[Dict[str, Any]] = mapped_column(
        JSONB if Base.metadata.bind and Base.metadata.bind.dialect.name == 'postgresql' else Text,
        nullable=False,
        default=lambda: {"steps": [], "transitions": []},
        comment="JSON configuration of workflow steps"
    )
    
    triggers: Mapped[Dict[str, Any]] = mapped_column(
        JSONB if Base.metadata.bind and Base.metadata.bind.dialect.name == 'postgresql' else Text,
        nullable=True,
        default=lambda: {"triggers": []},
        comment="JSON configuration of workflow triggers"
    )
    
    rules: Mapped[Dict[str, Any]] = mapped_column(
        JSONB if Base.metadata.bind and Base.metadata.bind.dialect.name == 'postgresql' else Text,
        nullable=True,
        default=lambda: {"rules": []},
        comment="JSON configuration of business rules"
    )
    
    # Foreign keys
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who created this workflow"
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
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_workflow_definitions"
    )
    
    instances: Mapped[list["WorkflowInstance"]] = relationship(
        "WorkflowInstance",
        back_populates="definition",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of the WorkflowDefinition."""
        return f"WorkflowDefinition(id={self.id!r}, name={self.name!r}, version={self.version!r}, status={self.status!r})"
    
    def to_dict(self) -> dict:
        """Convert WorkflowDefinition to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "status": self.status,
            "steps": self.steps,
            "triggers": self.triggers,
            "rules": self.rules,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def step_count(self) -> int:
        """Number of steps in this workflow."""
        if isinstance(self.steps, dict) and "steps" in self.steps:
            return len(self.steps["steps"])
        return 0
    
    @property
    def is_active(self) -> bool:
        """Check if workflow definition is active."""
        return self.status == "active"


def create_synthetic_workflow_definition(
    name: str,
    description: Optional[str] = None,
    version: int = 1,
    status: str = "active",
    steps: Optional[Dict[str, Any]] = None,
    created_by: Optional[str] = None
) -> WorkflowDefinition:
    """
    Create a synthetic workflow definition for testing and seeding.
    
    Args:
        name: Workflow name
        description: Workflow description
        version: Version number
        status: Workflow status
        steps: Workflow steps configuration
        created_by: User ID who created this workflow
    
    Returns:
        WorkflowDefinition instance
    """
    if steps is None:
        steps = {
            "steps": [
                {
                    "id": "step_1",
                    "name": "Initiate Request",
                    "type": "manual",
                    "role": "agent",
                    "timeout_minutes": 60
                },
                {
                    "id": "step_2",
                    "name": "Manager Approval",
                    "type": "approval",
                    "role": "manager",
                    "timeout_minutes": 120
                },
                {
                    "id": "step_3",
                    "name": "Complete Processing",
                    "type": "automated",
                    "role": "system",
                    "timeout_minutes": None
                }
            ],
            "transitions": [
                {"from": "step_1", "to": "step_2", "condition": "always"},
                {"from": "step_2", "to": "step_3", "condition": "approved"}
            ]
        }
    
    return WorkflowDefinition(
        name=name,
        description=description,
        version=version,
        status=status,
        steps=steps,
        triggers={"triggers": [{"type": "manual", "role": "agent"}]},
        rules={"rules": [{"type": "approval_threshold", "value": 1000}]},
        created_by=created_by,
        created_at=datetime.utcnow()
    )
