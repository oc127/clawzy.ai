import logging

import docker
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

    def get_container_status(self, container_id: str) -> str | None:
        try:
            container = self.client.containers.get(container_id)
            return container.status
        except NotFound:
            return None

    async def run_sandbox(self, language: str, code: str, timeout: int = 30) -> dict:
        """Run code in an ephemeral sandbox container."""
        image_map = {
            "python": "python:3.12-slim",
            "node": "node:20-slim",
            "bash": "ubuntu:22.04",
        }
        image = image_map.get(language, "ubuntu:22.04")

        if language == "python":
            cmd = ["python", "-c", code]
        elif language == "node":
            cmd = ["node", "-e", code]
        else:
            cmd = ["bash", "-c", code]

        container = self.client.containers.run(
            image,
            cmd,
            detach=True,
            mem_limit="256m",
            network_disabled=True,
            remove=False,
        )

        try:
            result = container.wait(timeout=timeout)
            stdout = container.logs(stdout=True, stderr=False).decode()
            stderr = container.logs(stdout=False, stderr=True).decode()
            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": result.get("StatusCode", -1),
            }
        except Exception as e:
            container.kill()
            return {"stdout": "", "stderr": str(e), "exit_code": -1}
        finally:
            container.remove(force=True)


docker_manager = DockerManager()
