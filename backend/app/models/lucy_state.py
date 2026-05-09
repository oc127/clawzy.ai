import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LucyState(Base):
    __tablename__ = "lucy_states"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, index=True)

    # Personality
    personality_type: Mapped[str] = mapped_column(String(20), default="少女")  # 少女, 御姐, custom
    custom_personality_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Emotional state
    mood: Mapped[str] = mapped_column(String(20), default="neutral")  # happy, neutral, thinking, shy, excited, tired, sad
    affection: Mapped[int] = mapped_column(Integer, default=0)  # 0-100

    # Interaction tracking
    interaction_streak: Mapped[int] = mapped_column(Integer, default=0)
    total_interactions: Mapped[int] = mapped_column(Integer, default=0)
    last_interaction_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Unlockables
    unlocked_expressions: Mapped[dict] = mapped_column(JSON, default=list)  # ["smile", "shy", "angry", ...]

    # Soul files content (stored in DB, synced to markdown format for prompt assembly)
    soul_md: Mapped[str] = mapped_column(Text, default="")
    persona_md: Mapped[str] = mapped_column(Text, default="")
    taste_md: Mapped[str] = mapped_column(Text, default="")

    # Model preference
    preferred_model: Mapped[str] = mapped_column(String(100), default="deepseek-chat")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    user = relationship("User", backref="lucy_state")
