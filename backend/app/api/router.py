from fastapi import APIRouter

from app.api.v1 import auth, users, agents, models, billing, chat, admin, usage_callback

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(agents.router)
api_router.include_router(models.router)
api_router.include_router(billing.router)
api_router.include_router(chat.router)
api_router.include_router(admin.router)
api_router.include_router(usage_callback.router)
