"""Tests for health endpoints."""

import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_health_returns_service_name(client):
    resp = await client.get("/health")
    data = resp.json()
    assert data["service"] == "clawzy-backend"
