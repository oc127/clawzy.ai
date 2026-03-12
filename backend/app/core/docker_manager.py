import docker
from docker.errors import NotFound

from app.config import settings


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
        container = self.client.containers.run(
            image=settings.openclaw_image,
            name=f"clawzy-agent-{agent_id[:12]}",
            detach=True,
            restart_policy={"Name": "unless-stopped"},
            environment={
                "OPENCLAW_GATEWAY_TOKEN": gateway_token,
                "OPENCLAW_GATEWAY_BIND": "lan",
                "OPENCLAW_ALLOW_INSECURE_PRIVATE_WS": "true",
                "LITELLM_MASTER_KEY": litellm_key,
            },
            network=settings.openclaw_network,
            volumes={
                "/opt/clawzy/openclaw/openclaw.json": {
                    "bind": "/home/node/.openclaw/openclaw.json",
                    "mode": "ro",
                },
            },
            mem_limit="512m",
            cpu_quota=50000,
            labels={
                "clawzy.agent_id": agent_id,
                "clawzy.managed": "true",
            },
        )
        return container.id

    def get_container_ip(self, container_id: str) -> str | None:
        """Get a container's IP address on the openclaw network."""
        try:
            container = self.client.containers.get(container_id)
            networks = container.attrs["NetworkSettings"]["Networks"]
            net = networks.get(settings.openclaw_network)
            if net:
                return net["IPAddress"]
            # Fallback: return first available IP
            for net_info in networks.values():
                if net_info.get("IPAddress"):
                    return net_info["IPAddress"]
        except (NotFound, KeyError):
            pass
        return None

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
