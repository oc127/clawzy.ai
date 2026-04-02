"""Workspace service — async file operations inside agent Docker containers."""

import logging

from app.core.docker_manager import docker_manager

logger = logging.getLogger(__name__)

# Default workspace root inside the container
WORKSPACE_ROOT = "/home/node/workspace"

# Directories created on workspace init
_INIT_DIRS = ["memory", "skills"]
_INIT_FILES = {
    "MEMORY.md": "# Agent Memory\n\nThis file stores persistent notes and context.\n",
}


async def _exec(container_id: str, cmd: list[str]) -> tuple[int, str]:
    """Run a command inside the agent container (non-blocking)."""
    exit_code, output_bytes = await docker_manager.exec_in_container(container_id, cmd)
    return exit_code, output_bytes.decode("utf-8", errors="replace")


async def init_workspace(container_id: str) -> None:
    """Create default workspace directories and files."""
    await _exec(container_id, ["mkdir", "-p", WORKSPACE_ROOT])

    for dirname in _INIT_DIRS:
        await _exec(container_id, ["mkdir", "-p", f"{WORKSPACE_ROOT}/{dirname}"])

    for filename, content in _INIT_FILES.items():
        filepath = f"{WORKSPACE_ROOT}/{filename}"
        exit_code, _ = await _exec(container_id, ["test", "-f", filepath])
        if exit_code != 0:
            await _exec(container_id, ["sh", "-c", f"cat > {filepath} << 'CLAWZY_EOF'\n{content}\nCLAWZY_EOF"])

    logger.info("Initialized workspace for container %s", container_id)


async def list_files(container_id: str, path: str = WORKSPACE_ROOT) -> list[dict]:
    """List files and directories at the given path inside the container."""
    exit_code, output = await _exec(container_id, [
        "find", path, "-maxdepth", "1", "-mindepth", "1",
        "-printf", "%y|%s|%f\n",
    ])

    if exit_code != 0:
        exit_code, output = await _exec(container_id, ["ls", "-la", path])
        if exit_code != 0:
            return []
        entries = []
        for line in output.strip().splitlines()[1:]:
            parts = line.split(None, 8)
            if len(parts) >= 9:
                is_dir = parts[0].startswith("d")
                entries.append({
                    "name": parts[8],
                    "type": "directory" if is_dir else "file",
                    "size": int(parts[4]) if not is_dir else 0,
                })
        return entries

    entries = []
    for line in output.strip().splitlines():
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            file_type, size, name = parts
            entries.append({
                "name": name,
                "type": "directory" if file_type == "d" else "file",
                "size": int(size) if file_type != "d" else 0,
            })
    return entries


async def read_file(container_id: str, path: str) -> str:
    """Read file content from the container."""
    exit_code, output = await _exec(container_id, ["cat", path])
    if exit_code != 0:
        raise FileNotFoundError(f"File not found or unreadable: {path}")
    return output


async def write_file(container_id: str, path: str, content: str) -> None:
    """Write content to a file inside the container."""
    parent = "/".join(path.rsplit("/", 1)[:-1]) or "/"
    await _exec(container_id, ["mkdir", "-p", parent])
    await _exec(container_id, ["sh", "-c", f"cat > {path} << 'CLAWZY_EOF'\n{content}\nCLAWZY_EOF"])
    logger.debug("Wrote file %s in container %s", path, container_id)


async def delete_file(container_id: str, path: str) -> None:
    """Delete a file or empty directory inside the container."""
    if path.rstrip("/") == WORKSPACE_ROOT.rstrip("/"):
        raise ValueError("Cannot delete workspace root")
    exit_code, output = await _exec(container_id, ["rm", "-rf", path])
    if exit_code != 0:
        raise FileNotFoundError(f"Failed to delete: {path}")
    logger.debug("Deleted %s in container %s", path, container_id)
