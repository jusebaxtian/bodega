"""Agrega los datos ya calculados (snapshots, scores, recomendaciones) para
alimentar el dashboard. No hace ninguna llamada a Meta ni a la IA — solo lee
y agrega lo que los módulos anteriores ya dejaron en la base."""

import uuid

from sqlalchemy.orm import Session

from app.db.models import Ad, AdAccount, AdSet, Campaign, CampaignScore, InsightSnapshot, Recommendation


def _latest_snapshot_by_ad(db: Session, ad_ids: list[uuid.UUID]) -> dict[uuid.UUID, InsightSnapshot]:
    if not ad_ids:
        return {}

    snapshots = (
        db.query(InsightSnapshot)
        .filter(InsightSnapshot.ad_id.in_(ad_ids))
        .order_by(InsightSnapshot.ad_id, InsightSnapshot.snapshot_date.desc())
        .all()
    )
    latest: dict[uuid.UUID, InsightSnapshot] = {}
    for snapshot in snapshots:
        if snapshot.ad_id not in latest:
            latest[snapshot.ad_id] = snapshot
    return latest


def _latest_score_by_campaign(db: Session, campaign_ids: list[uuid.UUID]) -> dict[uuid.UUID, CampaignScore]:
    if not campaign_ids:
        return {}

    scores = (
        db.query(CampaignScore)
        .filter(CampaignScore.campaign_id.in_(campaign_ids))
        .order_by(CampaignScore.campaign_id, CampaignScore.computed_at.desc())
        .all()
    )
    latest: dict[uuid.UUID, CampaignScore] = {}
    for score in scores:
        if score.campaign_id not in latest:
            latest[score.campaign_id] = score
    return latest


def build_dashboard_summary(db: Session, ad_account: AdAccount) -> dict:
    campaigns = db.query(Campaign).filter(Campaign.ad_account_id == ad_account.id).all()
    campaign_ids = [c.id for c in campaigns]

    ad_sets = db.query(AdSet).filter(AdSet.campaign_id.in_(campaign_ids)).all() if campaign_ids else []
    ad_set_ids = [a.id for a in ad_sets]

    ads = db.query(Ad).filter(Ad.ad_set_id.in_(ad_set_ids)).all() if ad_set_ids else []
    ad_ids = [a.id for a in ads]

    latest_snapshots = _latest_snapshot_by_ad(db, ad_ids)
    latest_scores = _latest_score_by_campaign(db, campaign_ids)

    values = list(latest_snapshots.values())
    total_spend = sum(float(s.spend) for s in values)
    total_conversions = sum(s.conversions for s in values)
    cpls = [float(s.cpl) for s in values if s.cpl is not None]
    ctrs = [float(s.ctr) for s in values]
    frequencies = [float(s.frequency) for s in values]

    kpis = {
        "total_spend": round(total_spend, 2),
        "avg_cpl": round(sum(cpls) / len(cpls), 2) if cpls else None,
        "avg_ctr": round(sum(ctrs) / len(ctrs), 2) if ctrs else 0.0,
        "total_conversions": total_conversions,
        "avg_frequency": round(sum(frequencies) / len(frequencies), 2) if frequencies else 0.0,
        "campaign_count": len(campaigns),
    }

    ranked = sorted(
        (
            {"campaign_id": c.id, "name": c.name, "score": latest_scores[c.id].score, "health_status": latest_scores[c.id].health_status}
            for c in campaigns
            if c.id in latest_scores
        ),
        key=lambda item: item["score"],
        reverse=True,
    )
    best_campaigns = ranked[:3]
    critical_campaigns = sorted(
        [c for c in ranked if c["health_status"] in ("critica", "atencion")],
        key=lambda item: item["score"],
    )[:5]

    top_alerts = [
        {
            "id": rec.id,
            "title": rec.title,
            "priority": rec.priority,
            "entity_type": rec.entity_type,
            "entity_id": rec.entity_id,
            "action_type": rec.action_type,
        }
        for rec in (
            db.query(Recommendation)
            .filter(Recommendation.ad_account_id == ad_account.id, Recommendation.status == "pending")
            .order_by(Recommendation.priority.desc(), Recommendation.created_at.desc())
            .limit(5)
            .all()
        )
    ]

    return {
        "kpis": kpis,
        "best_campaigns": best_campaigns,
        "critical_campaigns": critical_campaigns,
        "top_alerts": top_alerts,
    }


def build_campaign_detail(db: Session, campaign: Campaign) -> dict:
    ad_sets = db.query(AdSet).filter(AdSet.campaign_id == campaign.id).all()
    ad_set_ids = [a.id for a in ad_sets]
    ads = db.query(Ad).filter(Ad.ad_set_id.in_(ad_set_ids)).all() if ad_set_ids else []
    ad_ids = [a.id for a in ads]

    latest_snapshots = _latest_snapshot_by_ad(db, ad_ids)
    score = _latest_score_by_campaign(db, [campaign.id]).get(campaign.id)

    ads_by_set: dict[uuid.UUID, list[Ad]] = {}
    for ad in ads:
        ads_by_set.setdefault(ad.ad_set_id, []).append(ad)

    ad_set_payloads = []
    for ad_set in ad_sets:
        ad_payloads = []
        for ad in ads_by_set.get(ad_set.id, []):
            snapshot = latest_snapshots.get(ad.id)
            metrics = None
            if snapshot is not None:
                metrics = {
                    "spend": float(snapshot.spend),
                    "ctr": float(snapshot.ctr),
                    "cpl": float(snapshot.cpl) if snapshot.cpl is not None else None,
                    "frequency": float(snapshot.frequency),
                    "conversions": snapshot.conversions,
                }
            ad_payloads.append(
                {
                    "id": ad.id,
                    "name": ad.name,
                    "status": ad.status,
                    "creative_type": ad.creative_type,
                    "latest_metrics": metrics,
                }
            )
        ad_set_payloads.append({"id": ad_set.id, "name": ad_set.name, "status": ad_set.status, "ads": ad_payloads})

    snapshot_dates = sorted(
        {
            s.snapshot_date
            for s in db.query(InsightSnapshot).filter(InsightSnapshot.ad_id.in_(ad_ids)).all()
        }
    ) if ad_ids else []

    return {
        "id": campaign.id,
        "name": campaign.name,
        "objective": campaign.objective,
        "status": campaign.status,
        "score": score.score if score else None,
        "health_status": score.health_status if score else None,
        "ad_sets": ad_set_payloads,
        "snapshot_dates": snapshot_dates,
    }
