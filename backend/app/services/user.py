"""
User service for user CRUD operations and role-based access control.
Handles user management, role assignments, and permission checks.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import select, and_, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import settings
from ..models.user import User
from ..models.role_permission import RolePermission
from ..schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserRoleUpdate,
    UserStatusUpdate,
    UserSearchParams,
    UserPasswordUpdate,
    UserBulkUpdate,
    ErrorResponse
)


class UserService:
    """Service handling user management and role-based access control."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def get_user_by_id(self, user_id: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (User, error_message)
        """
        query = select(User).where(
            User.id == user_id,
            User.is_active == True
        )
        
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None, "User not found or inactive"
        
        return user, None
    
    async def get_user_by_email(self, email: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            Tuple of (User, error_message)
        """
        query = select(User).where(
            User.email == email,
            User.is_active == True
        )
        
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None, "User not found or inactive"
        
        return user, None
    
    async def create_user(self, user_data: UserCreate, current_user: Optional[User] = None) -> Tuple[Optional[UserResponse], Optional[str]]:
        """
        Create a new user with proper validation.
        
        Args:
            user_data: User creation data
            current_user: Optional current user for permission checking
            
        Returns:
            Tuple of (UserResponse, error_message)
        """
        # Check if user already exists
        email_query = select(User).where(User.email == user_data.email)
        username_query = select(User).where(User.username == user_data.username)
        
        email_result = await self.db_session.execute(email_query)
        username_result = await self.db_session.execute(username_query)
        
        if email_result.scalar_one_or_none():
            return None, "Email already registered"
        
        if username_result.scalar_one_or_none():
            return None, "Username already taken"
        
        # Hash password
        from .auth import AuthenticationService
        password_hash = AuthenticationService.hash_password(user_data.password)
        
        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=user_data.email,
            username=user_data.username,
            password_hash=password_hash,
            role=user_data.role,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Save to database
        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)
        
        # Convert to response schema
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return user_response, None
    
    async def update_user(
        self, 
        user_id: str, 
        user_data: UserUpdate, 
        current_user: Optional[User] = None
    ) -> Tuple[Optional[UserResponse], Optional[str]]:
        """
        Update an existing user.
        
        Args:
            user_id: User ID to update
            user_data: User update data
            current_user: Optional current user for permission checking
            
        Returns:
            Tuple of (UserResponse, error_message)
        """
        # Get user
        query = select(User).where(
            User.id == user_id,
            User.is_active == True
        )
        
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None, "User not found or inactive"
        
        # Check if new email is already taken
        if user_data.email and user_data.email != user.email:
            email_query = select(User).where(
                User.email == user_data.email,
                User.id != user_id
            )
            email_result = await self.db_session.execute(email_query)
            if email_result.scalar_one_or_none():
                return None, "Email already registered by another user"
        
        # Check if new username is already taken
        if user_data.username and user_data.username != user.username:
            username_query = select(User).where(
                User.username == user_data.username,
                User.id != user_id
            )
            username_result = await self.db_session.execute(username_query)
            if username_result.scalar_one_or_none():
                return None, "Username already taken by another user"
        
        # Apply updates
        update_data = {}
        if user_data.email is not None:
            update_data["email"] = user_data.email
        if user_data.username is not None:
            update_data["username"] = user_data.username
        if user_data.role is not None:
            update_data["role"] = user_data.role
        if user_data.is_active is not None:
            update_data["is_active"] = user_data.is_active
        
        # Update if there are changes
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Execute update
            stmt = update(User).where(User.id == user_id).values(**update_data)
            await self.db_session.execute(stmt)
            await self.db_session.commit()
            
            # Refresh user object
            await self.db_session.refresh(user)
        
        # Convert to response schema
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return user_response, None
    
    async def delete_user(self, user_id: str, current_user: Optional[User] = None) -> Tuple[bool, Optional[str]]:
        """
        Soft delete a user (set is_active=False).
        
        Args:
            user_id: User ID to delete
            current_user: Optional current user for permission checking
            
        Returns:
            Tuple of (success, error_message)
        """
        # Check if user exists
        query = select(User).where(
            User.id == user_id,
            User.is_active == True
        )
        
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return False, "User not found or already inactive"
        
        # Prevent self-deletion
        if current_user and current_user.id == user_id:
            return False, "Cannot delete your own account"
        
        # Soft delete (set is_active=False)
        stmt = update(User).where(User.id == user_id).values(
            is_active=False,
            updated_at=datetime.utcnow()
        )
        await self.db_session.execute(stmt)
        await self.db_session.commit()
        
        return True, None
    
    async def get_users(
        self, 
        search_params: UserSearchParams,
        current_user: Optional[User] = None
    ) -> Tuple[Optional[UserListResponse], Optional[str]]:
        """
        Get users with pagination and filtering.
        
        Args:
            search_params: Search and filter parameters
            current_user: Optional current user for permission checking
            
        Returns:
            Tuple of (UserListResponse, error_message)
        """
        # Build query
        query = select(User).where(User.is_active == True)
        
        # Apply filters
        if search_params.email:
            query = query.where(User.email.ilike(f"%{search_params.email}%"))
        
        if search_params.username:
            query = query.where(User.username.ilike(f"%{search_params.username}%"))
        
        if search_params.role:
            query = query.where(User.role == search_params.role)
        
        if search_params.is_active is not None:
            query = query.where(User.is_active == search_params.is_active)
        
        # Calculate pagination
        total_result = await self.db_session.execute(
            select(sqlalchemy.func.count()).select_from(query.subquery())
        )
        total = total_result.scalar_one()
        
        total_pages = (total + search_params.page_size - 1) // search_params.page_size
        offset = (search_params.page - 1) * search_params.page_size
        
        # Apply pagination
        query = query.offset(offset).limit(search_params.page_size)
        
        # Execute query
        result = await self.db_session.execute(query)
        users = result.scalars().all()
        
        # Convert to response schema
        user_responses = [
            UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ]
        
        user_list_response = UserListResponse(
            users=user_responses,
            total=total,
            page=search_params.page,
            page_size=search_params.page_size,
            total_pages=total_pages
        )
        
        return user_list_response, None
    
    async def update_user_role(
        self, 
        user_id: str, 
        role_data: UserRoleUpdate,
        current_user: Optional[User] = None
    ) -> Tuple[Optional[UserResponse], Optional[str]]:
        """
        Update user role.
        
        Args:
            user_id: User ID
            role_data: New role data
            current_user: Optional current user for permission checking
            
        Returns:
            Tuple of (UserResponse, error_message)
        """
        # Get user
        query = select(User).where(
            User.id == user_id,
            User.is_active == True
        )
        
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None, "User not found or inactive"
        
        # Prevent role changes on admin accounts (if current_user is not admin)
        if current_user and not current_user.is_admin and user.is_admin:
            return None, "Insufficient permissions to modify admin roles"
        
        # Update role
        stmt = update(User).where(User.id == user_id).values(
            role=role_data.role,
            updated_at=datetime.utcnow()
        )
        await self.db_session.execute(stmt)
        await self.db_session.commit()
        
        # Refresh user object
        await self.db_session.refresh(user)
        
        # Convert to response schema
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return user_response, None
    
    async def update_user_status(
        self, 
        user_id: str, 
        status_data: UserStatusUpdate,
        current_user: Optional[User] = None
    ) -> Tuple[Optional[UserResponse], Optional[str]]:
        """
        Update user active status.
        
        Args:
            user_id: User ID
            status_data: New status data
            current_user: Optional current user for permission checking
            
        Returns:
            Tuple of (UserResponse, error_message)
        """
        # Get user
        query = select(User).where(
            User.id == user_id,
            User.is_active == True  # Only find active users
        )
        
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None, "User not found or already inactive"
        
        # Prevent deactivation of admin accounts (if current_user is not admin)
        if current_user and not current_user.is_admin and user.is_admin and not status_data.is_active:
            return None, "Insufficient permissions to deactivate admin accounts"
        
        # Prevent self-deactivation
        if current_user and current_user.id == user_id and not status_data.is_active:
            return None, "Cannot deactivate your own account"
        
        # Update status
        stmt = update(User).where(User.id == user_id).values(
            is_active=status_data.is_active,
            updated_at=datetime.utcnow()
        )
        await self.db_session.execute(stmt)
        await self.db_session.commit()
        
        # Refresh user object
        await self.db_session.refresh(user)
        
        # Convert to response schema
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return user_response, None
    
    async def update_user_password(
        self, 
        user_id: str, 
        password_data: UserPasswordUpdate,
        current_user: Optional[User] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Update user password with validation.
        
        Args:
            user_id: User ID
            password_data: Password update data
            current_user: Optional current user for permission checking
            
        Returns:
            Tuple of (success, error_message)
        """
        # Get user
        query = select(User).where(
            User.id == user_id,
            User.is_active == True
        )
        
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return False, "User not found or inactive"
        
        # Verify current password
        from .auth import AuthenticationService
        if not AuthenticationService.verify_password(password_data.current_password, user.password_hash):
            return False, "Current password is incorrect"
        
        # Hash new password
        password_hash = AuthenticationService.hash_password(password_data.new_password)
        
        # Update password
        stmt = update(User).where(User.id == user_id).values(
            password_hash=password_hash,
            updated_at=datetime.utcnow()
        )
        await self.db_session.execute(stmt)
        await self.db_session.commit()
        
        return True, None
    
    async def bulk_update_users(
        self, 
        bulk_data: UserBulkUpdate,
        current_user: Optional[User] = None
    ) -> Tuple[int, Optional[str]]:
        """
        Bulk update multiple users.
        
        Args:
            bulk_data: Bulk update data
            current_user: Optional current user for permission checking
            
        Returns:
            Tuple of (updated_count, error_message)
        """
        # Validate all user IDs exist and are active
        query = select(User).where(
            User.id.in_(bulk_data.user_ids),
            User.is_active == True
        )
        
        result = await self.db_session.execute(query)
        users = result.scalars().all()
        
        if len(users) != len(bulk_data.user_ids):
            return 0, "Some users not found or inactive"
        
        # Prepare update data
        update_data = {"updated_at": datetime.utcnow()}
        
        if bulk_data.role is not None:
            update_data["role"] = bulk_data.role
        
        if bulk_data.is_active is not None:
            update_data["is_active"] = bulk_data.is_active
        
        # Execute bulk update
        stmt = update(User).where(User.id.in_(bulk_data.user_ids)).values(**update_data)
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        
        return len(bulk_data.user_ids), None
    
    async def check_permission(self, user: User, permission: str) -> bool:
        """
        Check if user has specific permission.
        
        Args:
            user: User object
            permission: Permission string to check
            
        Returns:
            True if user has permission, False otherwise
        """
        # Get role permissions
        query = select(RolePermission).where(
            RolePermission.role == user.role,
            RolePermission.permission == permission
        )
        
        result = await self.db_session.execute(query)
        role_permission = result.scalar_one_or_none()
        
        return role_permission is not None and role_permission.is_active
    
    async def get_allowed_actions(self, user: User) -> List[str]:
        """
        Get all allowed actions for a user based on their role.
        
        Args:
            user: User object
            
        Returns:
            List of allowed permission strings
        """
        query = select(RolePermission).where(
            RolePermission.role == user.role,
            RolePermission.is_active == True
        )
        
        result = await self.db_session.execute(query)
        role_permissions = result.scalars().all()
        
        return [rp.permission for rp in role_permissions]
    
    async def get_users_by_role(self, role: str) -> List[UserResponse]:
        """
        Get all users with a specific role.
        
        Args:
            role: User role
            
        Returns:
            List of UserResponse objects
        """
        query = select(User).where(
            User.role == role,
            User.is_active == True
        )
        
        result = await self.db_session.execute(query)
        users = result.scalars().all()
        
        return [
            UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ]
    
    async def search_users(
        self, 
        search_term: str,
        limit: int = 20
    ) -> List[UserResponse]:
        """
        Search users by email or username.
        
        Args:
            search_term: Search term
            limit: Maximum number of results
            
        Returns:
            List of UserResponse objects
        """
        query = select(User).where(
            and_(
                User.is_active == True,
                or_(
                    User.email.ilike(f"%{search_term}%"),
                    User.username.ilike(f"%{search_term}%")
                )
            )
        ).limit(limit)
        
        result = await self.db_session.execute(query)
        users = result.scalars().all()
        
        return [
            UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ]


# Create a service instance factory
async def get_user_service(db: AsyncSession) -> UserService:
    """Dependency injection for user service."""
    return UserService(db)