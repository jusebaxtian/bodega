import uuid
from dataclasses import dataclass
from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import Ad, AdAccount, AdSet, Campaign, InsightSnapshot, Org, Recommendation, Rule
from app.services.recommendation_service import evaluate_ad_account
from app.services.rules_engine.conditions import evaluate_condition
from app.services.rules_engine.evaluator import matching_rules
from app.services.rules_engine.seed_rules import SEED_RULES


@dataclass
class FakeSnapshot:
    snapshot_date: date
    frequency: float = 0
    ctr: float = 0
    cpl: float | None = None
    cpa: float | None = None
    roas: float | None = None
    spend: float = 0
    conversions: int = 0


def _series(values: list[float], metric: str) -> list[FakeSnapshot]:
    start = date(2026, 7, 1)
    snapshots = []
    for i, v in enumerate(values):
        kwargs = {"snapshot_date": start + timedelta(days=i), metric: v}
        snapshots.append(FakeSnapshot(**kwargs))
    return snapshots


# ---------- condiciones aisladas ----------


def test_gt_condition():
    snapshots = _series([1, 2, 5], "frequency")
    assert evaluate_condition(snapshots, {"metric": "frequency", "operator": "gt", "value": 3.5}) is True
    assert evaluate_condition(snapshots[:2], {"metric": "frequency", "operator": "gt", "value": 3.5}) is False


def test_decreased_by_pct_condition():
    # CTR: 2.0 hace 7 días -> 1.4 hoy = -30%
    values = [2.0] + [1.9, 1.8, 1.7, 1.6, 1.5, 1.4]
    snapshots = _series(values, "ctr")
    assert evaluate_condition(snapshots, {"metric": "ctr", "operator": "decreased_by_pct", "value": 25, "window_days": 6}) is True
    assert evaluate_condition(snapshots, {"metric": "ctr", "operator": "decreased_by_pct", "value": 40, "window_days": 6}) is False


def test_sustained_above_for_days_condition():
    snapshots = _series([10, 20, 20, 20], "cpl")
    assert evaluate_condition(snapshots, {"metric": "cpl", "operator": "sustained_above_for_days", "value": 15, "window_days": 3}) is True
    assert evaluate_condition(snapshots, {"metric": "cpl", "operator": "sustained_above_for_days", "value": 15, "window_days": 4}) is False


def test_condition_with_missing_metric_returns_false():
    snapshots = _series([1, 2, 3], "frequency")  # no tiene roas
    assert evaluate_condition(snapshots, {"metric": "roas", "operator": "gt", "value": 5}) is False


# ---------- evaluador con reglas semilla ----------


def test_fatigue_rule_triggers_and_others_dont():
    fatigue_rule = next(r for r in SEED_RULES if r["name"] == "Fatiga de anuncio")
    rule = Rule(id=uuid.uuid4(), org_id=None, is_active=True, **fatigue_rule)

    scale_rule_data = next(r for r in SEED_RULES if r["name"] == "Oportunidad de escalar")
    scale_rule = Rule(id=uuid.uuid4(), org_id=None, is_active=True, **scale_rule_data)

    start = date(2026, 7, 1)
    snapshots = []
    ctr_values = [2.0, 2.0, 1.9, 1.8, 1.6, 1.5, 1.4, 1.4]
    for i, ctr in enumerate(ctr_values):
        snapshots.append(FakeSnapshot(snapshot_date=start + timedelta(days=i), frequency=4.0, ctr=ctr, cpl=20))

    matched = matching_rules([rule, scale_rule], snapshots)
    matched_names = {r.name for r in matched}

    assert "Fatiga de anuncio" in matched_names
    assert "Oportunidad de escalar" not in matched_names


# ---------- integración: recommendation_service no duplica ----------


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _build_fatigued_ad(db_session) -> tuple[AdAccount, Ad]:
    org = Org(id=uuid.uuid4(), name="Test Org")
    ad_account = AdAccount(id=uuid.uuid4(), org_id=org.id, meta_account_id="act_1", name="Cuenta", connected_by=uuid.uuid4())
    campaign = Campaign(id=uuid.uuid4(), ad_account_id=ad_account.id, meta_campaign_id="c1", name="Campaña")
    ad_set = AdSet(id=uuid.uuid4(), campaign_id=campaign.id, meta_adset_id="as1", name="Conjunto")
    ad = Ad(id=uuid.uuid4(), ad_set_id=ad_set.id, meta_ad_id="ad1", name="Anuncio")

    db_session.add_all([org, ad_account, campaign, ad_set, ad])
    db_session.commit()

    start = date(2026, 7, 1)
    ctr_values = [2.0, 2.0, 1.9, 1.8, 1.6, 1.5, 1.4, 1.4]
    for i, ctr in enumerate(ctr_values):
        db_session.add(
            InsightSnapshot(
                ad_id=ad.id,
                snapshot_date=start + timedelta(days=i),
                frequency=4.0,
                ctr=ctr,
                spend=10,
                cpl=20,
            )
        )
    db_session.commit()

    return ad_account, ad


def test_evaluate_ad_account_creates_recommendation(db_session):
    ad_account, ad = _build_fatigued_ad(db_session)

    evaluate_ad_account(db_session, ad_account)

    recs = db_session.query(Recommendation).filter(Recommendation.entity_id == ad.id).all()
    assert len(recs) >= 1
    assert any(r.title == "Fatiga de anuncio" for r in recs)


def test_evaluate_ad_account_does_not_duplicate_pending_recommendation(db_session):
    ad_account, ad = _build_fatigued_ad(db_session)

    evaluate_ad_account(db_session, ad_account)
    evaluate_ad_account(db_session, ad_account)

    recs = (
        db_session.query(Recommendation)
        .filter(Recommendation.entity_id == ad.id, Recommendation.title == "Fatiga de anuncio")
        .all()
    )
    assert len(recs) == 1
