import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.ad_accounts import _user_ad_account_or_404
from app.core.security import CurrentUser, get_current_user
from app.db.models import Campaign, CampaignScore, OrgMember, Recommendation
from app.db.session import get_db
from app.schemas.recommendation import CampaignScoreOut, RecommendationOut

router = APIRouter(tags=["recommendations"])


@router.get("/ad-accounts/{ad_account_id}/recommendations", response_model=list[RecommendationOut])
def list_recommendations(
    ad_account_id: uuid.UUID,
    status_filter: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Recommendation]:
    _user_ad_account_or_404(db, ad_account_id, current_user)

    stmt = select(Recommendation).where(Recommendation.ad_account_id == ad_account_id)
    if status_filter:
        stmt = stmt.where(Recommendation.status == status_filter)
    stmt = stmt.order_by(Recommendation.created_at.desc())

    return list(db.execute(stmt).scalars().all())


def _recommendation_or_404(db: Session, recommendation_id: uuid.UUID, current_user: CurrentUser) -> Recommendation:
    recommendation = db.get(Recommendation, recommendation_id)
    if recommendation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recomendación no encontrada")
    _user_ad_account_or_404(db, recommendation.ad_account_id, current_user)
    return recommendation


@router.post("/recommendations/{recommendation_id}/apply", response_model=RecommendationOut)
def apply_recommendation(
    recommendation_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Recommendation:
    """Marca que el usuario ya ejecutó la acción él mismo en Meta Ads Manager.
    AdsControl IA nunca ejecuta esto en Meta; solo registra el resultado para el historial."""
    recommendation = _recommendation_or_404(db, recommendation_id, current_user)
    recommendation.status = "applied_by_user"
    recommendation.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(recommendation)
    return recommendation


@router.post("/recommendations/{recommendation_id}/dismiss", response_model=RecommendationOut)
def dismiss_recommendation(
    recommendation_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Recommendation:
    recommendation = _recommendation_or_404(db, recommendation_id, current_user)
    recommendation.status = "dismissed"
    recommendation.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(recommendation)
    return recommendation


@router.get("/ad-accounts/{ad_account_id}/scores", response_model=list[CampaignScoreOut])
def get_scores(
    ad_account_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CampaignScore]:
    _user_ad_account_or_404(db, ad_account_id, current_user)

    # último score por campaña
    campaign_ids = [c.id for c in db.query(Campaign).filter(Campaign.ad_account_id == ad_account_id).all()]
    scores = []
    for campaign_id in campaign_ids:
        latest = (
            db.query(CampaignScore)
            .filter(CampaignScore.campaign_id == campaign_id)
            .order_by(CampaignScore.computed_at.desc())
            .first()
        )
        if latest:
            scores.append(latest)
    return scores
