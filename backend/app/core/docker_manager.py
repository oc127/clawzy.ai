import json
import logging
import os

import docker
from docker.errors import NotFound

from app.config import settings

logger = logging.getLogger(__name__)

# Path inside the backend container where per-agent config dirs are written.
# Mapped from host path settings.agent_configs_host_path via docker-compose volume.
_CONFIGS_CONTAINER_PATH = "/app/agent_configs"

# LiteLLM URL reachable from inside per-agent containers (same Docker network)
_LITELLM_INTERNAL_URL = "http://clawzy-litellm:4000"


def _generate_openclaw_config(
    model_name: str,
    litellm_key: str,
    system_prompt: str | None = None,
) -> dict:
    """
    Generate an openclaw.json for a per-agent container.
    model_name e.g. "deepseek-chat", "deepseek-reasoner", "qwen-max"
    """
    is_reasoning = model_name in ("deepseek-reasoner",)
    agent_defaults: dict = {"model": {"primary": f"{model_name}/{model_name}"}}
    if system_prompt:
        agent_defaults["systemPrompt"] = system_prompt

    return {
        "models": {
            "mode": "merge",
            "providers": {
                model_name: {
                    "baseUrl": f"{_LITELLM_INTERNAL_URL}/v1",
                    "apiKey": litellm_key,
                    "api": "openai-completions",
                    "models": [
                        {
                            "id": model_name,
                            "name": model_name,
                            "reasoning": is_reasoning,
                            "input": ["text"],
                            "contextWindow": 65536,
                            "maxTokens": 8192,
                        }
                    ],
                }
            },
        },
        "agents": {"defaults": agent_defaults},
    }


class DockerManager:
    def __init__(self):
        self._client: docker.DockerClient | None = None

    @property
    def client(self) -> docker.DockerClient:
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    def _write_agent_config(
        self,
        agent_id: str,
        model_name: str,
        litellm_key: str,
        system_prompt: str | None = None,
    ) -> str:
        """
        Write openclaw.json to the per-agent config directory inside the backend container.

        Returns the HOST-side absolute path for bind-mounting into the per-agent container.
        The backend writes to _CONFIGS_CONTAINER_PATH/{agent_id}/ which is bind-mounted
        from settings.agent_configs_host_path on the host (see docker-compose.yml).
        """
        agent_dir = os.path.join(_CONFIGS_CONTAINER_PATH, agent_id)
        os.makedirs(agent_dir, exist_ok=True)
        config = _generate_openclaw_config(model_name, litellm_key, system_prompt)
        config_file = os.path.join(agent_dir, "openclaw.json")
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        host_path = os.path.join(
            settings.agent_configs_host_path, agent_id, "openclaw.json"
        )
        logger.info("Wrote openclaw.json for agent %s → host:%s", agent_id, host_path)
        return host_path

    def create_agent_container(
        self,
        agent_id: str,
        gateway_token: str,
        litellm_key: str,
        model_name: str,
        ws_port: int,
        system_prompt: str | None = None,
    ) -> str:
        """Create and start an OpenClaw container for a user's agent."""
        host_config_path = self._write_agent_config(
            agent_id, model_name, litellm_key, system_prompt
        )

        container = self.client.containers.run(
            image=settings.openclaw_image,
            name=f"clawzy-agent-{agent_id}",
            detach=True,
            restart_policy={"Name": "unless-stopped"},
            environment={
                "OPENCLAW_GATEWAY_TOKEN": gateway_token,
                "LITELLM_MASTER_KEY": litellm_key,
                "OPENCLAW_ALLOW_INSECURE_PRIVATE_WS": "true",
            },
            ports={
                "18789/tcp": ("127.0.0.1", ws_port),
            },
            volumes={
                host_config_path: {
                    "bind": "/home/node/.openclaw/openclaw.json",
                    "mode": "ro",
                },
            },
            network=settings.openclaw_network,
            mem_limit="512m",
            cpu_quota=50000,
            labels={
                "clawzy.agent_id": agent_id,
                "clawzy.managed": "true",
            },
        )
        return container.id

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

    def remove_container(self, container_id: str) -> None:
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=True)
        except NotFound:
            pass

    def get_container_status(self, container_id: str) -> str | None:
        try:
            container = self.client.containers.get(container_id)
            return container.status
        except NotFound:
            return None


docker_manager = DockerManager()
