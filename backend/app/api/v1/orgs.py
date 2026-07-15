import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import CurrentUser, get_current_user
from app.db.models import Org, OrgMember
from app.db.session import get_db
from app.schemas.org import OrgCreate, OrgOut

router = APIRouter(tags=["orgs"])


@router.post("/orgs", response_model=OrgOut, status_code=201)
def create_org(
    payload: OrgCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrgOut:
    org = Org(name=payload.name)
    db.add(org)
    db.flush()

    membership = OrgMember(org_id=org.id, user_id=uuid.UUID(current_user.id), role="owner")
    db.add(membership)
    db.commit()
    db.refresh(org)

    return OrgOut(id=org.id, name=org.name, role="owner", created_at=org.created_at)
