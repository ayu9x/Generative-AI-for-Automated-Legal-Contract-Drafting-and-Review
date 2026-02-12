"""Security utilities - JWT, password hashing, encryption."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings
from app.core.exceptions import AuthenticationError, EncryptionError, TokenExpiredError

# ─── Password Hashing ───────────────────────────────────────────────────

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS,
)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ─── JWT Token Management ───────────────────────────────────────────────

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "jti": secrets.token_urlsafe(32),
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": secrets.token_urlsafe(32),
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


# ─── Data Encryption (AES-256) ──────────────────────────────────────────

def _get_fernet_key() -> bytes:
    """Derive a Fernet-compatible key from the encryption key."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"legal-contract-ai-salt-v1",
        iterations=480000,
    )
    key = kdf.derive(settings.ENCRYPTION_KEY.encode())
    return base64.urlsafe_b64encode(key)


_fernet = None


def _get_fernet() -> Fernet:
    """Get or create Fernet encryption instance."""
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_get_fernet_key())
    return _fernet


def encrypt_data(data: str) -> str:
    """Encrypt sensitive data using AES-256 (Fernet)."""
    try:
        f = _get_fernet()
        encrypted = f.encrypt(data.encode())
        return encrypted.decode()
    except Exception as e:
        raise EncryptionError("encryption")


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt data encrypted with encrypt_data."""
    try:
        f = _get_fernet()
        decrypted = f.decrypt(encrypted_data.encode())
        return decrypted.decode()
    except Exception as e:
        raise EncryptionError("decryption")


def hash_document(content: str) -> str:
    """Create a SHA-256 hash of document content for integrity verification."""
    return hashlib.sha256(content.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"lca_{secrets.token_urlsafe(48)}"


# ─── Data Masking ────────────────────────────────────────────────────────

def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data, showing only the last N characters."""
    if len(data) <= visible_chars:
        return "*" * len(data)
    return "*" * (len(data) - visible_chars) + data[-visible_chars:]


def sanitize_log_data(data: Dict[str, Any], sensitive_fields: list = None) -> Dict[str, Any]:
    """Sanitize data for logging, masking sensitive fields."""
    sensitive = sensitive_fields or [
        "password", "token", "api_key", "secret", "ssn",
        "credit_card", "bank_account", "encryption_key",
    ]
    sanitized = {}
    for key, value in data.items():
        if any(s in key.lower() for s in sensitive):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value, sensitive)
        else:
            sanitized[key] = value
    return sanitized
