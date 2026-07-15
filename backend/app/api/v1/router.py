from fastapi import APIRouter

from app.api.v1 import ad_accounts, ai, health, me, meta, orgs, recommendations, rules

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(me.router)
api_router.include_router(orgs.router)
api_router.include_router(meta.router)
api_router.include_router(ad_accounts.router)
api_router.include_router(recommendations.router)
api_router.include_router(rules.router)
api_router.include_router(ai.router)
