from fastapi import APIRouter

from app.api.v1 import auth, users, agents, models, billing, chat, templates, clawhub, backup
from app.api.v1 import workspace, memories, tools
from app.api.v1 import skills, mcp, scheduler, approvals, channels, webhooks
from app.api.v1 import characters
from app.api.v1 import harness, schedule, files, onboarding

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(agents.router)
api_router.include_router(models.router)
api_router.include_router(billing.router)
api_router.include_router(chat.router)
api_router.include_router(templates.router)
api_router.include_router(clawhub.router)
api_router.include_router(backup.router)
api_router.include_router(workspace.router)
api_router.include_router(memories.router)
api_router.include_router(tools.router)
api_router.include_router(skills.router)
api_router.include_router(skills.builtin_router)
api_router.include_router(mcp.router)
api_router.include_router(scheduler.router)
api_router.include_router(approvals.router)
api_router.include_router(channels.router)
api_router.include_router(webhooks.router)
api_router.include_router(characters.router)
api_router.include_router(harness.router)
api_router.include_router(schedule.router)
api_router.include_router(files.router)
api_router.include_router(onboarding.router)
