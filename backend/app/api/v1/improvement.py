from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.evaluation import EvaluationRequest, EvaluationResponse, ImprovementRequest, ImprovementReport
from app.services import improvement_service
from sqlalchemy import select
from app.models.evaluation import ConversationEvaluation

router = APIRouter(prefix="/improvement", tags=["improvement"])


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_conversation(
    req: EvaluationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Evaluate a conversation and store the result."""
    try:
        evaluation = await improvement_service.evaluate_response(
            conversation_id=req.conversation_id,
            user_id=current_user.id,
            agent_id=req.agent_id,
            db=db,
        )
        return evaluation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/evaluations", response_model=list[EvaluationResponse])
async def list_evaluations(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recent evaluations for the current user."""
    result = await db.execute(
        select(ConversationEvaluation)
        .where(ConversationEvaluation.user_id == current_user.id)
        .order_by(ConversationEvaluation.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/improve")
async def run_improvement(
    req: ImprovementRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run an improvement cycle: extract patterns and improve skills."""
    result = await improvement_service.run_improvement_cycle(
        user_id=current_user.id,
        agent_id=req.agent_id,
        db=db,
    )
    return result


@router.get("/report")
async def get_improvement_report(
    period_days: int = 7,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get improvement report for the current user."""
    return await improvement_service.generate_improvement_report(
        user_id=current_user.id,
        db=db,
        period_days=period_days,
    )
