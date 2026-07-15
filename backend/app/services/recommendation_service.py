"""Orquesta la evaluación del motor de reglas sobre una cuenta publicitaria ya
sincronizada, y genera/actualiza recomendaciones + puntajes de campaña."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Ad, AdAccount, AdSet, Campaign, CampaignScore, InsightSnapshot, Recommendation, Rule
from app.services.rules_engine.evaluator import matching_rules
from app.services.rules_engine.seed_rules import ensure_seed_rules
from app.services.scoring import compute_campaign_score, health_status_for_score

CONFIDENCE_BY_PRIORITY = {"alta": 90, "media": 70, "baja": 50}


def _applicable_rules(db: Session, org_id) -> list[Rule]:
    stmt = select(Rule).where(Rule.is_active.is_(True)).where((Rule.org_id.is_(None)) | (Rule.org_id == org_id))
    return list(db.execute(stmt).scalars().all())


def _upsert_recommendation(db: Session, ad_account_id, ad: Ad, rule: Rule) -> None:
    existing = (
        db.query(Recommendation)
        .filter(
            Recommendation.entity_type == "ad",
            Recommendation.entity_id == ad.id,
            Recommendation.rule_id == rule.id,
            Recommendation.status == "pending",
        )
        .one_or_none()
    )
    if existing is not None:
        return  # ya existe una recomendación abierta igual, no duplicamos

    db.add(
        Recommendation(
            ad_account_id=ad_account_id,
            entity_type="ad",
            entity_id=ad.id,
            rule_id=rule.id,
            priority=rule.priority,
            title=rule.name,
            reason=rule.description or rule.name,
            confidence=CONFIDENCE_BY_PRIORITY.get(rule.priority, 50),
            action_type=rule.action_type,
        )
    )


def evaluate_ad_account(db: Session, ad_account: AdAccount) -> None:
    ensure_seed_rules(db)
    rules = _applicable_rules(db, ad_account.org_id)

    campaigns = db.query(Campaign).filter(Campaign.ad_account_id == ad_account.id).all()

    for campaign in campaigns:
        pending_priorities: list[str] = []

        ad_sets = db.query(AdSet).filter(AdSet.campaign_id == campaign.id).all()
        for ad_set in ad_sets:
            ads = db.query(Ad).filter(Ad.ad_set_id == ad_set.id).all()
            for ad in ads:
                snapshots = (
                    db.query(InsightSnapshot)
                    .filter(InsightSnapshot.ad_id == ad.id)
                    .order_by(InsightSnapshot.snapshot_date.asc())
                    .all()
                )
                if not snapshots:
                    continue

                for rule in matching_rules(rules, snapshots):
                    _upsert_recommendation(db, ad_account.id, ad, rule)
                    pending_priorities.append(rule.priority)

        score = compute_campaign_score(pending_priorities)
        db.add(
            CampaignScore(
                campaign_id=campaign.id,
                score=score,
                health_status=health_status_for_score(score),
                computed_at=datetime.now(timezone.utc),
            )
        )

    db.commit()
