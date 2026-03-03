import uuid
from datetime import datetime, timezone
import enum

from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CreditReason(str, enum.Enum):
    signup_bonus = "signup_bonus"
    subscription = "subscription"
    topup = "topup"
    usage = "usage"
    refund = "refund"


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount: Mapped[int] = mapped_column(Integer)  # positive = credit, negative = debit
    balance_after: Mapped[int] = mapped_column(Integer)
    reason: Mapped[CreditReason] = mapped_column(SAEnum(CreditReason))
    model_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tokens_input: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_output: Mapped[int | None] = mapped_column(Integer, nullable=True)
    agent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    user = relationship("User", back_populates="credit_transactions")
