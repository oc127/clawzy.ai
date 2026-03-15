"""Tests for skills endpoints: listing, install, uninstall, toggle."""

import pytest

from app.core.security import create_access_token


@pytest.mark.asyncio
class TestListSkills:
    async def test_list_skills(self, client, auth_headers, test_skill):
        resp = await client.get("/api/v1/skills", headers=auth_headers)
        assert resp.status_code == 200
        skills = resp.json()
        assert len(skills) >= 1
        assert skills[0]["name"] == "Web Search"

    async def test_filter_by_category(self, client, auth_headers, test_skill):
        resp = await client.get("/api/v1/skills?category=search", headers=auth_headers)
        assert resp.status_code == 200
        assert all(s["category"] == "search" for s in resp.json())

    async def test_search(self, client, auth_headers, test_skill):
        resp = await client.get("/api/v1/skills?search=web", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_sort_by_newest(self, client, auth_headers, test_skill):
        resp = await client.get("/api/v1/skills?sort_by=newest", headers=auth_headers)
        assert resp.status_code == 200


@pytest.mark.asyncio
class TestGetCategories:
    async def test_get_categories(self, client, auth_headers, test_skill):
        resp = await client.get("/api/v1/skills/categories", headers=auth_headers)
        assert resp.status_code == 200
        cats = resp.json()
        assert "search" in cats


@pytest.mark.asyncio
class TestTrending:
    async def test_trending(self, client, auth_headers, test_skill):
        resp = await client.get("/api/v1/skills/trending", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


@pytest.mark.asyncio
class TestGetSkill:
    async def test_get_by_slug(self, client, auth_headers, test_skill):
        resp = await client.get("/api/v1/skills/web-search", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "web-search"
        assert data["description"]

    async def test_not_found(self, client, auth_headers):
        resp = await client.get("/api/v1/skills/nonexistent-slug", headers=auth_headers)
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestInstallSkill:
    async def test_install_success(self, client, auth_headers, test_agent, test_skill):
        resp = await client.post(
            f"/api/v1/skills/agents/{test_agent.id}/install",
            json={"skill_id": test_skill.id},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["skill"]["slug"] == "web-search"
        assert data["enabled"] is True

    async def test_install_duplicate(self, client, auth_headers, test_agent, test_skill):
        # Install first time
        await client.post(
            f"/api/v1/skills/agents/{test_agent.id}/install",
            json={"skill_id": test_skill.id},
            headers=auth_headers,
        )
        # Try again
        resp = await client.post(
            f"/api/v1/skills/agents/{test_agent.id}/install",
            json={"skill_id": test_skill.id},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "already" in resp.json()["detail"].lower()

    async def test_install_nonexistent_skill(self, client, auth_headers, test_agent):
        resp = await client.post(
            f"/api/v1/skills/agents/{test_agent.id}/install",
            json={"skill_id": "fake-skill-id"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    async def test_install_on_other_users_agent(self, client, test_agent, test_skill, second_user):
        token = create_access_token(second_user.id)
        resp = await client.post(
            f"/api/v1/skills/agents/{test_agent.id}/install",
            json={"skill_id": test_skill.id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
class TestUninstallSkill:
    async def test_uninstall_success(self, client, auth_headers, test_agent, test_skill):
        # Install first
        await client.post(
            f"/api/v1/skills/agents/{test_agent.id}/install",
            json={"skill_id": test_skill.id},
            headers=auth_headers,
        )
        # Uninstall
        resp = await client.delete(
            f"/api/v1/skills/agents/{test_agent.id}/uninstall/{test_skill.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204

    async def test_uninstall_not_installed(self, client, auth_headers, test_agent, test_skill):
        resp = await client.delete(
            f"/api/v1/skills/agents/{test_agent.id}/uninstall/{test_skill.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 400


@pytest.mark.asyncio
class TestToggleSkill:
    async def test_toggle_disable(self, client, auth_headers, test_agent, test_skill):
        # Install first
        await client.post(
            f"/api/v1/skills/agents/{test_agent.id}/install",
            json={"skill_id": test_skill.id},
            headers=auth_headers,
        )
        # Disable
        resp = await client.patch(
            f"/api/v1/skills/agents/{test_agent.id}/toggle/{test_skill.id}",
            json={"enabled": False},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

    async def test_toggle_enable(self, client, auth_headers, test_agent, test_skill):
        # Install and disable
        await client.post(
            f"/api/v1/skills/agents/{test_agent.id}/install",
            json={"skill_id": test_skill.id},
            headers=auth_headers,
        )
        await client.patch(
            f"/api/v1/skills/agents/{test_agent.id}/toggle/{test_skill.id}",
            json={"enabled": False},
            headers=auth_headers,
        )
        # Re-enable
        resp = await client.patch(
            f"/api/v1/skills/agents/{test_agent.id}/toggle/{test_skill.id}",
            json={"enabled": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True
