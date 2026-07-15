import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CampaignScore(Base):
    __tablename__ = "campaign_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-100
    health_status: Mapped[str] = mapped_column(String, nullable=False)  # excelente|buena|atencion|critica
    computed_at: Mapped[datetime] = mapped_column(server_default=func.now())
