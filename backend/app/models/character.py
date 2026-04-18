import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, Boolean, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CharacterTemplate(Base):
    __tablename__ = "character_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50))
    name_reading: Mapped[str | None] = mapped_column(String(50), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    personality_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    personality_traits: Mapped[list | None] = mapped_column(JSON, nullable=True)
    speaking_style: Mapped[str | None] = mapped_column(String(200), nullable=True)
    catchphrase: Mapped[str | None] = mapped_column(String(200), nullable=True)
    interests: Mapped[list | None] = mapped_column(JSON, nullable=True)
    backstory: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    greeting_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sample_dialogues: Mapped[list | None] = mapped_column(JSON, nullable=True)
    avatar_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="healing")
    is_preset: Mapped[bool] = mapped_column(Boolean, default=True)
    creator_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
