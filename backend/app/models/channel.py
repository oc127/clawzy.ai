import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AgentChannel(Base):
    __tablename__ = "agent_channels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agents.id", ondelete="CASCADE"), index=True
    )
    channel_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'telegram', 'line', 'discord'
    config: Mapped[dict] = mapped_column(JSON, nullable=False)  # bot_token, webhook_secret, etc.
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    agent = relationship("Agent", backref="channels")
