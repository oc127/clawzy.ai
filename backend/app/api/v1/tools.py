"""Tools API — web fetch and sandbox code execution."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl

from app.core.docker_manager import docker_manager
from app.deps import get_current_user
from app.models.user import User
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
    language: str = "python"
    code: str


class CodeExecResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int


@router.post("/exec", response_model=CodeExecResponse)
async def execute_code(
    body: CodeExecRequest,
    user: User = Depends(get_current_user),
):
    supported = {"python", "node", "bash"}
    if body.language not in supported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language: {body.language}",
        )

    result = await docker_manager.run_sandbox(
        language=body.language,
        code=body.code,
    )

    return CodeExecResponse(
        stdout=result["stdout"][:10000],
        stderr=result["stderr"][:5000],
        exit_code=result["exit_code"],
    )
