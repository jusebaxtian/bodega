"""Arma el resumen compacto que se le entrega a la IA. Nunca se le pasan las
tablas crudas: solo un resumen ya calculado (últimos valores, tendencia vs
hace 7 días, reglas que dispararon, puntaje de la campaña)."""

import uuid

from sqlalchemy.orm import Session

from app.db.models import Ad, AdSet, Campaign, CampaignScore, InsightSnapshot, Recommendation


def _pct_change(current: float, baseline: float) -> float | None:
    if baseline == 0:
        return None
    return round((current - baseline) / baseline * 100, 1)


def build_ad_summary(db: Session, ad_id: uuid.UUID) -> dict:
    ad = db.get(Ad, ad_id)
    if ad is None:
        raise ValueError(f"Ad {ad_id} no encontrado")

    ad_set = db.get(AdSet, ad.ad_set_id)
    campaign = db.get(Campaign, ad_set.campaign_id)

    snapshots = (
        db.query(InsightSnapshot)
        .filter(InsightSnapshot.ad_id == ad_id)
        .order_by(InsightSnapshot.snapshot_date.asc())
        .all()
    )
    if not snapshots:
        raise ValueError(f"Ad {ad_id} no tiene datos de rendimiento todavía")

    latest = snapshots[-1]
    baseline = snapshots[0] if len(snapshots) > 1 else None

    trend = {}
    if baseline is not None:
        trend = {
            "ctr_change_pct": _pct_change(float(latest.ctr), float(baseline.ctr)),
            "frequency_change_pct": _pct_change(float(latest.frequency), float(baseline.frequency)),
            "cpl_change_pct": (
                _pct_change(float(latest.cpl), float(baseline.cpl))
                if latest.cpl is not None and baseline.cpl is not None
                else None
            ),
        }

    triggered_rules = [
        rec.title
        for rec in db.query(Recommendation)
        .filter(Recommendation.entity_type == "ad", Recommendation.entity_id == ad_id, Recommendation.status == "pending")
        .all()
    ]

    score = (
        db.query(CampaignScore)
        .filter(CampaignScore.campaign_id == campaign.id)
        .order_by(CampaignScore.computed_at.desc())
        .first()
    )

    days_active = (latest.snapshot_date - snapshots[0].snapshot_date).days + 1

    return {
        "ad_name": ad.name,
        "campaign_objective": campaign.objective,
        "days_active": days_active,
        "current_metrics": {
            "spend": float(latest.spend),
            "ctr": float(latest.ctr),
            "cpl": float(latest.cpl) if latest.cpl is not None else None,
            "frequency": float(latest.frequency),
            "conversions": latest.conversions,
        },
        "trend_vs_7_days_ago": trend,
        "rules_triggered": triggered_rules,
        "campaign_score": score.score if score else None,
        "campaign_health": score.health_status if score else None,
    }
