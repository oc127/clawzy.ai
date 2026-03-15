"""Tests for agent CRUD and lifecycle endpoints."""

import pytest

from app.core.security import create_access_token


@pytest.mark.asyncio
class TestListAgents:
    async def test_list_empty(self, client, auth_headers, test_user):
        resp = await client.get("/api/v1/agents", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_with_agent(self, client, auth_headers, test_agent):
        resp = await client.get("/api/v1/agents", headers=auth_headers)
        assert resp.status_code == 200
        agents = resp.json()
        assert len(agents) == 1
        assert agents[0]["name"] == "Test Agent"

    async def test_list_isolation(self, client, auth_headers, test_agent, second_user):
        """Other user's agents should not appear."""
        other_token = create_access_token(second_user.id)
        resp = await client.get(
            "/api/v1/agents",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []


@pytest.mark.asyncio
class TestCreateAgent:
    async def test_create_success(self, client, auth_headers, test_user):
        resp = await client.post("/api/v1/agents", json={
            "name": "My Agent",
            "model_name": "deepseek-chat",
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Agent"
        assert data["model_name"] == "deepseek-chat"
        assert data["status"] in ["running", "creating"]

    async def test_plan_limit_enforced(self, client, auth_headers, test_agent, test_user):
        """Free plan allows 1 agent. Creating a second should fail."""
        resp = await client.post("/api/v1/agents", json={
            "name": "Second Agent",
        }, headers=auth_headers)
        assert resp.status_code == 403
        assert "max" in resp.json()["detail"].lower() or "limit" in resp.json()["detail"].lower()


@pytest.mark.asyncio
class TestGetAgent:
    async def test_get_success(self, client, auth_headers, test_agent):
        resp = await client.get(
            f"/api/v1/agents/{test_agent.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == test_agent.id

    async def test_get_not_found(self, client, auth_headers):
        resp = await client.get(
            "/api/v1/agents/nonexistent-id",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_get_other_users_agent(self, client, test_agent, second_user):
        """Cannot access another user's agent."""
        token = create_access_token(second_user.id)
        resp = await client.get(
            f"/api/v1/agents/{test_agent.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestUpdateAgent:
    async def test_update_name(self, client, auth_headers, test_agent):
        resp = await client.patch(
            f"/api/v1/agents/{test_agent.id}",
            json={"name": "Renamed"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed"


@pytest.mark.asyncio
class TestDeleteAgent:
    async def test_delete_success(self, client, auth_headers, test_agent):
        resp = await client.delete(
            f"/api/v1/agents/{test_agent.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204

        # Verify it's gone
        resp2 = await client.get(
            f"/api/v1/agents/{test_agent.id}",
            headers=auth_headers,
        )
        assert resp2.status_code == 404

    async def test_delete_other_users_agent(self, client, test_agent, second_user):
        token = create_access_token(second_user.id)
        resp = await client.delete(
            f"/api/v1/agents/{test_agent.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestStartStopAgent:
    async def test_stop_running_agent(self, client, auth_headers, test_agent):
        resp = await client.post(
            f"/api/v1/agents/{test_agent.id}/stop",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "stopped"

    async def test_start_stopped_agent(self, client, auth_headers, test_agent):
        # Stop first
        await client.post(f"/api/v1/agents/{test_agent.id}/stop", headers=auth_headers)
        # Then start
        resp = await client.post(
            f"/api/v1/agents/{test_agent.id}/start",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"
