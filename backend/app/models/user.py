"""
User model for Solmar Workflow Automation Platform.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base


class User(Base):
    """
    User entity representing system users with authentication and authorization.
    
    Attributes:
        id: Unique identifier (UUID)
        email: User email for authentication (must contain @)
        username: Display name for user
        password_hash: Argon2id hashed password
        role: RBAC role determining permissions
        is_active: Soft delete flag
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "user"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),  # Using String instead of UUID for SQLite compatibility
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email for authentication"
    )
    
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Display name for user"
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Argon2id hashed password"
    )
    
    # RBAC and status
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="agent",
        comment="RBAC role determining permissions"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Soft delete flag"
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
    # These will be added when related models are implemented
    # created_workflow_definitions: Mapped[list["WorkflowDefinition"]] = relationship(
    #     back_populates="created_by_user",
    #     foreign_keys="[WorkflowDefinition.created_by]"
    # )
    # 
    # created_workflow_instances: Mapped[list["WorkflowInstance"]] = relationship(
    #     back_populates="created_by_user",
    #     foreign_keys="[WorkflowInstance.created_by]"
    # )
    # 
    # assigned_approval_requests: Mapped[list["ApprovalRequest"]] = relationship(
    #     back_populates="assigned_to_user",
    #     foreign_keys="[ApprovalRequest.assigned_to]"
    # )
    # 
    # responded_approval_requests: Mapped[list["ApprovalRequest"]] = relationship(
    #     back_populates="responded_by_user",
    #     foreign_keys="[ApprovalRequest.responded_by]"
    # )
    # 
    # assigned_tasks: Mapped[list["TaskAssignment"]] = relationship(
    #     back_populates="assigned_to_user",
    #     foreign_keys="[TaskAssignment.assigned_to]"
    # )
    # 
    # agent_activities: Mapped[list["AgentActivity"]] = relationship(
    #     back_populates="agent",
    #     foreign_keys="[AgentActivity.agent_id]"
    # )
    # 
    # audit_entries: Mapped[list["WorkflowAudit"]] = relationship(
    #     back_populates="performed_by_user",
    #     foreign_keys="[WorkflowAudit.performed_by]"
    # )
    
    def __repr__(self) -> str:
        """String representation of the User."""
        return f"User(id={self.id!r}, email={self.email!r}, username={self.username!r}, role={self.role!r})"
    
    def to_dict(self) -> dict:
        """Convert User to dictionary representation."""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == "admin"
    
    @property
    def is_manager(self) -> bool:
        """Check if user has manager role."""
        return self.role == "manager"
    
    @property
    def is_agent(self) -> bool:
        """Check if user has agent role."""
        return self.role == "agent"


# Create a function for generating synthetic users for testing
def create_synthetic_user(
    email: str,
    username: str,
    password_hash: str = "placeholder_hash",
    role: str = "agent",
    is_active: bool = True
) -> User:
    """
    Create a synthetic user for testing and seeding.
    
    Args:
        email: User email
        username: Display name
        password_hash: Hashed password (default placeholder)
        role: User role
        is_active: Whether user is active
    
    Returns:
        User instance
    """
    return User(
        email=email,
        username=username,
        password_hash=password_hash,
        role=role,
        is_active=is_active,
        created_at=datetime.utcnow()
    )