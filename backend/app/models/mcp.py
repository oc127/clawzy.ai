import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AgentMCPServer(Base):
    __tablename__ = "agent_mcp_servers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agents.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    transport: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 'stdio', 'http'
    command: Mapped[str | None] = mapped_column(Text, nullable=True)  # for stdio
    url: Mapped[str | None] = mapped_column(Text, nullable=True)  # for http
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    agent = relationship("Agent", backref="mcp_servers")
