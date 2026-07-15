import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.ad_accounts import _user_ad_account_or_404
from app.core.security import CurrentUser, get_current_user
from app.db.models import Campaign, OrgMember
from app.db.session import get_db
from app.schemas.dashboard import CampaignDetailOut, DashboardSummaryOut
from app.services.dashboard_service import build_campaign_detail, build_dashboard_summary

router = APIRouter(tags=["dashboard"])


@router.get("/ad-accounts/{ad_account_id}/dashboard-summary", response_model=DashboardSummaryOut)
def get_dashboard_summary(
    ad_account_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    ad_account = _user_ad_account_or_404(db, ad_account_id, current_user)
    return build_dashboard_summary(db, ad_account)


@router.get("/campaigns/{campaign_id}", response_model=CampaignDetailOut)
def get_campaign_detail(
    campaign_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaña no encontrada")

    _user_ad_account_or_404(db, campaign.ad_account_id, current_user)
    return build_campaign_detail(db, campaign)
