import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Platform(str, enum.Enum):
    line = "line"
    discord = "discord"
    telegram = "telegram"


class Integration(Base):
    __tablename__ = "integrations"
    __table_args__ = (
        UniqueConstraint("agent_id", "platform", name="uq_agent_platform"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    platform: Mapped[Platform] = mapped_column(SAEnum(Platform))

    # Platform credentials (stored per integration)
    bot_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    channel_secret: Mapped[str | None] = mapped_column(Text, nullable=True)  # LINE channel secret
    channel_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)  # LINE channel access token

    # Webhook verification
    webhook_secret: Mapped[str] = mapped_column(String(64), default=lambda: uuid.uuid4().hex)

    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    agent = relationship("Agent", back_populates="integrations")
    user = relationship("User")
