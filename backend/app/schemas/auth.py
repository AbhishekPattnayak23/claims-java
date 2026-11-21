"""
Pydantic schemas for authentication requests and responses.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


class LoginRequest(BaseModel):
    """Schema for login request."""
    
    email: EmailStr = Field(
        ..., 
        description="User email address for authentication",
        example="user@example.com"
    )
    password: str = Field(
        ..., 
        description="User password",
        min_length=8,
        max_length=100,
        example="SecurePassword123!"
    )

    class Config:
        schema_extra = {
            "example": {
                "email": "agent@solmar.com",
                "password": "AgentPass123!"
            }
        }


class RegisterRequest(BaseModel):
    """Schema for user registration request."""
    
    email: EmailStr = Field(
        ..., 
        description="User email address",
        example="user@example.com"
    )
    username: str = Field(
        ..., 
        description="Display name for user",
        min_length=3,
        max_length=100,
        example="john_doe"
    )
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
        # Check for at least one digit
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        # Check for at least one uppercase letter
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


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    
    access_token: str = Field(
        ..., 
        description="JWT access token for API authorization",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    refresh_token: str = Field(
        ..., 
        description="JWT refresh token for obtaining new access tokens",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    token_type: str = Field(
        default="bearer",
        description="Type of token",
        example="bearer"
    )
    expires_in: int = Field(
        default=900,
        description="Access token expiration time in seconds",
        example=900
    )

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900
            }
        }


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    
    refresh_token: str = Field(
        ..., 
        description="Refresh token to obtain new access token",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )

    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class LogoutRequest(BaseModel):
    """Schema for logout request."""
    
    refresh_token: str = Field(
        ..., 
        description="Refresh token to invalidate",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )

    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class UserProfileResponse(BaseModel):
    """Schema for user profile response."""
    
    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., description="Display name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True
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


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""
    
    current_password: str = Field(
        ..., 
        description="Current password",
        min_length=8,
        max_length=100
    )
    new_password: str = Field(
        ..., 
        description="New password",
        min_length=8,
        max_length=100
    )
    confirm_new_password: str = Field(
        ..., 
        description="New password confirmation",
        min_length=8,
        max_length=100
    )

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


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    
    email: EmailStr = Field(
        ..., 
        description="User email address for password reset",
        example="user@example.com"
    )

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirmRequest(BaseModel):
    """Schema for password reset confirmation."""
    
    token: str = Field(
        ..., 
        description="Password reset token",
        example="abc123def456"
    )
    new_password: str = Field(
        ..., 
        description="New password",
        min_length=8,
        max_length=100
    )
    confirm_new_password: str = Field(
        ..., 
        description="New password confirmation",
        min_length=8,
        max_length=100
    )

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
                "token": "abc123def456",
                "new_password": "NewPass123!",
                "confirm_new_password": "NewPass123!"
            }
        }


class AuthErrorResponse(BaseModel):
    """Schema for authentication error responses."""
    
    detail: str = Field(
        ..., 
        description="Error description",
        example="Invalid credentials"
    )
    code: Optional[str] = Field(
        None,
        description="Error code for client handling",
        example="INVALID_CREDENTIALS"
    )

    class Config:
        schema_extra = {
            "example": {
                "detail": "Invalid credentials",
                "code": "INVALID_CREDENTIALS"
            }
        }