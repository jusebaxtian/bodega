"""Cliente de solo lectura para la Graph API de Meta.

IMPORTANTE: AdsControl IA es un producto de solo lectura. Este cliente
únicamente expone llamadas GET (cuentas, campañas, conjuntos, anuncios,
insights). No existe -ni debe agregarse- ningún método que modifique,
pause o cree recursos en Meta Ads.
"""

from datetime import date

import httpx

from app.core.config import get_settings

GRAPH_BASE_URL = "https://graph.facebook.com"


class MetaClient:
    def __init__(self, access_token: str, api_version: str | None = None):
        self.access_token = access_token
        self.api_version = api_version or get_settings().meta_api_version
        self._client = httpx.Client(base_url=f"{GRAPH_BASE_URL}/{self.api_version}", timeout=30.0)

    def _get(self, path: str, params: dict | None = None) -> dict:
        params = {**(params or {}), "access_token": self.access_token}
        response = self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    def get_ad_accounts(self) -> list[dict]:
        data = self._get("/me/adaccounts", {"fields": "id,name,account_status"})
        return data.get("data", [])

    def get_campaigns(self, ad_account_id: str) -> list[dict]:
        data = self._get(
            f"/{ad_account_id}/campaigns",
            {"fields": "id,name,objective,status,daily_budget"},
        )
        return data.get("data", [])

    def get_ad_sets(self, campaign_id: str) -> list[dict]:
        data = self._get(
            f"/{campaign_id}/adsets",
            {"fields": "id,name,status,targeting"},
        )
        return data.get("data", [])

    def get_ads(self, ad_set_id: str) -> list[dict]:
        data = self._get(
            f"/{ad_set_id}/ads",
            {"fields": "id,name,status,creative"},
        )
        return data.get("data", [])

    def get_insights(self, ad_id: str, since: date, until: date) -> list[dict]:
        data = self._get(
            f"/{ad_id}/insights",
            {
                "fields": "spend,impressions,clicks,ctr,cpc,cpm,frequency,actions",
                "time_range": f'{{"since":"{since.isoformat()}","until":"{until.isoformat()}"}}',
                "time_increment": 1,
            },
        )
        return data.get("data", [])

    def close(self) -> None:
        self._client.close()


def build_oauth_url(redirect_uri: str | None = None) -> str:
    settings = get_settings()
    redirect = redirect_uri or settings.meta_redirect_uri
    scopes = "ads_read,business_management"
    return (
        f"https://www.facebook.com/{settings.meta_api_version}/dialog/oauth"
        f"?client_id={settings.meta_app_id}"
        f"&redirect_uri={redirect}"
        f"&scope={scopes}"
        f"&response_type=code"
    )


def exchange_code_for_token(code: str, redirect_uri: str | None = None) -> dict:
    settings = get_settings()
    redirect = redirect_uri or settings.meta_redirect_uri
    with httpx.Client(base_url=f"{GRAPH_BASE_URL}/{settings.meta_api_version}", timeout=30.0) as client:
        response = client.get(
            "/oauth/access_token",
            params={
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "redirect_uri": redirect,
                "code": code,
            },
        )
        response.raise_for_status()
        return response.json()
