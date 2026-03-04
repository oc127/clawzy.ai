"""Tests for auth endpoints."""

import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    # First registration
    await client.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "password": "password123",
        "name": "User 1",
    })
    # Duplicate
    resp = await client.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "password": "password456",
        "name": "User 2",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client):
    # Register first
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "password": "password123",
        "name": "Login User",
    })
    # Login
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/v1/auth/register", json={
        "email": "wrongpw@example.com",
        "password": "password123",
        "name": "Wrong PW",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "wrongpw@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email(client):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "password123",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "refresh@example.com",
        "password": "password123",
        "name": "Refresh User",
    })
    tokens = reg.json()

    resp = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": tokens["refresh_token"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_refresh_invalid_token(client):
    resp = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": "invalid.token.here",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_forgot_password_always_200(client):
    # Should return 200 even for non-existent email (prevent enumeration)
    resp = await client.post("/api/v1/auth/forgot-password", json={
        "email": "noone@example.com",
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client):
    resp = await client.post("/api/v1/auth/reset-password", json={
        "token": "invalid-token",
        "new_password": "newpassword123",
    })
    assert resp.status_code == 400
