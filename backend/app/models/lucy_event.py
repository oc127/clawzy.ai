import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LucyEvent(Base):
    __tablename__ = "lucy_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50))  # "github_webhook", "health_check", "scheduled", "custom"
    name: Mapped[str] = mapped_column(String(200))  # "Monitor my-repo", "Check API status"
    config: Mapped[dict] = mapped_column(JSON, default=dict)  # type-specific config
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    user = relationship("User", backref="lucy_events")


class LucyInitiative(Base):
    __tablename__ = "lucy_initiatives"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    initiative_type: Mapped[str] = mapped_column(String(50))  # "greeting", "reminder", "alert", "care", "event_report"
    message: Mapped[str] = mapped_column(Text)  # The message Lucy wants to send
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Additional context data
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user = relationship("User", backref="lucy_initiatives")
