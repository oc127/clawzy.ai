"""Docker container management with async wrappers.

All Docker SDK calls run in a thread pool via asyncio.to_thread()
to avoid blocking the FastAPI event loop.
"""

import asyncio

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

    # ── Sync methods (called via to_thread) ─────────────────────────

    def _create_agent_container(
        self,
        agent_id: str,
        gateway_token: str,
        litellm_key: str,
        model_name: str,
        ws_port: int,
    ) -> str:
        container = self.client.containers.run(
            image=settings.openclaw_image,
            name=f"clawzy-agent-{agent_id}",
            detach=True,
            restart_policy={"Name": "unless-stopped"},
            environment={
                "OPENCLAW_GATEWAY_TOKEN": gateway_token,
            },
            ports={
                "18789/tcp": ("127.0.0.1", ws_port),
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

    def _stop_container(self, container_id: str) -> None:
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=10)
        except NotFound:
            pass

    def _start_container(self, container_id: str) -> None:
        try:
            container = self.client.containers.get(container_id)
            container.start()
        except NotFound as e:
            raise ValueError(f"Container {container_id} not found") from e

    def _remove_container(self, container_id: str) -> None:
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=True)
        except NotFound:
            pass

    def _get_container_status(self, container_id: str) -> str | None:
        try:
            container = self.client.containers.get(container_id)
            return container.status
        except NotFound:
            return None

    def _exec_in_container(self, container_id: str, cmd: list[str]) -> tuple[int, bytes]:
        container = self.client.containers.get(container_id)
        exit_code, output = container.exec_run(cmd, demux=False)
        return exit_code, output or b""

    # ── Async wrappers (safe for FastAPI event loop) ────────────────

    async def create_agent_container(self, **kwargs) -> str:
        return await asyncio.to_thread(self._create_agent_container, **kwargs)

    async def stop_container(self, container_id: str) -> None:
        await asyncio.to_thread(self._stop_container, container_id)

    async def start_container(self, container_id: str) -> None:
        await asyncio.to_thread(self._start_container, container_id)

    async def remove_container(self, container_id: str) -> None:
        await asyncio.to_thread(self._remove_container, container_id)

    async def get_container_status(self, container_id: str) -> str | None:
        return await asyncio.to_thread(self._get_container_status, container_id)

    async def exec_in_container(self, container_id: str, cmd: list[str]) -> tuple[int, bytes]:
        return await asyncio.to_thread(self._exec_in_container, container_id, cmd)


docker_manager = DockerManager()
