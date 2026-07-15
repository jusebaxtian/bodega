import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad_account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ad_accounts.id", ondelete="CASCADE"))
    entity_type: Mapped[str] = mapped_column(String, nullable=False)  # 'campaign'|'ad_set'|'ad'
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    rule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rules.id", ondelete="CASCADE"))
    priority: Mapped[str] = mapped_column(String, nullable=False)  # alta|media|baja
    title: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-100
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")  # pending|applied_by_user|dismissed
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)
