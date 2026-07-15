import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InsightSnapshot(Base):
    """Una fila = un anuncio, un día. Es la base para detectar tendencias
    (fatiga, caída de CTR, incremento de CPL) en el motor de reglas (Módulo 3)."""

    __tablename__ = "insight_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ads.id", ondelete="CASCADE"))
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)

    spend: Mapped[float] = mapped_column(Numeric, default=0)
    impressions: Mapped[int] = mapped_column(default=0)
    clicks: Mapped[int] = mapped_column(default=0)
    ctr: Mapped[float] = mapped_column(Numeric, default=0)
    cpc: Mapped[float] = mapped_column(Numeric, default=0)
    cpm: Mapped[float] = mapped_column(Numeric, default=0)
    cpl: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    cpa: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    roas: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    conversions: Mapped[int] = mapped_column(default=0)
    frequency: Mapped[float] = mapped_column(Numeric, default=0)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
