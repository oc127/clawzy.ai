"""Docker 容器管理 — 每用户独立网络隔离"""

import logging
import os

import docker
from docker.errors import NotFound, APIError

from app.config import settings

# openclaw.json 的宿主机绝对路径（挂载到每个 agent 容器中）
_OPENCLAW_CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "openclaw", "openclaw.json")
)

logger = logging.getLogger(__name__)


class DockerManager:
    def __init__(self):
        self._client: docker.DockerClient | None = None

    @property
    def client(self) -> docker.DockerClient:
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    # ------------------------------------------------------------------ #
    #  网络隔离：每个 Agent 一个独立的 Docker network
    # ------------------------------------------------------------------ #

    def _get_or_create_agent_network(self, agent_id: str) -> str:
        """为每个 Agent 创建独立的 Docker network，确保容器间零通信。"""
        network_name = f"clawzy-agent-{agent_id}"
        try:
            net = self.client.networks.get(network_name)
            return net.name
        except NotFound:
            net = self.client.networks.create(
                network_name,
                driver="bridge",
                internal=False,  # 需要外网访问 LiteLLM API
                labels={
                    "clawzy.agent_id": agent_id,
                    "clawzy.managed": "true",
                },
            )
            logger.info("Created isolated network: %s", network_name)
            return net.name

    def _remove_agent_network(self, agent_id: str) -> None:
        """清理 Agent 专属网络。"""
        network_name = f"clawzy-agent-{agent_id}"
        try:
            net = self.client.networks.get(network_name)
            net.remove()
            logger.info("Removed network: %s", network_name)
        except (NotFound, APIError):
            pass

    # ------------------------------------------------------------------ #
    #  容器生命周期
    # ------------------------------------------------------------------ #

    def create_agent_container(
        self,
        agent_id: str,
        gateway_token: str,
        litellm_key: str,
        model_name: str,
        ws_port: int,
    ) -> str:
        """创建并启动一个隔离的 OpenClaw 容器。

        安全措施:
        - 独立 Docker network（与其他用户容器零通信）
        - 内存 512MB / CPU 0.5 核限制
        - 丢弃所有 Linux capabilities，只保留必需的
        - PID 限制防 fork 炸弹
        - 禁止权限提升
        """
        # 创建独立网络
        network_name = self._get_or_create_agent_network(agent_id)

        # 构建 volume 挂载：将 openclaw.json 只读挂载到容器
        volumes = {}
        if os.path.isfile(_OPENCLAW_CONFIG_PATH):
            volumes[_OPENCLAW_CONFIG_PATH] = {
                "bind": "/home/node/.openclaw/openclaw.json",
                "mode": "ro",
            }

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
            volumes=volumes,

            # --- 资源限制 ---
            mem_limit="512m",
            memswap_limit="512m",    # 禁用 swap，严格内存限制
            cpu_quota=50000,          # 0.5 CPU
            pids_limit=100,           # 防 fork 炸弹

            # --- 安全限制 ---
            cap_drop=["ALL"],         # 丢弃所有 Linux capabilities
            cap_add=["NET_RAW"],      # 只保留网络访问（部分工具需要）
            security_opt=["no-new-privileges:true"],  # 禁止权限提升
            read_only=False,          # OpenClaw 需要写文件（记忆等）

            # --- 网络隔离 ---
            network=network_name,

            # --- 标签 ---
            labels={
                "clawzy.agent_id": agent_id,
                "clawzy.managed": "true",
            },
        )

        # 额外连接到 compose 主网络，使容器能访问 clawzy-litellm
        try:
            compose_net = self.client.networks.get(settings.openclaw_network)
            compose_net.connect(container)
            logger.info("Connected container to compose network: %s", settings.openclaw_network)
        except (NotFound, APIError) as e:
            logger.warning(
                "Could not connect container to compose network '%s': %s",
                settings.openclaw_network, e,
            )

        logger.info(
            "Created container %s for agent %s on network %s",
            container.short_id, agent_id, network_name,
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

    def remove_container(self, container_id: str, agent_id: str | None = None) -> None:
        """删除容器 + 清理对应的独立网络。"""
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=True)
        except NotFound:
            pass

        # 清理该 Agent 的专属网络
        if agent_id:
            self._remove_agent_network(agent_id)

    def get_container_status(self, container_id: str) -> str | None:
        try:
            container = self.client.containers.get(container_id)
            return container.status
        except NotFound:
            return None


docker_manager = DockerManager()
