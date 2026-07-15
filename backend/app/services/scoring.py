"""Calcula el puntaje IA (0-100) de una campaña a partir de sus recomendaciones
pendientes. Es una heurística simple y transparente (no una caja negra):
cada recomendación pendiente resta puntos según su prioridad."""

PRIORITY_PENALTY = {"alta": 25, "media": 10, "baja": 5}


def compute_campaign_score(pending_priorities: list[str]) -> int:
    score = 100
    for priority in pending_priorities:
        score -= PRIORITY_PENALTY.get(priority, 5)
    return max(score, 0)


def health_status_for_score(score: int) -> str:
    if score >= 90:
        return "excelente"
    if score >= 70:
        return "buena"
    if score >= 50:
        return "atencion"
    return "critica"
