import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.harness import (
    PipelineCreate,
    PipelineDetailResponse,
    PipelineListResponse,
    PipelineResponse,
    PipelineStepResponse,
)
from app.services.harness_service import (
    cancel_pipeline,
    create_pipeline,
    get_pipeline_status,
    list_pipeline_steps,
    list_pipelines,
    run_pipeline,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/harness", tags=["harness"])


@router.post("/pipelines", response_model=PipelineDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline_endpoint(
    body: PipelineCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await create_pipeline(db, user.id, body.prompt)
    steps = await list_pipeline_steps(db, pipeline.id)
    resp = PipelineDetailResponse(
        id=pipeline.id,
        user_id=pipeline.user_id,
        title=pipeline.title,
        description=pipeline.description,
        status=pipeline.status,
        original_prompt=pipeline.original_prompt,
        plan=pipeline.plan,
        result_summary=pipeline.result_summary,
        total_steps=pipeline.total_steps,
        completed_steps=pipeline.completed_steps,
        created_at=pipeline.created_at,
        completed_at=pipeline.completed_at,
        steps=[PipelineStepResponse.model_validate(s) for s in steps],
    )
    return resp


@router.get("/pipelines", response_model=PipelineListResponse)
async def list_pipelines_endpoint(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipelines, total = await list_pipelines(db, user.id, offset=offset, limit=limit)
    return PipelineListResponse(
        pipelines=[PipelineResponse.model_validate(p) for p in pipelines],
        total=total,
    )


@router.get("/pipelines/{pipeline_id}", response_model=PipelineDetailResponse)
async def get_pipeline_endpoint(
    pipeline_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await get_pipeline_status(db, pipeline_id)
    if not pipeline or pipeline.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    steps = await list_pipeline_steps(db, pipeline_id)
    resp = PipelineDetailResponse(
        id=pipeline.id,
        user_id=pipeline.user_id,
        title=pipeline.title,
        description=pipeline.description,
        status=pipeline.status,
        original_prompt=pipeline.original_prompt,
        plan=pipeline.plan,
        result_summary=pipeline.result_summary,
        total_steps=pipeline.total_steps,
        completed_steps=pipeline.completed_steps,
        created_at=pipeline.created_at,
        completed_at=pipeline.completed_at,
        steps=[PipelineStepResponse.model_validate(s) for s in steps],
    )
    return resp


@router.post("/pipelines/{pipeline_id}/run", response_model=PipelineResponse)
async def run_pipeline_endpoint(
    pipeline_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await get_pipeline_status(db, pipeline_id)
    if not pipeline or pipeline.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    if pipeline.status not in ("ready", "planning"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pipeline cannot be run in status: {pipeline.status}",
        )

    pipeline.status = "running"
    await db.commit()

    async def _run_bg() -> None:
        from app.core.database import async_session as _session_factory

        async with _session_factory() as bg_db:
            await run_pipeline(bg_db, pipeline_id)

    asyncio.create_task(_run_bg())
    await db.refresh(pipeline)
    return PipelineResponse.model_validate(pipeline)


@router.post("/pipelines/{pipeline_id}/cancel", response_model=PipelineResponse)
async def cancel_pipeline_endpoint(
    pipeline_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await get_pipeline_status(db, pipeline_id)
    if not pipeline or pipeline.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    updated = await cancel_pipeline(db, pipeline_id)
    return PipelineResponse.model_validate(updated)


@router.get("/pipelines/{pipeline_id}/steps", response_model=list[PipelineStepResponse])
async def list_pipeline_steps_endpoint(
    pipeline_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await get_pipeline_status(db, pipeline_id)
    if not pipeline or pipeline.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    steps = await list_pipeline_steps(db, pipeline_id)
    return [PipelineStepResponse.model_validate(s) for s in steps]
