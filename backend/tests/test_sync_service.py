import uuid
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import Ad, AdAccount, AdSet, Campaign, InsightSnapshot, Org
from app.services.sync_service import sync_ad_account


class FakeMetaClient:
    """Sustituye a MetaClient en los tests: nunca llama a Meta real."""

    def get_campaigns(self, ad_account_id: str) -> list[dict]:
        return [{"id": "c1", "name": "Campaña Leads", "objective": "LEAD_GENERATION", "status": "ACTIVE", "daily_budget": "5000"}]

    def get_ad_sets(self, campaign_id: str) -> list[dict]:
        return [{"id": "as1", "name": "Conjunto 1", "status": "ACTIVE", "targeting": {"age_min": 18}}]

    def get_ads(self, ad_set_id: str) -> list[dict]:
        return [{"id": "ad1", "name": "Anuncio 1", "status": "ACTIVE", "creative": {"object_type": "VIDEO"}}]

    def get_insights(self, ad_id: str, since: date, until: date) -> list[dict]:
        return [
            {
                "date_start": "2026-07-14",
                "spend": "100.0",
                "impressions": "1000",
                "clicks": "50",
                "ctr": "5.0",
                "cpc": "2.0",
                "cpm": "100.0",
                "frequency": "1.2",
                "actions": [{"action_type": "lead", "value": "10"}],
            }
        ]


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_sync_ad_account_creates_full_hierarchy(db_session):
    org = Org(id=uuid.uuid4(), name="Test Org")
    ad_account = AdAccount(
        id=uuid.uuid4(),
        org_id=org.id,
        meta_account_id="act_123",
        name="Cuenta test",
        connected_by=uuid.uuid4(),
    )
    db_session.add(org)
    db_session.add(ad_account)
    db_session.commit()

    job = sync_ad_account(db_session, ad_account, FakeMetaClient())

    assert job.status == "success"
    assert db_session.query(Campaign).count() == 1
    assert db_session.query(AdSet).count() == 1
    assert db_session.query(Ad).count() == 1

    snapshot = db_session.query(InsightSnapshot).one()
    assert snapshot.conversions == 10
    assert float(snapshot.spend) == 100.0
    assert float(snapshot.cpl) == 10.0


def test_sync_ad_account_upserts_without_duplicating(db_session):
    org = Org(id=uuid.uuid4(), name="Test Org")
    ad_account = AdAccount(
        id=uuid.uuid4(),
        org_id=org.id,
        meta_account_id="act_123",
        name="Cuenta test",
        connected_by=uuid.uuid4(),
    )
    db_session.add(org)
    db_session.add(ad_account)
    db_session.commit()

    sync_ad_account(db_session, ad_account, FakeMetaClient())
    sync_ad_account(db_session, ad_account, FakeMetaClient())

    assert db_session.query(Campaign).count() == 1
    assert db_session.query(AdSet).count() == 1
    assert db_session.query(Ad).count() == 1
    assert db_session.query(InsightSnapshot).count() == 1
