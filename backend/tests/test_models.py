"""Tests for models endpoint."""

import pytest


@pytest.mark.asyncio
class TestListModels:
    async def test_list_models(self, client):
        resp = await client.get("/api/v1/models")
        assert resp.status_code == 200
        models = resp.json()
        assert len(models) == 10

    async def test_model_structure(self, client):
        resp = await client.get("/api/v1/models")
        model = resp.json()[0]
        assert "id" in model
        assert "name" in model
        assert "provider" in model
        assert "tier" in model
        assert "credits_per_1k_input" in model
        assert "credits_per_1k_output" in model
        assert "description" in model

    async def test_known_models_present(self, client):
        resp = await client.get("/api/v1/models")
        ids = [m["id"] for m in resp.json()]
        assert "deepseek-chat" in ids
        assert "claude-sonnet" in ids
        assert "gpt-4o" in ids
        assert "gemini-flash" in ids

    async def test_no_auth_required(self, client):
        """Models endpoint should be public."""
        resp = await client.get("/api/v1/models")
        assert resp.status_code == 200


@pytest.mark.asyncio
class TestHealthCheck:
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["service"] == "clawzy-backend"
