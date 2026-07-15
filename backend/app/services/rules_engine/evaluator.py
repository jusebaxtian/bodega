from app.db.models import Rule
from app.services.rules_engine.conditions import SnapshotLike, evaluate_conditions


def rule_matches(rule: Rule, snapshots: list[SnapshotLike]) -> bool:
    """rule.conditions tiene la forma {"mode": "AND"|"OR", "items": [condition, ...]}."""
    mode = rule.conditions.get("mode", "AND")
    items = rule.conditions.get("items", [])
    if not items:
        return False
    return evaluate_conditions(snapshots, items, mode=mode)


def matching_rules(rules: list[Rule], snapshots: list[SnapshotLike]) -> list[Rule]:
    return [rule for rule in rules if rule.is_active and rule_matches(rule, snapshots)]
