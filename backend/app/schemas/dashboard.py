import uuid
from datetime import date

from pydantic import BaseModel


class DashboardKPIs(BaseModel):
    total_spend: float
    avg_cpl: float | None
    avg_ctr: float
    total_conversions: int
    avg_frequency: float
    campaign_count: int


class CampaignRankingItem(BaseModel):
    campaign_id: uuid.UUID
    name: str
    score: int
    health_status: str


class DashboardSummaryOut(BaseModel):
    kpis: DashboardKPIs
    best_campaigns: list[CampaignRankingItem]
    critical_campaigns: list[CampaignRankingItem]
    top_alerts: list[dict]


class AdWithMetricsOut(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    creative_type: str | None
    latest_metrics: dict | None


class AdSetWithAdsOut(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    ads: list[AdWithMetricsOut]


class CampaignDetailOut(BaseModel):
    id: uuid.UUID
    name: str
    objective: str | None
    status: str
    score: int | None
    health_status: str | None
    ad_sets: list[AdSetWithAdsOut]
    snapshot_dates: list[date]
