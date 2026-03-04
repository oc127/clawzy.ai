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
    stripe_price_starter: str = "price_starter_monthly"
    stripe_price_pro: str = "price_pro_monthly"
    stripe_price_business: str = "price_business_monthly"

    # --- OpenClaw ---
    openclaw_image: str = "ghcr.io/openclaw/openclaw:latest"
    openclaw_network: str = "clawzy-network"
    openclaw_port_start: int = 19000
    openclaw_port_end: int = 19999

    # --- Credits ---
    signup_bonus_credits: int = 500

    # --- Self-Healing ---
    cb_failure_threshold: int = 5
    cb_recovery_timeout: int = 60
    cb_window_seconds: int = 300
    retry_max_attempts: int = 2
    retry_backoff_base: float = 1.0

    # --- Monitoring & Alerting ---
    alert_webhook_url: str = ""
    alert_error_rate_threshold: float = 0.3
    alert_cooldown_seconds: int = 300
    metrics_retention_hours: int = 24

    # --- Email (SMTP) ---
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@clawzy.ai"
    app_url: str = "https://clawzy.ai"

    # --- Sentry ---
    sentry_dsn: str = ""

    # --- Admin ---
    admin_api_key: str = ""

    # --- Telegram (Ops Agent) ---
    telegram_bot_token: str = ""
    telegram_admin_chat_id: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
