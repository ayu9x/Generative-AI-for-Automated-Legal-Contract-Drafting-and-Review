"""Authentication and authorization routes."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

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
    role: str = Field(default="CONTRACT_VIEWER")


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


# ── In-Memory User Store (Replace with DB in production) ────────────

_users_db: dict = {}
_api_keys: dict = {}

# ── Seed a demo admin user so login works out-of-the-box ────────────
_demo_user_id = "demo-admin-001"
_users_db[_demo_user_id] = {
    "id": _demo_user_id,
    "email": "admin@legalai.com",
    "password_hash": hash_password("Admin@123456"),
    "full_name": "Admin User",
    "organization": "Legal AI Corp",
    "role": "ADMIN",
    "is_active": True,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "last_login": None,
}


def _get_user_by_email(email: str) -> Optional[dict]:
    """Find user by email."""
    for user in _users_db.values():
        if user["email"] == email:
            return user
    return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Dependency to get current authenticated user."""
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id not in _users_db:
            raise AuthenticationError("User not found")
        user = _users_db[user_id]
        if not user.get("is_active", True):
            raise AuthorizationError("Account is deactivated")
        return user
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
async def register(request: RegisterRequest):
    """Register a new user account."""
    if _get_user_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    user = {
        "id": user_id,
        "email": request.email,
        "password_hash": hash_password(request.password),
        "full_name": request.full_name,
        "organization": request.organization,
        "role": request.role,
        "is_active": True,
        "created_at": now,
        "last_login": now,
    }
    _users_db[user_id] = user

    access_token = create_access_token({"sub": user_id, "email": request.email, "role": request.role})
    refresh_token = create_refresh_token({"sub": user_id})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user_id,
        email=request.email,
        role=request.role,
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user and return tokens."""
    user = _get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    user["last_login"] = datetime.now(timezone.utc).isoformat()

    access_token = create_access_token({"sub": user["id"], "email": user["email"], "role": user["role"]})
    refresh_token = create_refresh_token({"sub": user["id"]})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user["id"],
        email=user["email"],
        role=user["role"],
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    try:
        payload = decode_token(request.refresh_token)
        user_id = payload.get("sub")
        if user_id not in _users_db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        user = _users_db[user_id]
        access_token = create_access_token({"sub": user["id"], "email": user["email"], "role": user["role"]})
        new_refresh_token = create_refresh_token({"sub": user["id"]})

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            user_id=user["id"],
            email=user["email"],
            role=user["role"],
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
):
    """Update current user profile."""
    if request.full_name is not None:
        current_user["full_name"] = request.full_name
    if request.organization is not None:
        current_user["organization"] = request.organization

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
):
    """Change current user's password."""
    if not verify_password(request.current_password, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user["password_hash"] = hash_password(request.new_password)
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
