import uuid
from datetime import datetime

from pydantic import BaseModel


class RecommendationOut(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    priority: str
    title: str
    reason: str
    confidence: int
    action_type: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignScoreOut(BaseModel):
    campaign_id: uuid.UUID
    score: int
    health_status: str
    computed_at: datetime

    model_config = {"from_attributes": True}


class RuleCreate(BaseModel):
    name: str
    description: str | None = None
    conditions: dict
    action_type: str
    priority: str = "media"


class RuleOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID | None
    name: str
    description: str | None
    is_active: bool
    conditions: dict
    action_type: str
    priority: str
    created_at: datetime

    model_config = {"from_attributes": True}
