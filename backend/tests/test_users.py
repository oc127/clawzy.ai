"""Tests for user profile endpoints."""

import pytest


@pytest.mark.asyncio
class TestGetMe:
    async def test_get_me_success(self, client, auth_headers, test_user):
        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@clawzy.ai"
        assert data["name"] == "Test User"
        assert data["credit_balance"] == 500
        assert "password_hash" not in data

    async def test_get_me_no_auth(self, client):
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code in (401, 403)  # depends on FastAPI version

    async def test_get_me_invalid_token(self, client):
        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid.token"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestUpdateMe:
    async def test_update_name(self, client, auth_headers, test_user):
        resp = await client.patch(
            "/api/v1/users/me",
            json={"name": "Updated Name"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    async def test_update_avatar(self, client, auth_headers, test_user):
        resp = await client.patch(
            "/api/v1/users/me",
            json={"avatar_url": "https://example.com/avatar.png"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["avatar_url"] == "https://example.com/avatar.png"

    async def test_partial_update(self, client, auth_headers, test_user):
        # Only update name, avatar_url should remain unchanged
        resp = await client.patch(
            "/api/v1/users/me",
            json={"name": "Partial"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Partial"
