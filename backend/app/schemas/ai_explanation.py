import uuid
from datetime import datetime

from pydantic import BaseModel


class AIExplainRequest(BaseModel):
    entity_type: str  # por ahora solo 'ad' está soportado
    entity_id: uuid.UUID


class AIExplanationOut(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    main_problem: str
    severity: str
    diagnosis: str
    immediate_actions: list[str]
    actions_72h: list[str]
    confidence: int
    explanation_simple: str
    model_used: str
    created_at: datetime

    model_config = {"from_attributes": True, "protected_namespaces": ()}
