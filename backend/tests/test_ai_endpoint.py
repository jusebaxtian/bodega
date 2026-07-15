import json
import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.ai import get_ai_explainer
from app.core.security import CurrentUser, get_current_user
from app.db.base import Base
from app.db.models import Ad, AdAccount, AdSet, Campaign, InsightSnapshot, Org, OrgMember
from app.db.session import get_db
from app.main import app
from app.services.ai.explainer import AIExplainer

VALID_RESPONSE = json.dumps(
    {
        "main_problem": "El anuncio muestra fatiga",
        "severity": "alta",
        "diagnosis": "La frecuencia subió y el CTR cayó.",
        "immediate_actions": ["Pausar el creativo actual"],
        "actions_72h": ["Medir nuevos creativos"],
        "confidence": 85,
        "explanation_simple": "La gente ya vio el anuncio muchas veces.",
    }
)


class FakeLLMClient:
    def __init__(self, response: str):
        self.response = response
        self.calls = 0

    def complete(self, system: str, user: str) -> str:
        self.calls += 1
        return self.response


@pytest.fixture
def client_with_seeded_ad():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    session = TestSession()
    user_id = uuid.uuid4()
    org = Org(id=uuid.uuid4(), name="Test Org")
    membership = OrgMember(org_id=org.id, user_id=user_id, role="owner")
    ad_account = AdAccount(id=uuid.uuid4(), org_id=org.id, meta_account_id="act_1", name="Cuenta", connected_by=user_id)
    campaign = Campaign(id=uuid.uuid4(), ad_account_id=ad_account.id, meta_campaign_id="c1", name="Campaña")
    ad_set = AdSet(id=uuid.uuid4(), campaign_id=campaign.id, meta_adset_id="as1", name="Conjunto")
    ad = Ad(id=uuid.uuid4(), ad_set_id=ad_set.id, meta_ad_id="ad1", name="Anuncio 1")
    session.add_all([org, membership, ad_account, campaign, ad_set, ad])

    start = date(2026, 7, 1)
    for i, ctr in enumerate([2.0, 1.4]):
        session.add(
            InsightSnapshot(
                ad_id=ad.id,
                snapshot_date=start + timedelta(days=i * 6),
                spend=100,
                ctr=ctr,
                frequency=2.0,
                cpl=10,
                conversions=5,
            )
        )
    session.commit()

    fake_llm = FakeLLMClient(VALID_RESPONSE)

    def _get_db_override():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=str(user_id), email="test@example.com")
    app.dependency_overrides[get_ai_explainer] = lambda: AIExplainer(llm_client=fake_llm, model_name="fake-model")

    yield TestClient(app), ad.id, fake_llm

    app.dependency_overrides.clear()
    session.close()


def test_explain_endpoint_returns_diagnosis(client_with_seeded_ad):
    client, ad_id, fake_llm = client_with_seeded_ad

    response = client.post("/api/v1/ai/explain", json={"entity_type": "ad", "entity_id": str(ad_id)})

    assert response.status_code == 200
    body = response.json()
    assert body["main_problem"] == "El anuncio muestra fatiga"
    assert body["model_used"] == "fake-model"
    assert fake_llm.calls == 1


def test_explain_endpoint_uses_cache_same_day(client_with_seeded_ad):
    client, ad_id, fake_llm = client_with_seeded_ad

    first = client.post("/api/v1/ai/explain", json={"entity_type": "ad", "entity_id": str(ad_id)})
    second = client.post("/api/v1/ai/explain", json={"entity_type": "ad", "entity_id": str(ad_id)})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert fake_llm.calls == 1  # la segunda llamada usó la caché, no volvió a llamar al LLM
