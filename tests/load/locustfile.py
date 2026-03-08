"""Clawzy.ai — Locust Load Test

Interactive load testing with Web UI.
Run: locust -f tests/load/locustfile.py --host http://localhost:8000

Environment variables:
  LOCUST_TEST_EMAIL    - Test account email (default: loadtest@clawzy.ai)
  LOCUST_TEST_PASSWORD - Test account password (default: loadtest123)
"""

import os
import json
import logging

from locust import HttpUser, task, between, events

logger = logging.getLogger(__name__)

TEST_EMAIL = os.getenv("LOCUST_TEST_EMAIL", "loadtest@clawzy.ai")
TEST_PASSWORD = os.getenv("LOCUST_TEST_PASSWORD", "loadtest123")


class ClawzyUser(HttpUser):
    """Simulates a typical Clawzy.ai user workflow."""

    wait_time = between(1, 3)

    def on_start(self):
        """Login and store JWT token."""
        self.token = None
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            name="/api/v1/auth/login",
        )
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token")
            logger.info("Login succeeded")
        else:
            logger.warning("Login failed: HTTP %d", resp.status_code)

    @property
    def auth_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(5)
    def health_check(self):
        """Basic health check — lightweight baseline."""
        self.client.get("/health", name="/health")

    @task(3)
    def status_page(self):
        """Public status page."""
        self.client.get("/status", name="/status")

    @task(4)
    def list_agents(self):
        """List user's agents."""
        if not self.token:
            return
        self.client.get(
            "/api/v1/agents",
            headers=self.auth_headers,
            name="/api/v1/agents",
        )

    @task(3)
    def list_models(self):
        """List available models."""
        if not self.token:
            return
        self.client.get(
            "/api/v1/models",
            headers=self.auth_headers,
            name="/api/v1/models",
        )

    @task(1)
    def login_flow(self):
        """Simulate a fresh login."""
        self.client.post(
            "/api/v1/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            name="/api/v1/auth/login",
        )

    @task(2)
    def deep_health(self):
        """Deep health check (heavier)."""
        self.client.get("/health/deep", name="/health/deep")


class ClawzyAdmin(HttpUser):
    """Simulates admin monitoring patterns — lower frequency."""

    wait_time = between(5, 10)
    weight = 1  # 1/10 of ClawzyUser traffic

    def on_start(self):
        self.admin_key = os.getenv("ADMIN_API_KEY", "")
        if not self.admin_key:
            logger.warning("ADMIN_API_KEY not set, admin tasks will fail")

    @property
    def admin_headers(self):
        return {"X-Admin-Key": self.admin_key}

    @task(3)
    def check_metrics(self):
        """Pull system metrics."""
        if not self.admin_key:
            return
        self.client.get(
            "/admin/metrics",
            headers=self.admin_headers,
            name="/admin/metrics",
        )

    @task(2)
    def check_health(self):
        """Admin deep health check."""
        if not self.admin_key:
            return
        self.client.get(
            "/admin/health",
            headers=self.admin_headers,
            name="/admin/health",
        )

    @task(1)
    def check_stats(self):
        """System stats."""
        if not self.admin_key:
            return
        self.client.get(
            "/admin/stats",
            headers=self.admin_headers,
            name="/admin/stats",
        )

    @task(1)
    def prometheus_metrics(self):
        """Prometheus metrics endpoint."""
        if not self.admin_key:
            return
        self.client.get(
            "/admin/metrics/prometheus",
            headers=self.admin_headers,
            name="/admin/metrics/prometheus",
        )
