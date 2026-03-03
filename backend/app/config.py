from pydantic_settings import BaseSettings


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

    # --- Credits ---
    signup_bonus_credits: int = 500

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
