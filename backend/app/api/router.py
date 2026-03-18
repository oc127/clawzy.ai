from fastapi import APIRouter

from app.api.v1 import agents, auth, billing, chat, integrations, models, skills, users, webhooks

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(agents.router)
api_router.include_router(models.router)
api_router.include_router(billing.router)
api_router.include_router(chat.router)
api_router.include_router(skills.router)
api_router.include_router(integrations.router)
api_router.include_router(webhooks.router)
