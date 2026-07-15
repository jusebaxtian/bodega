import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AdAccount(Base):
    """Una cuenta publicitaria de Meta conectada a una organización.

    access_token vive cifrado a nivel de aplicación (no en texto plano);
    el cifrado/descifrado se implementa en el Módulo 2 junto con el OAuth de Meta.
    """

    __tablename__ = "ad_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"))
    meta_account_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="active")
    connected_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    access_token_encrypted: Mapped[str | None] = mapped_column(String, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
