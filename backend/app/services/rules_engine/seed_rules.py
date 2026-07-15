"""Reglas globales del sistema (org_id = None). Se insertan una sola vez
(idempotente por `name`) — ver el uso en recommendation_service o en un
script de setup inicial."""

from sqlalchemy.orm import Session

from app.db.models import Rule

SEED_RULES: list[dict] = [
    {
        "name": "Fatiga de anuncio",
        "description": "Frecuencia alta y CTR cayendo: el creativo se está agotando.",
        "conditions": {
            "mode": "AND",
            "items": [
                {"metric": "frequency", "operator": "gt", "value": 3.5},
                {"metric": "ctr", "operator": "decreased_by_pct", "value": 25, "window_days": 7},
            ],
        },
        "action_type": "new_creatives",
        "priority": "alta",
    },
    {
        "name": "CPL sostenido por encima del objetivo",
        "description": "El CPL lleva 3 días seguidos por encima de un umbral considerado alto.",
        "conditions": {
            "mode": "AND",
            "items": [{"metric": "cpl", "operator": "sustained_above_for_days", "value": 15, "window_days": 3}],
        },
        "action_type": "review_targeting",
        "priority": "media",
    },
    {
        "name": "Oportunidad de escalar",
        "description": "CTR estable o en aumento y CPL bajo: hay espacio para subir presupuesto.",
        "conditions": {
            "mode": "AND",
            "items": [
                {"metric": "cpl", "operator": "lt", "value": 5},
                {"metric": "ctr", "operator": "gt", "value": 1.5},
            ],
        },
        "action_type": "scale_budget",
        "priority": "media",
    },
]


def ensure_seed_rules(db: Session) -> None:
    existing_names = {name for (name,) in db.query(Rule.name).filter(Rule.org_id.is_(None)).all()}

    for rule_data in SEED_RULES:
        if rule_data["name"] in existing_names:
            continue
        db.add(Rule(org_id=None, is_active=True, **rule_data))

    db.commit()
