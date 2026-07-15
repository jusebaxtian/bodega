import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad_account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ad_accounts.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|running|success|failed
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
