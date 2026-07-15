import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad_account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ad_accounts.id", ondelete="CASCADE"))
    meta_campaign_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    objective: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active")
    daily_budget: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    ad_sets: Mapped[list["AdSet"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")


class AdSet(Base):
    __tablename__ = "ad_sets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    meta_adset_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="active")
    targeting_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    campaign: Mapped["Campaign"] = relationship(back_populates="ad_sets")
    ads: Mapped[list["Ad"]] = relationship(back_populates="ad_set", cascade="all, delete-orphan")


class Ad(Base):
    __tablename__ = "ads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad_set_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ad_sets.id", ondelete="CASCADE"))
    meta_ad_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="active")
    creative_type: Mapped[str | None] = mapped_column(String, nullable=True)
    creative_preview_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    ad_set: Mapped["AdSet"] = relationship(back_populates="ads")
