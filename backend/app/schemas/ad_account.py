import uuid
from datetime import datetime

from pydantic import BaseModel


class AdAccountOut(BaseModel):
    id: uuid.UUID
    meta_account_id: str
    name: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SyncJobOut(BaseModel):
    id: uuid.UUID
    ad_account_id: uuid.UUID
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None

    model_config = {"from_attributes": True}


class OAuthUrlOut(BaseModel):
    url: str


class MetaCallbackIn(BaseModel):
    code: str
    org_id: uuid.UUID
