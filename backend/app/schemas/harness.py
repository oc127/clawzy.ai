from datetime import datetime
from pydantic import BaseModel


class PipelineStepResponse(BaseModel):
    id: str
    pipeline_id: str
    agent_id: str | None = None
    step_order: int
    title: str
    description: str | None = None
    status: str
    agent_role: str
    input_data: dict | None = None
    output_data: dict | None = None
    evaluation_score: float | None = None
    evaluation_notes: str | None = None
    depends_on: list | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PipelineResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: str | None = None
    status: str
    original_prompt: str | None = None
    plan: dict | None = None
    result_summary: str | None = None
    total_steps: int
    completed_steps: int
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class PipelineDetailResponse(PipelineResponse):
    steps: list[PipelineStepResponse] = []


class PipelineCreate(BaseModel):
    prompt: str


class PipelineListResponse(BaseModel):
    pipelines: list[PipelineResponse]
    total: int
