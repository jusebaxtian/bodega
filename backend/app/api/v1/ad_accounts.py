import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import CurrentUser, get_current_user
from app.db.models import AdAccount, OrgMember, SyncJob
from app.db.session import SessionLocal, get_db
from app.schemas.ad_account import AdAccountOut, SyncJobOut
from app.services.meta_client import MetaClient
from app.services.sync_service import sync_ad_account
from app.services.token_crypto import decrypt_token

router = APIRouter(tags=["ad-accounts"])


def _user_ad_account_or_404(db: Session, ad_account_id: uuid.UUID, current_user: CurrentUser) -> AdAccount:
    stmt = (
        select(AdAccount)
        .join(OrgMember, OrgMember.org_id == AdAccount.org_id)
        .where(AdAccount.id == ad_account_id, OrgMember.user_id == uuid.UUID(current_user.id))
    )
    ad_account = db.execute(stmt).scalars().one_or_none()
    if ad_account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cuenta publicitaria no encontrada")
    return ad_account


@router.get("/ad-accounts", response_model=list[AdAccountOut])
def list_ad_accounts(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AdAccount]:
    stmt = (
        select(AdAccount)
        .join(OrgMember, OrgMember.org_id == AdAccount.org_id)
        .where(OrgMember.user_id == uuid.UUID(current_user.id))
    )
    return list(db.execute(stmt).scalars().all())


def _run_sync_job(ad_account_id: uuid.UUID) -> None:
    db = SessionLocal()
    try:
        ad_account = db.get(AdAccount, ad_account_id)
        if ad_account is None or not ad_account.access_token_encrypted:
            return
        access_token = decrypt_token(ad_account.access_token_encrypted)
        meta_client = MetaClient(access_token=access_token)
        try:
            sync_ad_account(db, ad_account, meta_client)
        finally:
            meta_client.close()
    finally:
        db.close()


@router.post("/ad-accounts/{ad_account_id}/sync", status_code=202)
def trigger_sync(
    ad_account_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    _user_ad_account_or_404(db, ad_account_id, current_user)
    background_tasks.add_task(_run_sync_job, ad_account_id)
    return {"status": "sync_started"}


@router.get("/ad-accounts/{ad_account_id}/sync-status", response_model=SyncJobOut | None)
def get_sync_status(
    ad_account_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SyncJob | None:
    _user_ad_account_or_404(db, ad_account_id, current_user)
    stmt = (
        select(SyncJob)
        .where(SyncJob.ad_account_id == ad_account_id)
        .order_by(SyncJob.created_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().one_or_none()
