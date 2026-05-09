import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LucyTask(Base):
    __tablename__ = "lucy_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(String(30))  # code_review, research, analysis, generation, custom
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, running, completed, failed, cancelled
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100

    result: Mapped[str | None] = mapped_column(Text, nullable=True)  # Completed output (markdown)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Error message if failed
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Task-specific config

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    user = relationship("User", backref="lucy_tasks")
