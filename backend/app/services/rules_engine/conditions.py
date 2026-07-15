"""Evaluadores puros de condiciones sobre una serie temporal de snapshots.

Cada snapshot es un objeto (InsightSnapshot o similar) con atributos numéricos
como `frequency`, `ctr`, `cpl`, `cpa`, `roas`, `spend`, `conversions`.
Las funciones aquí no tocan la base de datos: reciben datos, devuelven bool.
"""

from typing import Any, Protocol


class SnapshotLike(Protocol):
    snapshot_date: Any
    frequency: Any
    ctr: Any
    cpl: Any
    cpa: Any
    roas: Any
    spend: Any
    conversions: Any


def _get_metric(snapshot: SnapshotLike, metric: str) -> float | None:
    value = getattr(snapshot, metric, None)
    if value is None:
        return None
    return float(value)


def evaluate_condition(snapshots: list[SnapshotLike], condition: dict) -> bool:
    """snapshots debe venir ordenado ascendente por fecha (el más reciente al final)."""
    if not snapshots:
        return False

    metric = condition["metric"]
    operator = condition["operator"]
    threshold = condition.get("value")
    window_days = condition.get("window_days", 1)

    latest_value = _get_metric(snapshots[-1], metric)
    if latest_value is None:
        return False

    if operator == "gt":
        return latest_value > threshold
    if operator == "lt":
        return latest_value < threshold
    if operator == "gte":
        return latest_value >= threshold
    if operator == "lte":
        return latest_value <= threshold

    if operator in ("decreased_by_pct", "increased_by_pct"):
        if len(snapshots) <= window_days:
            return False
        baseline = _get_metric(snapshots[-1 - window_days], metric)
        if baseline is None or baseline == 0:
            return False
        change_pct = (latest_value - baseline) / baseline * 100
        if operator == "decreased_by_pct":
            return change_pct <= -threshold
        return change_pct >= threshold

    if operator in ("sustained_above_for_days", "sustained_below_for_days"):
        if len(snapshots) < window_days:
            return False
        recent = snapshots[-window_days:]
        values = [_get_metric(s, metric) for s in recent]
        if any(v is None for v in values):
            return False
        if operator == "sustained_above_for_days":
            return all(v > threshold for v in values)
        return all(v < threshold for v in values)

    raise ValueError(f"Operador de condición desconocido: {operator}")


def evaluate_conditions(snapshots: list[SnapshotLike], conditions: list[dict], mode: str = "AND") -> bool:
    results = [evaluate_condition(snapshots, c) for c in conditions]
    if mode == "OR":
        return any(results)
    return all(results)
