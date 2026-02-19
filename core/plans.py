"""
Centralized plan utilities and constants.
Single source of truth for plan hierarchy and normalization.
"""

PLAN_ORDER = ["free", "trial", "cazador", "competidor", "dominador"]

PLAN_ALIASES = {
    "alertas": "cazador",
    "starter": "cazador",
    "business": "competidor",
    "enterprise": "dominador",
    "trial": "free",
}


def normalize_plan(plan: str) -> str:
    """Normalize legacy plan names to current names."""
    if not plan:
        return "free"
    return PLAN_ALIASES.get(plan, plan)


def check_plan_access(user_plan: str, required_plan: str) -> bool:
    """Check if user's plan meets required plan tier."""
    try:
        user_normalized = normalize_plan(user_plan)
        required_normalized = normalize_plan(required_plan)

        user_idx = PLAN_ORDER.index(user_normalized)
        req_idx = PLAN_ORDER.index(required_normalized)

        return user_idx >= req_idx
    except ValueError:
        # Plan not in order list
        return False
