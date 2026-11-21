"""
Pydantic schemas for user CRUD requests and responses.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    """Base schema for user operations."""
    
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., description="Display name for user", min_length=3, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    
    password: str = Field(
        ..., 
        description="User password",
        min_length=8,
        max_length=100,
        example="SecurePassword123!"
    )
    confirm_password: str = Field(
        ..., 
        description="Password confirmation",
        min_length=8,
        max_length=100,
        example="SecurePassword123!"
    )
    role: str = Field(
        default="agent",
        description="User role",
        pattern="^(admin|manager|agent)$",
        example="agent"
    )
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        """Validate that password and confirm_password match."""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "newuser@solmar.com",
                "username": "new_user",
                "password": "NewPass123!",
                "confirm_password": "NewPass123!",
                "role": "agent"
            }
        }


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""
    
    email: Optional[EmailStr] = Field(None, description="User email address")
    username: Optional[str] = Field(None, description="Display name for user", min_length=3, max_length=100)
    role: Optional[str] = Field(None, description="User role", pattern="^(admin|manager|agent)$")
    is_active: Optional[bool] = Field(None, description="Whether user is active")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "updated@solmar.com",
                "username": "updated_user",
                "role": "manager",
                "is_active": True
            }
        }


class UserResponse(BaseModel):
    """Schema for user response (read operations)."""
    
    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., description="Display name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True  # Allows conversion from ORM models
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "agent@solmar.com",
                "username": "sales_agent",
                "role": "agent",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class UserListResponse(BaseModel):
    """Schema for listing multiple users with pagination."""
    
    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    class Config:
        schema_extra = {
            "example": {
                "users": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "email": "agent@solmar.com",
                        "username": "sales_agent",
                        "role": "agent",
                        "is_active": True,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "total_pages": 1
            }
        }


class UserRoleUpdate(BaseModel):
    """Schema for updating a user's role."""
    
    role: str = Field(
        ..., 
        description="New user role",
        pattern="^(admin|manager|agent)$",
        example="manager"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "role": "manager"
            }
        }


class UserStatusUpdate(BaseModel):
    """Schema for updating a user's status."""
    
    is_active: bool = Field(
        ..., 
        description="New active status",
        example=True
    )
    
    class Config:
        schema_extra = {
            "example": {
                "is_active": False
            }
        }


class UserSearchParams(BaseModel):
    """Schema for user search parameters."""
    
    email: Optional[str] = Field(None, description="Search by email (partial match)")
    username: Optional[str] = Field(None, description="Search by username (partial match)")
    role: Optional[str] = Field(None, description="Filter by role")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Page size")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "solmar",
                "role": "agent",
                "is_active": True,
                "page": 1,
                "page_size": 20
            }
        }


class UserPasswordUpdate(BaseModel):
    """Schema for updating a user's password."""
    
    current_password: str = Field(..., description="Current password", min_length=8, max_length=100)
    new_password: str = Field(..., description="New password", min_length=8, max_length=100)
    confirm_new_password: str = Field(..., description="New password confirmation", min_length=8, max_length=100)
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values, **kwargs):
        """Validate that new_password and confirm_new_password match."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v
    
    @validator('new_password')
    def validate_new_password_strength(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('New password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('New password must contain at least one uppercase letter')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "OldPass123!",
                "new_password": "NewPass123!",
                "confirm_new_password": "NewPass123!"
            }
        }


class UserBulkUpdate(BaseModel):
    """Schema for bulk updating users."""
    
    user_ids: List[str] = Field(..., description="List of user IDs to update", min_items=1)
    role: Optional[str] = Field(None, description="New role for all users")
    is_active: Optional[bool] = Field(None, description="New active status for all users")
    
    @validator('role')
    def validate_role(cls, v):
        """Validate role if provided."""
        if v is not None and v not in ['admin', 'manager', 'agent']:
            raise ValueError('Role must be one of: admin, manager, agent')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "user_ids": ["550e8400-e29b-41d4-a716-446655440000", "660e8400-e29b-41d4-a716-446655440001"],
                "role": "manager",
                "is_active": True
            }
        }


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    
    detail: str = Field(..., description="Error description")
    code: Optional[str] = Field(None, description="Error code")
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "User not found",
                "code": "USER_NOT_FOUND"
            }
        }