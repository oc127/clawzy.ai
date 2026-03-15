"""Tests for authentication endpoints: register, login, refresh."""

import pytest
import pytest_asyncio


@pytest.mark.asyncio
class TestRegister:
    async def test_register_success(self, client):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "new@clawzy.ai",
            "password": "securepass",
            "name": "New User",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client, test_user):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "test@clawzy.ai",
            "password": "pass",
            "name": "Dup",
        })
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"].lower()

    async def test_register_invalid_email(self, client):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "pass",
            "name": "Bad",
        })
        assert resp.status_code == 422

    async def test_register_missing_fields(self, client):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "a@b.com",
        })
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client, test_user):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "test@clawzy.ai",
            "password": "password123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, client, test_user):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "test@clawzy.ai",
            "password": "wrongpass",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "nobody@clawzy.ai",
            "password": "pass",
        })
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestRefresh:
    async def test_refresh_success(self, client, test_user):
        # First login to get tokens
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "test@clawzy.ai",
            "password": "password123",
        })
        refresh_token = login_resp.json()["refresh_token"]

        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_with_access_token_fails(self, client, test_user_token):
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": test_user_token,  # access token, not refresh
        })
        assert resp.status_code == 401

    async def test_refresh_invalid_token(self, client):
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.here",
        })
        assert resp.status_code == 401
