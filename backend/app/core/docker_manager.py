import json
import logging
import os
import time

import docker
import httpx
from docker.errors import NotFound

from app.config import settings

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
        # Generate per-agent config and write to host directory
        config = self._generate_agent_config(model_name, litellm_key)
        config_dir = os.path.join(settings.openclaw_agent_config_dir, agent_id)
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "openclaw.json")
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        container = self.client.containers.run(
            image=settings.openclaw_image,
            name=f"clawzy-agent-{agent_id}",
            command="gateway start --foreground",
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
                config_path: {
                    "bind": "/home/node/.openclaw/openclaw.json",
                    "mode": "ro",
                },
            },
            labels={
                "clawzy.agent_id": agent_id,
                "clawzy.managed": "true",
            },
        )
        return container.id

    def _generate_agent_config(self, model_name: str, litellm_key: str) -> dict:
        """Generate a per-agent openclaw.json config."""
        return {
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
            config_dir = os.path.join(settings.openclaw_agent_config_dir, agent_id)
            config_path = os.path.join(config_dir, "openclaw.json")
            try:
                os.remove(config_path)
                os.rmdir(config_dir)
            except OSError:
                pass

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
