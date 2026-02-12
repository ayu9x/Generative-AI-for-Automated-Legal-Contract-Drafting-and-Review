"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    """Test user registration."""
    response = await client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "securepass123",
        "full_name": "Test User",
        "organization": "Test Org",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["email"] == "newuser@example.com"
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration with duplicate email."""
    payload = {
        "email": "duplicate@example.com",
        "password": "securepass123",
        "full_name": "User One",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    """Test user login."""
    # Register first
    await client.post("/api/v1/auth/register", json={
        "email": "loginuser@example.com",
        "password": "securepass123",
        "full_name": "Login User",
    })

    # Login
    response = await client.post("/api/v1/auth/login", json={
        "email": "loginuser@example.com",
        "password": "securepass123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with wrong password."""
    await client.post("/api/v1/auth/register", json={
        "email": "wrongpass@example.com",
        "password": "correctpass",
        "full_name": "User",
    })

    response = await client.post("/api/v1/auth/login", json={
        "email": "wrongpass@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_profile(client: AsyncClient):
    """Test getting user profile."""
    # Register and get token
    reg_response = await client.post("/api/v1/auth/register", json={
        "email": "profile@example.com",
        "password": "securepass123",
        "full_name": "Profile User",
    })
    token = reg_response.json()["access_token"]

    # Get profile
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "profile@example.com"
    assert data["full_name"] == "Profile User"


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test accessing protected endpoint without auth."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 403  # No auth header


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    """Test token refresh."""
    reg_response = await client.post("/api/v1/auth/register", json={
        "email": "refresh@example.com",
        "password": "securepass123",
        "full_name": "Refresh User",
    })
    refresh_token = reg_response.json()["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
