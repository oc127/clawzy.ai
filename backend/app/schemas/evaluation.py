from datetime import datetime
from pydantic import BaseModel


class EvaluationRequest(BaseModel):
    conversation_id: str
    agent_id: str | None = None


class EvaluationResponse(BaseModel):
    id: str
    user_id: str
    agent_id: str | None
    conversation_id: str | None
    score: float | None
    relevance_score: float | None
    coherence_score: float | None
    helpfulness_score: float | None
    summary: str | None
    patterns_found: list | None
    improvement_suggestions: list | None
    skill_extracted: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ImprovementRequest(BaseModel):
    agent_id: str | None = None
    max_conversations: int = 20


class ImprovementReport(BaseModel):
    user_id: str
    period_days: int
    total_evaluations: int
    avg_score: float | None
    top_patterns: list[str]
    skills_extracted: int
    recommendations: list[str]
    generated_at: datetime
