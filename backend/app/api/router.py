from fastapi import APIRouter

from app.api.v1 import agents, auth, billing, chat, line_webhook, memory, models, skills, subtasks, tools, users

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(agents.router)
api_router.include_router(models.router)
api_router.include_router(billing.router)
api_router.include_router(chat.router)
api_router.include_router(skills.router)
api_router.include_router(memory.router)
api_router.include_router(tools.router)
api_router.include_router(subtasks.router)
api_router.include_router(line_webhook.router)
