import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import CurrentUser, get_current_user
from app.db.models import Org, OrgMember
from app.db.session import get_db
from app.schemas.org import MeOut, OrgOut

router = APIRouter(tags=["me"])


@router.get("/me", response_model=MeOut)
def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeOut:
    stmt = (
        select(Org, OrgMember.role)
        .join(OrgMember, OrgMember.org_id == Org.id)
        .where(OrgMember.user_id == uuid.UUID(current_user.id))
    )
    rows = db.execute(stmt).all()

    orgs = [OrgOut(id=org.id, name=org.name, role=role, created_at=org.created_at) for org, role in rows]

    return MeOut(id=current_user.id, email=current_user.email, orgs=orgs)
