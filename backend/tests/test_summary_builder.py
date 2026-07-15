import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import Ad, AdAccount, AdSet, Campaign, InsightSnapshot, Org, Recommendation, Rule
from app.services.ai.summary_builder import build_ad_summary


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_build_ad_summary_has_expected_shape(db_session):
    org = Org(id=uuid.uuid4(), name="Test Org")
    ad_account = AdAccount(id=uuid.uuid4(), org_id=org.id, meta_account_id="act_1", name="Cuenta", connected_by=uuid.uuid4())
    campaign = Campaign(id=uuid.uuid4(), ad_account_id=ad_account.id, meta_campaign_id="c1", name="Campaña", objective="LEAD_GENERATION")
    ad_set = AdSet(id=uuid.uuid4(), campaign_id=campaign.id, meta_adset_id="as1", name="Conjunto")
    ad = Ad(id=uuid.uuid4(), ad_set_id=ad_set.id, meta_ad_id="ad1", name="Anuncio 1")
    db_session.add_all([org, ad_account, campaign, ad_set, ad])
    db_session.commit()

    rule = Rule(
        id=uuid.uuid4(),
        org_id=None,
        name="Fatiga de anuncio",
        conditions={"mode": "AND", "items": []},
        action_type="new_creatives",
        priority="alta",
    )
    db_session.add(rule)
    db_session.add(
        Recommendation(
            ad_account_id=ad_account.id,
            entity_type="ad",
            entity_id=ad.id,
            rule_id=rule.id,
            priority="alta",
            title="Fatiga de anuncio",
            reason="CTR bajó",
            confidence=90,
            action_type="new_creatives",
            status="pending",
        )
    )

    start = date(2026, 7, 1)
    values = [(2.0, 1.0, 10.0), (1.4, 4.0, 20.0)]  # (ctr, frequency, cpl)
    for i, (ctr, frequency, cpl) in enumerate(values):
        db_session.add(
            InsightSnapshot(
                ad_id=ad.id,
                snapshot_date=start + timedelta(days=i * 6),
                spend=100,
                ctr=ctr,
                frequency=frequency,
                cpl=cpl,
                conversions=5,
            )
        )
    db_session.commit()

    summary = build_ad_summary(db_session, ad.id)

    assert summary["ad_name"] == "Anuncio 1"
    assert summary["campaign_objective"] == "LEAD_GENERATION"
    assert summary["current_metrics"]["ctr"] == 1.4
    assert summary["trend_vs_7_days_ago"]["ctr_change_pct"] == -30.0
    assert summary["rules_triggered"] == ["Fatiga de anuncio"]
    assert summary["days_active"] == 7


def test_build_ad_summary_raises_without_data(db_session):
    org = Org(id=uuid.uuid4(), name="Test Org")
    ad_account = AdAccount(id=uuid.uuid4(), org_id=org.id, meta_account_id="act_1", name="Cuenta", connected_by=uuid.uuid4())
    campaign = Campaign(id=uuid.uuid4(), ad_account_id=ad_account.id, meta_campaign_id="c1", name="Campaña")
    ad_set = AdSet(id=uuid.uuid4(), campaign_id=campaign.id, meta_adset_id="as1", name="Conjunto")
    ad = Ad(id=uuid.uuid4(), ad_set_id=ad_set.id, meta_ad_id="ad1", name="Anuncio sin datos")
    db_session.add_all([org, ad_account, campaign, ad_set, ad])
    db_session.commit()

    with pytest.raises(ValueError):
        build_ad_summary(db_session, ad.id)
