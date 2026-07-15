import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import CurrentUser
from app.db.models import OrgMember


def require_org_member(db: Session, org_id: uuid.UUID, current_user: CurrentUser) -> OrgMember:
    membership = db.execute(
        select(OrgMember).where(
            OrgMember.org_id == org_id,
            OrgMember.user_id == uuid.UUID(current_user.id),
        )
    ).scalar_one_or_none()

    if membership is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No perteneces a esta organización")

    return membership
