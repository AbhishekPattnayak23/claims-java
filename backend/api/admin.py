"""
Admin API endpoints for Solmar Workflow Automation Platform.
Provides administrative functions for user management, workflow management,
and system configuration with RBAC protection.
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..app.db.database import get_db_session
from ..app.models.user import User, UserRole, UserStatus
from ..app.models.role_permission import RolePermission
from ..app.models.workflow_definition import WorkflowDefinition
from ..app.models.workflow_instance import WorkflowInstance, WorkflowStatus
from ..app.models.approval_request import ApprovalRequest, ApprovalStatus
from ..app.models.task_assignment import TaskAssignment, TaskStatus
from ..app.models.audit_trail import AuditTrail, AuditAction
from ..app.schemas.admin import (
    UserUpdateRequest,
    UserResponse,
    UsersListResponse,
    UserStats,
    RoleAssignmentRequest,
    WorkflowDefinitionUpdateRequest,
    WorkflowDefinitionResponse,
    WorkflowInstanceResponse,
    SystemStatsResponse,
    PaginationParams,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin_role():
    """Dependency to require admin role for admin endpoints."""
    # TODO: Implement actual JWT validation and role checking
    # For now, we'll assume the user is authenticated and has admin role
    return True


@router.get("/users", response_model=UsersListResponse)
async def list_users(
    db: AsyncSession = Depends(get_db_session),
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    status: Optional[UserStatus] = Query(None, description="Filter by user status"),
    email_contains: Optional[str] = Query(None, description="Filter by email contains"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    _admin: bool = Depends(require_admin_role),
):
    """
    List users with pagination and filtering.
    
    Args:
        db: Database session
        role: Filter by user role
        status: Filter by user status
        email_contains: Filter by email substring
        page: Page number
        page_size: Items per page
    
    Returns:
        Paginated list of users with metadata
    """
    try:
        # Build query
        query = select(User)
        
        if role:
            query = query.where(User.role == role)
        
        if status:
            query = query.where(User.status == status)
        
        if email_contains:
            query = query.where(User.email.ilike(f"%{email_contains}%"))
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        users = result.scalars().all()
        
        # Convert to response models
        user_responses = [
            UserResponse(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                role=user.role,
                status=user.status,
                department=user.department,
                created_at=user.created_at,
                last_login_at=user.last_login_at,
                is_active=user.is_active,
                is_verified=user.is_verified,
            )
            for user in users
        ]
        
        return UsersListResponse(
            users=user_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=(total_count + page_size - 1) // page_size,
        )
        
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user list",
        )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    _admin: bool = Depends(require_admin_role),
):
    """
    Get user details by ID.
    
    Args:
        user_id: User ID
        db: Database session
    
    Returns:
        User details
    """
    try:
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            status=user.status,
            department=user.department,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
            is_active=user.is_active,
            is_verified=user.is_verified,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user details",
        )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    _admin: bool = Depends(require_admin_role),
):
    """
    Update user details.
    
    Args:
        user_id: User ID
        user_data: Updated user data
        db: Database session
    
    Returns:
        Updated user details
    """
    try:
        # Check if user exists
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        
        # Check if email is being changed to an existing email
        if user_data.email and user_data.email != user.email:
            email_query = select(User).where(User.email == user_data.email, User.id != user_id)
            email_result = await db.execute(email_query)
            existing_user = email_result.scalar_one_or_none()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email {user_data.email} is already registered",
                )
        
        # Update user fields
        update_fields = {}
        
        if user_data.first_name is not None:
            update_fields["first_name"] = user_data.first_name
        
        if user_data.last_name is not None:
            update_fields["last_name"] = user_data.last_name
        
        if user_data.email is not None:
            update_fields["email"] = user_data.email
        
        if user_data.role is not None:
            update_fields["role"] = user_data.role
        
        if user_data.status is not None:
            update_fields["status"] = user_data.status
        
        if user_data.department is not None:
            update_fields["department"] = user_data.department
        
        if user_data.is_active is not None:
            update_fields["is_active"] = user_data.is_active
        
        if user_data.is_verified is not None:
            update_fields["is_verified"] = user_data.is_verified
        
        if update_fields:
            update_fields["updated_at"] = datetime.utcnow()
            
            update_stmt = (
                update(User)
                .where(User.id == user_id)
                .values(**update_fields)
            )
            await db.execute(update_stmt)
            await db.commit()
            
            # Refresh user from database
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
        
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            status=user.status,
            department=user.department,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
            is_active=user.is_active,
            is_verified=user.is_verified,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


@router.put("/users/{user_id}/roles", response_model=UserResponse)
async def assign_role(
    user_id: str,
    role_request: RoleAssignmentRequest,
    db: AsyncSession = Depends(get_db_session),
    _admin: bool = Depends(require_admin_role),
):
    """
    Assign role to user.
    
    Args:
        user_id: User ID
        role_request: Role assignment request
        db: Database session
    
    Returns:
        Updated user details
    """
    try:
        # Check if user exists
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        
        # Update role
        update_stmt = (
            update(User)
            .where(User.id == user_id)
            .values(role=role_request.role, updated_at=datetime.utcnow())
        )
        await db.execute(update_stmt)
        await db.commit()
        
        # Refresh user from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        # Create audit trail
        audit_entry = AuditTrail(
            entity_type="user",
            entity_id=user_id,
            action=AuditAction.UPDATE,
            performed_by="admin",  # TODO: Get actual admin user ID
            changes={
                "old_values": {"role": user.role},
                "new_values": {"role": role_request.role},
                "changed_fields": ["role"]
            },
            ip_address="127.0.0.1",  # TODO: Get actual IP
            user_agent="Admin API",
        )
        db.add(audit_entry)
        await db.commit()
        
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            status=user.status,
            department=user.department,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
            is_active=user.is_active,
            is_verified=user.is_verified,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning role to user {user_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign role",
        )


@router.get("/workflow-definitions", response_model=List[WorkflowDefinitionResponse])
async def list_workflow_definitions(
    db: AsyncSession = Depends(get_db_session),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    _admin: bool = Depends(require_admin_role),
):
    """
    List workflow definitions with filtering.
    
    Args:
        db: Database session
        is_active: Filter by active status
        category: Filter by category
    
    Returns:
        List of workflow definitions
    """
    try:
        query = select(WorkflowDefinition)
        
        if is_active is not None:
            query = query.where(WorkflowDefinition.is_active == is_active)
        
        if category:
            query = query.where(WorkflowDefinition.category == category)
        
        query = query.order_by(WorkflowDefinition.created_at.desc())
        result = await db.execute(query)
        definitions = result.scalars().all()
        
        return [
            WorkflowDefinitionResponse(
                id=definition.id,
                name=definition.name,
                description=definition.description,
                version=definition.version,
                category=definition.category,
                steps=definition.steps,
                is_active=definition.is_active,
                created_at=definition.created_at,
                updated_at=definition.updated_at,
            )
            for definition in definitions
        ]
        
    except Exception as e:
        logger.error(f"Error listing workflow definitions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow definitions",
        )


@router.put("/workflow-definitions/{definition_id}", response_model=WorkflowDefinitionResponse)
async def update_workflow_definition(
    definition_id: str,
    definition_data: WorkflowDefinitionUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    _admin: bool = Depends(require_admin_role),
):
    """
    Update workflow definition.
    
    Args:
        definition_id: Workflow definition ID
        definition_data: Updated definition data
        db: Database session
    
    Returns:
        Updated workflow definition
    """
    try:
        # Check if definition exists
        query = select(WorkflowDefinition).where(WorkflowDefinition.id == definition_id)
        result = await db.execute(query)
        definition = result.scalar_one_or_none()
        
        if not definition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow definition with ID {definition_id} not found",
            )
        
        # Update definition fields
        update_fields = {}
        
        if definition_data.name is not None:
            update_fields["name"] = definition_data.name
        
        if definition_data.description is not None:
            update_fields["description"] = definition_data.description
        
        if definition_data.category is not None:
            update_fields["category"] = definition_data.category
        
        if definition_data.steps is not None:
            update_fields["steps"] = definition_data.steps
        
        if definition_data.is_active is not None:
            update_fields["is_active"] = definition_data.is_active
        
        if update_fields:
            update_fields["updated_at"] = datetime.utcnow()
            
            update_stmt = (
                update(WorkflowDefinition)
                .where(WorkflowDefinition.id == definition_id)
                .values(**update_fields)
            )
            await db.execute(update_stmt)
            await db.commit()
            
            # Refresh from database
            result = await db.execute(select(WorkflowDefinition).where(WorkflowDefinition.id == definition_id))
            definition = result.scalar_one_or_none()
        
        return WorkflowDefinitionResponse(
            id=definition.id,
            name=definition.name,
            description=definition.description,
            version=definition.version,
            category=definition.category,
            steps=definition.steps,
            is_active=definition.is_active,
            created_at=definition.created_at,
            updated_at=definition.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow definition {definition_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update workflow definition",
        )


@router.get("/workflow-instances", response_model=List[WorkflowInstanceResponse])
async def list_workflow_instances(
    db: AsyncSession = Depends(get_db_session),
    status: Optional[WorkflowStatus] = Query(None, description="Filter by status"),
    days: int = Query(7, ge=1, le=365, description="Lookback days"),
    _admin: bool = Depends(require_admin_role),
):
    """
    List workflow instances with filtering.
    
    Args:
        db: Database session
        status: Filter by status
        days: Lookback days
    
    Returns:
        List of workflow instances
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(WorkflowInstance).where(
            WorkflowInstance.created_at >= cutoff_date
        )
        
        if status:
            query = query.where(WorkflowInstance.status == status)
        
        query = query.order_by(WorkflowInstance.created_at.desc())
        result = await db.execute(query)
        instances = result.scalars().all()
        
        return [
            WorkflowInstanceResponse(
                id=instance.id,
                workflow_definition_id=instance.workflow_definition_id,
                name=instance.name,
                status=instance.status,
                current_step=instance.current_step,
                created_by=instance.created_by,
                created_at=instance.created_at,
                updated_at=instance.updated_at,
                completed_at=instance.completed_at,
            )
            for instance in instances
        ]
        
    except Exception as e:
        logger.error(f"Error listing workflow instances: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow instances",
        )


