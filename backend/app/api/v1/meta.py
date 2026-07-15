import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import require_org_member
from app.core.security import CurrentUser, get_current_user
from app.db.models import AdAccount
from app.db.session import get_db
from app.schemas.ad_account import MetaCallbackIn, OAuthUrlOut
from app.services.meta_client import MetaClient, build_oauth_url, exchange_code_for_token
from app.services.token_crypto import encrypt_token

router = APIRouter(tags=["meta"])


@router.get("/meta/oauth-url", response_model=OAuthUrlOut)
def get_oauth_url() -> OAuthUrlOut:
    return OAuthUrlOut(url=build_oauth_url())


@router.post("/meta/callback", response_model=list[str])
def meta_callback(
    payload: MetaCallbackIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[str]:
    """Intercambia el `code` de Facebook Login por un access_token, lista las
    cuentas publicitarias del usuario y las guarda ligadas a su organización.
    Solo lectura: nunca se pide ni se usa un permiso de escritura sobre Meta Ads.
    """
    require_org_member(db, payload.org_id, current_user)

    token_data = exchange_code_for_token(payload.code)
    access_token = token_data["access_token"]
    encrypted_token = encrypt_token(access_token)

    meta_client = MetaClient(access_token=access_token)
    try:
        accounts = meta_client.get_ad_accounts()
    finally:
        meta_client.close()

    created_ids = []
    for account in accounts:
        existing = (
            db.query(AdAccount)
            .filter(
                AdAccount.org_id == payload.org_id,
                AdAccount.meta_account_id == account["id"],
            )
            .one_or_none()
        )
        if existing:
            existing.access_token_encrypted = encrypted_token
            existing.name = account.get("name", existing.name)
        else:
            db.add(
                AdAccount(
                    org_id=payload.org_id,
                    meta_account_id=account["id"],
                    name=account.get("name", account["id"]),
                    connected_by=uuid.UUID(current_user.id),
                    access_token_encrypted=encrypted_token,
                )
            )
        created_ids.append(account["id"])

    db.commit()
    return created_ids
