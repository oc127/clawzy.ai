from fastapi import APIRouter

from app.schemas.billing import ModelInfo
from app.services.model_service import get_available_models

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[ModelInfo])
async def list_models():
    return get_available_models()
