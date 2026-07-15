import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Rule(Base):
    """Una regla de negocio configurable. org_id = None significa que es una
    regla global del sistema (seed), visible/aplicable a todas las orgs."""

    __tablename__ = "rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"), nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    conditions: Mapped[dict] = mapped_column(JSON, nullable=False)
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[str] = mapped_column(String, nullable=False, default="media")  # alta|media|baja
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
