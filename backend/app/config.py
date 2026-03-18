import logging
import sys

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # --- App ---
    app_name: str = "Clawzy.ai"
    debug: bool = False

    # --- Database ---
    database_url: str = "postgresql+asyncpg://clawzy:clawzy@localhost:5432/clawzy"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- JWT ---
    jwt_secret: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7

    # --- LiteLLM ---
    litellm_url: str = "http://localhost:4000"
    litellm_master_key: str = "sk-clawzy-change-me"

    # --- Stripe ---
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # --- OpenClaw ---
    openclaw_image: str = "ghcr.io/openclaw/openclaw:latest"
    openclaw_network: str = "clawzy-network"
    openclaw_port_start: int = 19000
    openclaw_port_end: int = 19999
    openclaw_gateway_url: str = "http://localhost:18789"
    openclaw_gateway_token: str = ""
    openclaw_agent_config_dir: str = "/var/lib/clawzy/agents"

    # --- CORS ---
    cors_origins: str = "*"  # comma-separated origins, or "*" for dev

    # --- Rate Limiting ---
    rate_limit_per_minute: int = 60
    rate_limit_auth_per_minute: int = 10

    # --- Credits ---
    signup_bonus_credits: int = 500

    # --- OAuth ---
    github_client_id: str = ""
    github_client_secret: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    oauth_redirect_base_url: str = ""  # e.g. https://clawzy.ai

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# Startup security checks
_INSECURE_SECRETS = {"change-me-jwt-secret", "", "secret", "test"}
if settings.jwt_secret in _INSECURE_SECRETS:
    if settings.debug:
        logger.warning(
            "WARNING: Using insecure JWT_SECRET in debug mode. Set JWT_SECRET environment variable for production."
        )
    else:
        logger.critical("FATAL: JWT_SECRET is not set or using default value. Generate one with: openssl rand -hex 32")
        sys.exit(1)

if settings.litellm_master_key in {"sk-clawzy-change-me", ""} and not settings.debug:
    logger.warning("WARNING: LITELLM_MASTER_KEY is using default value. Generate one with: openssl rand -hex 16")