@router.delete("/workflow-instances/{instance_id}")
async def cancel_workflow_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db_session),
    _admin: bool = Depends(require_admin_role),
):
    """
    Cancel workflow instance.
    
    Args:
        instance_id: Workflow instance ID
        db: Database session
    
    Returns:
        Success message
    """
    try:
        # Check if instance exists
        query = select(WorkflowInstance).where(WorkflowInstance.id == instance_id)
        result = await db.execute(query)
        instance = result.scalar_one_or_none()
        
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow instance with ID {instance_id} not found",
            )
        
        # Only allow cancellation if not already completed or cancelled
        if instance.status in [WorkflowStatus.COMPLETED, WorkflowStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel workflow instance with status {instance.status}",
            )
        
        # Update status to cancelled
        update_stmt = (
            update(WorkflowInstance)
            .where(WorkflowInstance.id == instance_id)
            .values(
                status=WorkflowStatus.CANCELLED,
                updated_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
        )
        await db.execute(update_stmt)
        
        # Also cancel any pending approval requests
        approval_update_stmt = (
            update(ApprovalRequest)
            .where(
                ApprovalRequest.workflow_instance_id == instance_id,
                ApprovalRequest.status == ApprovalStatus.PENDING,
            )
            .values(
                status=ApprovalStatus.CANCELLED,
                updated_at=datetime.utcnow(),
                response_notes="Workflow cancelled by admin",
            )
        )
        await db.execute(approval_update_stmt)
        
        # Create audit trail
        audit_entry = AuditTrail(
            entity_type="workflow_instance",
            entity_id=instance_id,
            action=AuditAction.CANCEL,
            performed_by="admin",  # TODO: Get actual admin user ID
            changes={
                "old_values": {"status": instance.status},
                "new_values": {"status": WorkflowStatus.CANCELLED},
                "changed_fields": ["status"]
            },
            ip_address="127.0.0.1",  # TODO: Get actual IP
            user_agent="Admin API",
        )
        db.add(audit_entry)
        
        await db.commit()
        
        return {"message": f"Workflow instance {instance_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling workflow instance {instance_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel workflow instance",
        )


@router.get("/stats/system", response_model=SystemStatsResponse)
async def get_system_stats(
    db: AsyncSession = Depends(get_db_session),
    _admin: bool = Depends(require_admin_role),
):
    """
    Get system statistics.
    
    Args:
        db: Database session
    
    Returns:
        System statistics
    """
    try:
        # User statistics
        users_total_query = select(func.count()).select_from(User)
        users_active_query = select(func.count()).where(User.is_active == True)
        users_by_role_query = select(User.role, func.count()).group_by(User.role)
        
        users_total_result = await db.execute(users_total_query)
        users_active_result = await db.execute(users_active_query)
        users_by_role_result = await db.execute(users_by_role_query)
        
        users_total = users_total_result.scalar()
        users_active = users_active_result.scalar()
        
        users_by_role = [
            {"role": role, "count": count}
            for role, count in users_by_role_result.all()
        ]
        
        # Workflow statistics
        workflows_total_query = select(func.count()).select_from(WorkflowInstance)
        workflows_by_status_query = select(WorkflowInstance.status, func.count()).group_by(WorkflowInstance.status)
        
        workflows_total_result = await db.execute(workflows_total_query)
        workflows_by_status_result = await db.execute(workflows_by_status_query)
        
        workflows_total = workflows_total_result.scalar()
        workflows_by_status = [
            {"status": status, "count": count}
            for status, count in workflows_by_status_result.all()
        ]
        
        # Task statistics
        tasks_total_query = select(func.count()).select_from(TaskAssignment)
        tasks_pending_query = select(func.count()).where(TaskAssignment.status == TaskStatus.PENDING)
        tasks_overdue_query = select(func.count()).where(
            TaskAssignment.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            TaskAssignment.due_date < datetime.utcnow(),
        )
        
        tasks_total_result = await db.execute(tasks_total_query)
        tasks_pending_result = await db.execute(tasks_pending_query)
        tasks_overdue_result = await db.execute(tasks_overdue_query)
        
        tasks_total = tasks_total_result.scalar()
        tasks_pending = tasks_pending_result.scalar()
        tasks_overdue = tasks_overdue_result.scalar()
        
        # Approval statistics
        approvals_total_query = select(func.count()).select_from(ApprovalRequest)
        approvals_pending_query = select(func.count()).where(ApprovalRequest.status == ApprovalStatus.PENDING)
        
        approvals_total_result = await db.execute(approvals_total_query)
        approvals_pending_result = await db.execute(approvals_pending_query)
        
        approvals_total = approvals_total_result.scalar()
        approvals_pending = approvals_pending_result.scalar()
        
        return SystemStatsResponse(
            users=UserStats(
                total=users_total,
                active=users_active,
                by_role=users_by_role,
            ),
            workflows={
                "total": workflows_total,
                "by_status": workflows_by_status,
            },
            tasks={
                "total": tasks_total,
                "pending": tasks_pending,
                "overdue": tasks_overdue,
            },
            approvals={
                "total": approvals_total,
                "pending": approvals_pending,
            },
        )
        
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics",
        )