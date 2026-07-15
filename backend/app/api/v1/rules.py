import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import require_org_member
from app.core.security import CurrentUser, get_current_user
from app.db.models import Rule
from app.db.session import get_db
from app.schemas.recommendation import RuleCreate, RuleOut

router = APIRouter(tags=["rules"])


@router.get("/orgs/{org_id}/rules", response_model=list[RuleOut])
def list_rules(
    org_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Rule]:
    require_org_member(db, org_id, current_user)
    stmt = select(Rule).where((Rule.org_id.is_(None)) | (Rule.org_id == org_id))
    return list(db.execute(stmt).scalars().all())


@router.post("/orgs/{org_id}/rules", response_model=RuleOut, status_code=201)
def create_rule(
    org_id: uuid.UUID,
    payload: RuleCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Rule:
    membership = require_org_member(db, org_id, current_user)
    if membership.role != "owner":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el owner de la organización puede crear reglas")

    rule = Rule(org_id=org_id, **payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
