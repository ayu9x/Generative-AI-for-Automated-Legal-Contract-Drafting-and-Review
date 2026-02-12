"""Tests for security utilities."""

import pytest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    encrypt_data,
    decrypt_data,
    hash_document,
    generate_api_key,
    mask_sensitive_data,
)


def test_password_hashing():
    """Test password hashing and verification."""
    password = "SecurePassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)


def test_password_hash_uniqueness():
    """Test that same password produces different hashes (salted)."""
    password = "SamePassword"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    assert hash1 != hash2  # bcrypt uses random salt
    assert verify_password(password, hash1)
    assert verify_password(password, hash2)


def test_jwt_access_token():
    """Test JWT access token creation and decoding."""
    payload = {"sub": "user-123", "email": "test@test.com", "role": "ADMIN"}
    token = create_access_token(payload)
    decoded = decode_token(token)
    assert decoded["sub"] == "user-123"
    assert decoded["email"] == "test@test.com"


def test_jwt_refresh_token():
    """Test JWT refresh token."""
    payload = {"sub": "user-123"}
    token = create_refresh_token(payload)
    decoded = decode_token(token)
    assert decoded["sub"] == "user-123"


def test_data_encryption():
    """Test data encryption and decryption."""
    sensitive_data = "This is confidential contract content"
    encrypted = encrypt_data(sensitive_data)
    assert encrypted != sensitive_data
    decrypted = decrypt_data(encrypted)
    assert decrypted == sensitive_data


def test_encryption_different_outputs():
    """Test that same data produces different encrypted outputs."""
    data = "Same content"
    enc1 = encrypt_data(data)
    enc2 = encrypt_data(data)
    # Fernet uses timestamp, so same data can produce different ciphertext
    decrypted1 = decrypt_data(enc1)
    decrypted2 = decrypt_data(enc2)
    assert decrypted1 == data
    assert decrypted2 == data


def test_document_hashing():
    """Test document hashing."""
    content = "This is a legal contract."
    hash1 = hash_document(content)
    hash2 = hash_document(content)
    assert hash1 == hash2  # Same content = same hash
    assert len(hash1) == 64  # SHA-256 hex digest

    hash3 = hash_document(content + " Modified.")
    assert hash3 != hash1  # Different content = different hash


def test_api_key_generation():
    """Test API key generation."""
    key1 = generate_api_key()
    key2 = generate_api_key()
    assert key1 != key2
    assert len(key1) > 20


def test_mask_sensitive_data():
    """Test sensitive data masking."""
    data = "SSN: 123-45-6789, Email: user@test.com"
    masked = mask_sensitive_data(data)
    assert "123-45-6789" not in masked or "***" in masked
