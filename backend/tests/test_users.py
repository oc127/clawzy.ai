"""Tests for user endpoints."""

import pytest


@pytest.mark.asyncio
async def test_get_me(client):
    # Register to get a token
    reg = await client.post("/api/v1/auth/register", json={
        "email": "me@example.com",
        "password": "password123",
        "name": "Me User",
    })
    token = reg.json()["access_token"]

    resp = await client.get("/api/v1/users/me", headers={
        "Authorization": f"Bearer {token}",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "me@example.com"
    assert data["name"] == "Me User"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_update_name(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "update@example.com",
        "password": "password123",
        "name": "Old Name",
    })
    token = reg.json()["access_token"]

    resp = await client.patch("/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "New Name"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_change_password(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "changepw@example.com",
        "password": "oldpassword",
        "name": "PW User",
    })
    token = reg.json()["access_token"]

    resp = await client.post("/api/v1/users/me/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "oldpassword", "new_password": "newpassword"},
    )
    assert resp.status_code == 200

    # Verify new password works
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "changepw@example.com",
        "password": "newpassword",
    })
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "wrongcurrent@example.com",
        "password": "password123",
        "name": "WC User",
    })
    token = reg.json()["access_token"]

    resp = await client.post("/api/v1/users/me/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "wrongone", "new_password": "newpassword"},
    )
    assert resp.status_code == 400
