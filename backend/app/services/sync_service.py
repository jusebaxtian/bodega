"""Orquesta el pipeline de sincronización: campañas → conjuntos → anuncios → insights.

Es puramente de lectura: trae datos de Meta y los guarda/actualiza en nuestra base.
Nunca llama a un endpoint de escritura de la Graph API.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models import Ad, AdAccount, AdSet, Campaign, InsightSnapshot, SyncJob
from app.services.meta_client import MetaClient
from app.services.recommendation_service import evaluate_ad_account


def _extract_conversions(actions: list[dict] | None) -> int:
    if not actions:
        return 0
    lead_types = {"lead", "offsite_conversion.fb_pixel_lead", "purchase"}
    return sum(int(float(a["value"])) for a in actions if a.get("action_type") in lead_types)


def _upsert_campaign(db: Session, ad_account_id, data: dict) -> Campaign:
    campaign = (
        db.query(Campaign)
        .filter(Campaign.ad_account_id == ad_account_id, Campaign.meta_campaign_id == data["id"])
        .one_or_none()
    )
    if campaign is None:
        campaign = Campaign(ad_account_id=ad_account_id, meta_campaign_id=data["id"])
        db.add(campaign)

    campaign.name = data.get("name", "")
    campaign.objective = data.get("objective")
    campaign.status = data.get("status", "active").lower()
    campaign.daily_budget = Decimal(data["daily_budget"]) / 100 if data.get("daily_budget") else None
    db.flush()
    return campaign


def _upsert_ad_set(db: Session, campaign_id, data: dict) -> AdSet:
    ad_set = (
        db.query(AdSet)
        .filter(AdSet.campaign_id == campaign_id, AdSet.meta_adset_id == data["id"])
        .one_or_none()
    )
    if ad_set is None:
        ad_set = AdSet(campaign_id=campaign_id, meta_adset_id=data["id"])
        db.add(ad_set)

    ad_set.name = data.get("name", "")
    ad_set.status = data.get("status", "active").lower()
    ad_set.targeting_summary = data.get("targeting")
    db.flush()
    return ad_set


def _upsert_ad(db: Session, ad_set_id, data: dict) -> Ad:
    ad = db.query(Ad).filter(Ad.ad_set_id == ad_set_id, Ad.meta_ad_id == data["id"]).one_or_none()
    if ad is None:
        ad = Ad(ad_set_id=ad_set_id, meta_ad_id=data["id"])
        db.add(ad)

    creative = data.get("creative") or {}
    ad.name = data.get("name", "")
    ad.status = data.get("status", "active").lower()
    ad.creative_type = creative.get("object_type")
    ad.creative_preview_url = creative.get("thumbnail_url")
    db.flush()
    return ad


def _upsert_insight(db: Session, ad_id, insight: dict) -> None:
    snapshot_date = date.fromisoformat(insight["date_start"])
    snapshot = (
        db.query(InsightSnapshot)
        .filter(InsightSnapshot.ad_id == ad_id, InsightSnapshot.snapshot_date == snapshot_date)
        .one_or_none()
    )
    if snapshot is None:
        snapshot = InsightSnapshot(ad_id=ad_id, snapshot_date=snapshot_date)
        db.add(snapshot)

    conversions = _extract_conversions(insight.get("actions"))
    spend = Decimal(str(insight.get("spend", "0")))

    snapshot.spend = spend
    snapshot.impressions = int(insight.get("impressions", 0))
    snapshot.clicks = int(insight.get("clicks", 0))
    snapshot.ctr = Decimal(str(insight.get("ctr", "0")))
    snapshot.cpc = Decimal(str(insight.get("cpc", "0")))
    snapshot.cpm = Decimal(str(insight.get("cpm", "0")))
    snapshot.frequency = Decimal(str(insight.get("frequency", "0")))
    snapshot.conversions = conversions
    snapshot.cpl = (spend / conversions) if conversions else None
    db.flush()


def sync_ad_account(
    db: Session,
    ad_account: AdAccount,
    meta_client: MetaClient,
    lookback_days: int = 7,
) -> SyncJob:
    job = SyncJob(ad_account_id=ad_account.id, status="running", started_at=datetime.now(timezone.utc))
    db.add(job)
    db.commit()

    try:
        since = date.today() - timedelta(days=lookback_days)
        until = date.today()

        for campaign_data in meta_client.get_campaigns(ad_account.meta_account_id):
            campaign = _upsert_campaign(db, ad_account.id, campaign_data)

            for ad_set_data in meta_client.get_ad_sets(campaign_data["id"]):
                ad_set = _upsert_ad_set(db, campaign.id, ad_set_data)

                for ad_data in meta_client.get_ads(ad_set_data["id"]):
                    ad = _upsert_ad(db, ad_set.id, ad_data)

                    for insight in meta_client.get_insights(ad_data["id"], since, until):
                        _upsert_insight(db, ad.id, insight)

        evaluate_ad_account(db, ad_account)

        job.status = "success"
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:  # noqa: BLE001 - queremos capturar cualquier falla de la sync
        db.rollback()
        job.status = "failed"
        job.error_message = str(exc)
        job.finished_at = datetime.now(timezone.utc)
        db.add(job)
        db.commit()
        raise
    finally:
        db.refresh(job)

    return job
