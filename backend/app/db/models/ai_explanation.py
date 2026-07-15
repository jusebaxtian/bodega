import uuid
from datetime import datetime

from sqlalchemy import JSON, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AIExplanation(Base):
    """Diagnóstico redactado por la IA para una entidad (ad/ad_set/campaign),
    a partir de un resumen ya calculado por el motor de reglas. La IA nunca
    recibe ni recalcula las tablas crudas de insights."""

    __tablename__ = "ai_explanations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)  # 'campaign'|'ad_set'|'ad'
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    main_problem: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)  # baja|media|alta|critica
    diagnosis: Mapped[str] = mapped_column(String, nullable=False)
    immediate_actions: Mapped[list] = mapped_column(JSON, nullable=False)
    actions_72h: Mapped[list] = mapped_column(JSON, nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-100
    explanation_simple: Mapped[str] = mapped_column(String, nullable=False)

    model_used: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
