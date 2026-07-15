import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import CurrentUser, get_current_user
from app.db.models import Ad, AdAccount, AdSet, AIExplanation, Campaign, OrgMember
from app.db.session import get_db
from app.schemas.ai_explanation import AIExplainRequest, AIExplanationOut
from app.services.ai.explainer import AIExplainer, AnthropicLLMClient
from app.services.ai.summary_builder import build_ad_summary

router = APIRouter(tags=["ai"])


def get_ai_explainer() -> AIExplainer:
    return AIExplainer(llm_client=AnthropicLLMClient(), model_name="claude-sonnet-4-5")


def _require_ad_access(db: Session, ad_id: uuid.UUID, current_user: CurrentUser) -> Ad:
    ad = db.get(Ad, ad_id)
    if ad is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Anuncio no encontrado")

    ad_set = db.get(AdSet, ad.ad_set_id)
    campaign = db.get(Campaign, ad_set.campaign_id)

    is_member = (
        db.query(OrgMember)
        .join(AdAccount, AdAccount.org_id == OrgMember.org_id)
        .filter(
            AdAccount.id == campaign.ad_account_id,
            OrgMember.user_id == uuid.UUID(current_user.id),
        )
        .first()
    )
    if is_member is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No tienes acceso a este anuncio")

    return ad


@router.post("/ai/explain", response_model=AIExplanationOut)
def explain_entity(
    payload: AIExplainRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_explainer: AIExplainer = Depends(get_ai_explainer),
) -> AIExplanation:
    if payload.entity_type != "ad":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Por ahora solo se soporta entity_type='ad'")

    _require_ad_access(db, payload.entity_id, current_user)

    today = datetime.now(timezone.utc).date()
    existing = (
        db.query(AIExplanation)
        .filter(AIExplanation.entity_type == "ad", AIExplanation.entity_id == payload.entity_id)
        .order_by(AIExplanation.created_at.desc())
        .first()
    )
    if existing is not None and existing.created_at.date() == today:
        return existing

    summary = build_ad_summary(db, payload.entity_id)
    result, model_name = ai_explainer.explain(summary)

    explanation = AIExplanation(
        entity_type="ad",
        entity_id=payload.entity_id,
        main_problem=result.main_problem,
        severity=result.severity,
        diagnosis=result.diagnosis,
        immediate_actions=result.immediate_actions,
        actions_72h=result.actions_72h,
        confidence=result.confidence,
        explanation_simple=result.explanation_simple,
        model_used=model_name,
    )
    db.add(explanation)
    db.commit()
    db.refresh(explanation)
    return explanation


@router.get("/ai/explanations/{entity_type}/{entity_id}", response_model=AIExplanationOut | None)
def get_latest_explanation(
    entity_type: str,
    entity_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIExplanation | None:
    if entity_type == "ad":
        _require_ad_access(db, entity_id, current_user)

    return (
        db.query(AIExplanation)
        .filter(AIExplanation.entity_type == entity_type, AIExplanation.entity_id == entity_id)
        .order_by(AIExplanation.created_at.desc())
        .first()
    )
