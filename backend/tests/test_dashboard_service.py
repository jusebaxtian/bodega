import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import Ad, AdAccount, AdSet, Campaign, CampaignScore, InsightSnapshot, Org, Recommendation, Rule
from app.services.dashboard_service import build_campaign_detail, build_dashboard_summary


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _seed_two_campaigns(db_session):
    org = Org(id=uuid.uuid4(), name="Test Org")
    ad_account = AdAccount(id=uuid.uuid4(), org_id=org.id, meta_account_id="act_1", name="Cuenta", connected_by=uuid.uuid4())
    db_session.add_all([org, ad_account])

    good_campaign = Campaign(id=uuid.uuid4(), ad_account_id=ad_account.id, meta_campaign_id="c1", name="Campaña buena")
    bad_campaign = Campaign(id=uuid.uuid4(), ad_account_id=ad_account.id, meta_campaign_id="c2", name="Campaña crítica")
    db_session.add_all([good_campaign, bad_campaign])

    good_set = AdSet(id=uuid.uuid4(), campaign_id=good_campaign.id, meta_adset_id="as1", name="Conjunto bueno")
    bad_set = AdSet(id=uuid.uuid4(), campaign_id=bad_campaign.id, meta_adset_id="as2", name="Conjunto malo")
    db_session.add_all([good_set, bad_set])

    good_ad = Ad(id=uuid.uuid4(), ad_set_id=good_set.id, meta_ad_id="ad1", name="Anuncio bueno")
    bad_ad = Ad(id=uuid.uuid4(), ad_set_id=bad_set.id, meta_ad_id="ad2", name="Anuncio malo")
    db_session.add_all([good_ad, bad_ad])

    db_session.add(InsightSnapshot(ad_id=good_ad.id, snapshot_date=date(2026, 7, 15), spend=50, ctr=3.0, cpl=5, frequency=1.2, conversions=10))
    db_session.add(InsightSnapshot(ad_id=bad_ad.id, snapshot_date=date(2026, 7, 15), spend=200, ctr=0.5, cpl=40, frequency=5.0, conversions=1))

    db_session.add(CampaignScore(campaign_id=good_campaign.id, score=95, health_status="excelente", computed_at=datetime.now(timezone.utc)))
    db_session.add(CampaignScore(campaign_id=bad_campaign.id, score=30, health_status="critica", computed_at=datetime.now(timezone.utc)))

    rule = Rule(id=uuid.uuid4(), org_id=None, name="Fatiga de anuncio", conditions={"mode": "AND", "items": []}, action_type="new_creatives", priority="alta")
    db_session.add(rule)
    db_session.add(
        Recommendation(
            ad_account_id=ad_account.id,
            entity_type="ad",
            entity_id=bad_ad.id,
            rule_id=rule.id,
            priority="alta",
            title="Fatiga de anuncio",
            reason="CTR muy bajo",
            confidence=90,
            action_type="new_creatives",
            status="pending",
        )
    )
    db_session.commit()

    return ad_account, good_campaign, bad_campaign


def test_dashboard_summary_aggregates_kpis_and_ranking(db_session):
    ad_account, good_campaign, bad_campaign = _seed_two_campaigns(db_session)

    summary = build_dashboard_summary(db_session, ad_account)

    assert summary["kpis"]["total_spend"] == 250.0
    assert summary["kpis"]["total_conversions"] == 11
    assert summary["kpis"]["campaign_count"] == 2

    assert summary["best_campaigns"][0]["campaign_id"] == good_campaign.id
    assert summary["critical_campaigns"][0]["campaign_id"] == bad_campaign.id
    assert len(summary["top_alerts"]) == 1
    assert summary["top_alerts"][0]["title"] == "Fatiga de anuncio"


def test_campaign_detail_includes_ads_with_metrics(db_session):
    ad_account, good_campaign, bad_campaign = _seed_two_campaigns(db_session)

    detail = build_campaign_detail(db_session, bad_campaign)

    assert detail["health_status"] == "critica"
    assert len(detail["ad_sets"]) == 1
    assert detail["ad_sets"][0]["ads"][0]["latest_metrics"]["ctr"] == 0.5
