import uuid
from datetime import datetime

from pydantic import BaseModel


class OrgCreate(BaseModel):
    name: str


class OrgOut(BaseModel):
    id: uuid.UUID
    name: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MeOut(BaseModel):
    id: str
    email: str | None
    orgs: list[OrgOut]
