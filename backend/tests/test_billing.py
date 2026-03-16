"""Tests for billing endpoints: credits, plans, subscribe."""

import pytest


@pytest.mark.asyncio
class TestGetCredits:
    async def test_get_credits(self, client, auth_headers, test_user):
        resp = await client.get("/api/v1/billing/credits", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["balance"] == 500
        assert data["used_this_period"] == 0
        assert data["plan"] == "free"


@pytest.mark.asyncio
class TestGetTransactions:
    async def test_empty_transactions(self, client, auth_headers, test_user):
        resp = await client.get("/api/v1/billing/credits/transactions", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_pagination(self, client, auth_headers, test_user):
        resp = await client.get(
            "/api/v1/billing/credits/transactions?limit=5&offset=0",
            headers=auth_headers,
        )
        assert resp.status_code == 200


@pytest.mark.asyncio
class TestListPlans:
    async def test_list_plans(self, client, auth_headers):
        resp = await client.get("/api/v1/billing/plans")
        assert resp.status_code == 200
        plans = resp.json()
        assert len(plans) == 4
        ids = [p["id"] for p in plans]
        assert "free" in ids
        assert "starter" in ids
        assert "pro" in ids
        assert "business" in ids

    async def test_plan_structure(self, client):
        resp = await client.get("/api/v1/billing/plans")
        plan = resp.json()[0]
        assert "id" in plan
        assert "name" in plan
        assert "price_monthly" in plan
        assert "credits_included" in plan
        assert "max_agents" in plan


@pytest.mark.asyncio
class TestSubscribe:
    async def test_upgrade_plan(self, client, auth_headers, test_user):
        resp = await client.post(
            "/api/v1/billing/subscribe",
            json={"plan": "pro"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] == "pro"

        # Credits should have increased
        credits_resp = await client.get("/api/v1/billing/credits", headers=auth_headers)
        assert credits_resp.json()["balance"] == 500 + 8000  # original + pro credits
        assert credits_resp.json()["plan"] == "pro"

    async def test_subscribe_invalid_plan(self, client, auth_headers, test_user):
        resp = await client.post(
            "/api/v1/billing/subscribe",
            json={"plan": "nonexistent"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    async def test_subscribe_same_plan(self, client, auth_headers, test_user):
        # Subscribe to starter
        await client.post(
            "/api/v1/billing/subscribe",
            json={"plan": "starter"},
            headers=auth_headers,
        )
        # Try again
        resp = await client.post(
            "/api/v1/billing/subscribe",
            json={"plan": "starter"},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "already" in resp.json()["detail"].lower()
