import contextlib
import json
import logging
import os
import re
import shutil
import time

import docker
import httpx
from docker.errors import NotFound

from app.config import settings

# Validate agent_id to prevent path traversal
_SAFE_ID_RE = re.compile(r"^[a-f0-9\-]{36}$")

logger = logging.getLogger(__name__)


class DockerManager:
    def __init__(self):
        self._client: docker.DockerClient | None = None

    @property
    def client(self) -> docker.DockerClient:
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    def create_agent_container(
        self,
        agent_id: str,
        gateway_token: str,
        litellm_key: str,
        model_name: str,
        ws_port: int,
    ) -> str:
        """Create and start an OpenClaw container for a user's agent."""
        if not _SAFE_ID_RE.match(agent_id):
            raise ValueError(f"Invalid agent_id format: {agent_id}")

        # Generate per-agent config and write to host directory
        config = self._generate_agent_config(model_name, litellm_key)
        config_dir = os.path.join(settings.openclaw_agent_config_dir, agent_id)
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "openclaw.json")
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        # Create a workspace directory for the agent
        workspace_dir = os.path.join(config_dir, "workspace")
        os.makedirs(workspace_dir, exist_ok=True)

        container = self.client.containers.run(
            image=settings.openclaw_image,
            name=f"clawzy-agent-{agent_id}",
            detach=True,
            restart_policy={"Name": "unless-stopped"},
            environment={
                "OPENCLAW_GATEWAY_TOKEN": gateway_token,
                "OPENCLAW_ALLOW_INSECURE_PRIVATE_WS": "true",
            },
            ports={
                "18789/tcp": ("127.0.0.1", ws_port),
            },
            mem_limit="512m",
            cpu_quota=50000,
            network=settings.openclaw_network,
            volumes={
                config_dir: {
                    "bind": "/home/node/.openclaw",
                    "mode": "rw",
                },
                workspace_dir: {
                    "bind": "/home/node/workspace",
                    "mode": "rw",
                },
            },
            labels={
                "clawzy.agent_id": agent_id,
                "clawzy.managed": "true",
            },
        )
        return container.id

    def generate_agent_config(
        self,
        model_name: str,
        litellm_key: str,
        skill_slugs: list[str] | None = None,
    ) -> dict:
        """Generate a per-agent openclaw.json config."""
        config = {
            "gateway": {
                "auth": {"mode": "token"},
                "http": {
                    "endpoints": {
                        "chatCompletions": {"enabled": True},
                    },
                },
            },
            "models": {
                "mode": "merge",
                "providers": {
                    model_name: {
                        "baseUrl": "http://clawzy-litellm:4000/v1",
                        "apiKey": litellm_key,
                        "api": "openai-completions",
                        "models": [{"id": model_name}],
                    },
                },
            },
            "agents": {
                "defaults": {
                    "model": {"primary": f"{model_name}/{model_name}"},
                },
            },
        }

        # Inject installed skills into config
        if skill_slugs:
            config["skills"] = {
                "entries": {slug: {"enabled": True} for slug in skill_slugs},
            }
            config["plugins"] = {
                "entries": {slug: {"enabled": True} for slug in skill_slugs},
            }

        return config

    def _generate_agent_config(self, model_name: str, litellm_key: str) -> dict:
        """Backward-compatible wrapper."""
        return self.generate_agent_config(model_name, litellm_key)

    def restart_container(self, container_id: str, timeout: int = 10) -> None:
        """Restart a running container."""
        try:
            container = self.client.containers.get(container_id)
            container.restart(timeout=timeout)
        except NotFound as e:
            raise ValueError(f"Container {container_id} not found") from e

    def get_container_logs(self, container_id: str, tail: int = 50) -> str:
        """Get recent container logs."""
        try:
            container = self.client.containers.get(container_id)
            return container.logs(tail=tail, timestamps=True).decode("utf-8", errors="replace")
        except NotFound:
            return ""

    def get_container_health(self, container_id: str) -> dict:
        """Get detailed container health info."""
        try:
            container = self.client.containers.get(container_id)
            attrs = container.attrs
            state = attrs.get("State", {})
            health = state.get("Health", {})
            return {
                "status": container.status,
                "running": state.get("Running", False),
                "started_at": state.get("StartedAt"),
                "health_status": health.get("Status", "unknown"),
                "health_log": (health.get("Log") or [])[-3:],  # last 3 health checks
                "restart_count": attrs.get("RestartCount", 0),
            }
        except NotFound:
            return {"status": "not_found", "running": False}

    def stop_container(self, container_id: str) -> None:
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=10)
        except NotFound:
            pass

    def start_container(self, container_id: str) -> None:
        try:
            container = self.client.containers.get(container_id)
            container.start()
        except NotFound as e:
            raise ValueError(f"Container {container_id} not found") from e

    def remove_container(self, container_id: str, agent_id: str | None = None) -> None:
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=True)
        except NotFound:
            pass
        # Clean up config directory
        if agent_id:
            if not _SAFE_ID_RE.match(agent_id):
                logger.warning("Skipping cleanup for invalid agent_id: %s", agent_id)
                return
            config_dir = os.path.join(settings.openclaw_agent_config_dir, agent_id)
            with contextlib.suppress(OSError):
                shutil.rmtree(config_dir, ignore_errors=True)

    def get_container_status(self, container_id: str) -> str | None:
        try:
            container = self.client.containers.get(container_id)
            return container.status
        except NotFound:
            return None

    def wait_for_healthy(self, agent_id: str, timeout: int = 30) -> bool:
        """Poll the container's /healthz endpoint until it responds 200."""
        # Use Docker network container name (backend runs inside Docker)
        container_name = f"clawzy-agent-{agent_id}"
        url = f"http://{container_name}:18789/healthz"
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                resp = httpx.get(url, timeout=3.0)
                if resp.status_code == 200:
                    return True
            except (httpx.ConnectError, httpx.TimeoutException):
                pass
            time.sleep(2)
        return False


docker_manager = DockerManager()
