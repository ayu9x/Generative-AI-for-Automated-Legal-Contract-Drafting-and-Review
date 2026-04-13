"""Authentication and authorization routes."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User, UserRole

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    generate_api_key,
)
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# ── Request/Response Schemas ─────────────────────────────────────────

class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=255)
    organization: Optional[str] = None
    role: str = Field(default="viewer")


class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800
    user_id: str
    email: str
    role: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: str
    email: str
    full_name: str
    organization: Optional[str] = None
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    """Update profile request."""
    full_name: Optional[str] = None
    organization: Optional[str] = None


class APIKeyResponse(BaseModel):
    """API key response."""
    api_key: str
    created_at: str


# ── In-Memory API Keys Store (Replace with DB in production) ────────────
_api_keys: dict = {}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Dependency to get current authenticated user as dictionary for backwards compatibility."""
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token")
            
        result = await db.execute(select(User).filter_by(id=UUID(user_id)))
        user = result.scalar_one_or_none()
        
        if not user:
            raise AuthenticationError("User not found")
        if not user.is_active:
            raise AuthorizationError("Account is deactivated")
            
        return {
            "id": str(user.id),
            "email": user.email,
            "password_hash": user.hashed_password,
            "full_name": user.full_name,
            "organization": user.organization,
            "role": user.role.value if isinstance(user.role, UserRole) else user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(*roles: str):
    """Dependency factory for role-based access control."""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(roles)}",
            )
        return current_user
    return role_checker


# ── Routes ───────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    # Check if email is taken
    result = await db.execute(select(User).filter_by(email=request.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user_id = uuid4()
    now = datetime.now(timezone.utc)
    
    # generate a unique username from email
    base_username = request.email.split("@")[0]
    username = f"{base_username}_{str(user_id)[:8]}"

    # Map role string to enum
    try:
        role_enum = UserRole(request.role.lower())
    except ValueError:
        role_enum = UserRole.VIEWER

    user = User(
        id=user_id,
        email=request.email,
        username=username,
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
        organization=request.organization,
        role=role_enum,
        is_active=True,
        created_at=now,
        last_login=now,
    )
    db.add(user)
    await db.commit()

    user_id_str = str(user_id)
    role_str = role_enum.value

    access_token = create_access_token({"sub": user_id_str, "email": request.email, "role": role_str})
    refresh_token = create_refresh_token({"sub": user_id_str})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user_id_str,
        email=request.email,
        role=role_str,
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return tokens."""
    result = await db.execute(select(User).filter_by(email=request.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    
    user_id_str = str(user.id)
    role_str = user.role.value if isinstance(user.role, UserRole) else str(user.role)

    access_token = create_access_token({"sub": user_id_str, "email": user.email, "role": role_str})
    refresh_token = create_refresh_token({"sub": user_id_str})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user_id_str,
        email=user.email,
        role=role_str,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token."""
    try:
        payload = decode_token(request.refresh_token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
            
        result = await db.execute(select(User).filter_by(id=UUID(user_id)))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists",
            )
            
        user_id_str = str(user.id)
        role_str = user.role.value if isinstance(user.role, UserRole) else str(user.role)
        
        access_token = create_access_token({"sub": user_id_str, "email": user.email, "role": role_str})
        new_refresh_token = create_refresh_token({"sub": user_id_str})

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            user_id=user_id_str,
            email=user.email,
            role=role_str,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}",
        )


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile."""
    return UserProfileResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        organization=current_user.get("organization"),
        role=current_user["role"],
        is_active=current_user["is_active"],
        created_at=current_user["created_at"],
        last_login=current_user.get("last_login"),
    )


@router.put("/me", response_model=UserProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile."""
    result = await db.execute(select(User).filter_by(id=UUID(current_user["id"])))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if request.full_name is not None:
        user.full_name = request.full_name
        current_user["full_name"] = request.full_name
    if request.organization is not None:
        user.organization = request.organization
        current_user["organization"] = request.organization

    await db.commit()

    return UserProfileResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        organization=current_user.get("organization"),
        role=current_user["role"],
        is_active=current_user["is_active"],
        created_at=current_user["created_at"],
        last_login=current_user.get("last_login"),
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change current user's password."""
    if not verify_password(request.current_password, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    result = await db.execute(select(User).filter_by(id=UUID(current_user["id"])))
    user = result.scalar_one_or_none()
    
    if user:
        user.hashed_password = hash_password(request.new_password)
        await db.commit()
        
    return {"message": "Password changed successfully"}


@router.post("/api-key", response_model=APIKeyResponse)
async def create_api_key(current_user: dict = Depends(get_current_user)):
    """Generate a new API key for the current user."""
    api_key = generate_api_key()
    _api_keys[api_key] = current_user["id"]

    return APIKeyResponse(
        api_key=api_key,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout current user (invalidate session)."""
    return {"message": "Successfully logged out"}
