"""Tools API — web fetch and sandbox code execution."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.docker_manager import docker_manager
from app.deps import get_current_user
from app.models.user import User
from app.services.agent_service import get_agent
from app.services.web_fetch_service import web_fetch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["tools"])


# ---------- Web Fetch ----------

class WebFetchRequest(BaseModel):
    url: HttpUrl


class WebFetchResponse(BaseModel):
    url: str
    content: str
    title: str = ""
    type: str = "text"
    error: str | None = None


@router.post("/web-fetch", response_model=WebFetchResponse)
async def fetch_web_page(
    body: WebFetchRequest,
    user: User = Depends(get_current_user),
):
    result = await web_fetch(str(body.url))
    return WebFetchResponse(**result)


# ---------- Sandbox Code Execution ----------

class CodeExecRequest(BaseModel):
    agent_id: str
    code: str
    language: str = "python"
    timeout: int = 30


class CodeExecResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int


@router.post("/exec", response_model=CodeExecResponse)
async def execute_code(
    body: CodeExecRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await get_agent(db, body.agent_id, user.id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    if not agent.container_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent has no running container")

    try:
        container = docker_manager.client.containers.get(agent.container_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Container not found")

    if body.language == "python":
        cmd = ["python3", "-c", body.code]
    elif body.language == "bash":
        cmd = ["bash", "-c", body.code]
    elif body.language == "node":
        cmd = ["node", "-e", body.code]
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported language: {body.language}")

    try:
        exec_result = container.exec_run(
            cmd,
            workdir="/home/node/workspace",
            demux=True,
            environment={"PYTHONDONTWRITEBYTECODE": "1"},
        )
        stdout = (exec_result.output[0] or b"").decode("utf-8", errors="replace") if exec_result.output else ""
        stderr = (exec_result.output[1] or b"").decode("utf-8", errors="replace") if exec_result.output and len(exec_result.output) > 1 else ""
        return CodeExecResponse(
            stdout=stdout[:10000],
            stderr=stderr[:5000],
            exit_code=exec_result.exit_code or 0,
        )
    except Exception as e:
        logger.exception("Code execution failed for agent %s", body.agent_id)
        return CodeExecResponse(stdout="", stderr=str(e), exit_code=1)
