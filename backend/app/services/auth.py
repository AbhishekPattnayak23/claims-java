"""
Authentication service for user registration, login, and JWT token management.
Handles password hashing, JWT token generation, and validation.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.user import User
from ..schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    AuthErrorResponse
)
from ..schemas.user import UserResponse


class AuthenticationService:
    """Service handling authentication and authorization logic."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False
    
    @staticmethod
    def create_access_token(user_id: str, user_role: str) -> str:
        """
        Create a JWT access token.
        
        Args:
            user_id: User ID
            user_role: User role
            
        Returns:
            JWT access token
        """
        now = datetime.utcnow()
        expires = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": user_id,
            "role": user_role,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
            "jti": str(uuid.uuid4())
        }
        
        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return token
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            user_id: User ID
            
        Returns:
            JWT refresh token
        """
        now = datetime.utcnow()
        expires = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
            "jti": str(uuid.uuid4())
        }
        
        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return token
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
        """
        Verify a JWT token and return its payload.
        
        Args:
            token: JWT token string
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Check token type
            if payload.get("type") != token_type:
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def register_user(self, register_data: RegisterRequest) -> Tuple[Optional[UserResponse], Optional[str]]:
        """
        Register a new user.
        
        Args:
            register_data: Registration data
            
        Returns:
            Tuple of (UserResponse, error_message)
        """
        # Check if user already exists
        email_query = select(User).where(User.email == register_data.email)
        username_query = select(User).where(User.username == register_data.username)
        
        email_result = await self.db_session.execute(email_query)
        username_result = await self.db_session.execute(username_query)
        
        if email_result.scalar_one_or_none():
            return None, "Email already registered"
        
        if username_result.scalar_one_or_none():
            return None, "Username already taken"
        
        # Hash password
        password_hash = self.hash_password(register_data.password)
        
        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=register_data.email,
            username=register_data.username,
            password_hash=password_hash,
            role=register_data.role,
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
    
    async def login_user(self, login_data: LoginRequest) -> Tuple[Optional[TokenResponse], Optional[str]]:
        """
        Authenticate user and return JWT tokens.
        
        Args:
            login_data: Login credentials
            
        Returns:
            Tuple of (TokenResponse, error_message)
        """
        # Find user by email
        query = select(User).where(
            User.email == login_data.email,
            User.is_active == True
        )
        
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None, "Invalid credentials"
        
        # Verify password
        if not self.verify_password(login_data.password, user.password_hash):
            return None, "Invalid credentials"
        
        # Create tokens
        access_token = self.create_access_token(user.id, user.role)
        refresh_token = self.create_refresh_token(user.id)
        
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert minutes to seconds
        )
        
        return token_response, None
    
    async def refresh_token(self, refresh_data: RefreshTokenRequest) -> Tuple[Optional[TokenResponse], Optional[str]]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_data: Refresh token request
            
        Returns:
            Tuple of (TokenResponse, error_message)
        """
        # Verify refresh token
        payload = self.verify_token(refresh_data.refresh_token, "refresh")
        if not payload:
            return None, "Invalid or expired refresh token"
        
        user_id = payload.get("sub")
        if not user_id:
            return None, "Invalid token payload"
        
        # Find user
        query = select(User).where(
            User.id == user_id,
            User.is_active == True
        )
        
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None, "User not found or inactive"
        
        # Create new access token
        access_token = self.create_access_token(user.id, user.role)
        
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_data.refresh_token,  # Return same refresh token
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        return token_response, None
    
    async def get_current_user(self, access_token: str) -> Tuple[Optional[UserResponse], Optional[str]]:
        """
        Get current user from access token.
        
        Args:
            access_token: JWT access token
            
        Returns:
            Tuple of (UserResponse, error_message)
        """
        # Verify access token
        payload = self.verify_token(access_token, "access")
        if not payload:
            return None, "Invalid or expired access token"
        
        user_id = payload.get("sub")
        if not user_id:
            return None, "Invalid token payload"
        
        # Find user
        query = select(User).where(
            User.id == user_id,
            User.is_active == True
        )
        
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None, "User not found or inactive"
        
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
    
    async def change_password(
        self, 
        user_id: str, 
        password_data: PasswordChangeRequest
    ) -> Tuple[bool, Optional[str]]:
        """
        Change user password.
        
        Args:
            user_id: User ID
            password_data: Password change data
            
        Returns:
            Tuple of (success, error_message)
        """
        # Find user
        query = select(User).where(
            User.id == user_id,
            User.is_active == True
        )
        
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return False, "User not found or inactive"
        
        # Verify current password
        if not self.verify_password(password_data.current_password, user.password_hash):
            return False, "Current password is incorrect"
        
        # Hash new password
        new_password_hash = self.hash_password(password_data.new_password)
        
        # Update password
        user.password_hash = new_password_hash
        user.updated_at = datetime.utcnow()
        
        await self.db_session.commit()
        
        return True, None
    
    async def initiate_password_reset(self, email: str) -> Tuple[bool, Optional[str]]:
        """
        Initiate password reset process.
        
        Args:
            email: User email
            
        Returns:
            Tuple of (success, error_message)
        """
        # Find user by email
        query = select(User).where(
            User.email == email,
            User.is_active == True
        )
        
        result = await self.db_session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            # Still return success to avoid email enumeration
            return True, None
        
        # Generate reset token (in production, this would be sent via email)
        # For now, we'll just return success
        return True, None
    
    async def confirm_password_reset(
        self, 
        reset_token: str, 
        password_data: PasswordResetConfirmRequest
    ) -> Tuple[bool, Optional[str]]:
        """
        Confirm password reset with token.
        
        Args:
            reset_token: Password reset token
            password_data: New password data
            
        Returns:
            Tuple of (success, error_message)
        """
        # In a real implementation, this would verify the reset token
        # For now, we'll simulate checking if token is valid
        # In production, this token would come from an email link
        
        # For mock implementation, we'll accept any token that's not empty
        if not reset_token or len(reset_token) < 10:
            return False, "Invalid reset token"
        
        # Find user by token (in real implementation, token would be stored with user)
        # For now, we'll just simulate success
        return True, None


# Create a service instance factory
async def get_authentication_service(db: AsyncSession) -> AuthenticationService:
    """Dependency injection for authentication service."""
    return AuthenticationService(db)