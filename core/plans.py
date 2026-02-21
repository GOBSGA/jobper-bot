"""
Centralized plan utilities and constants.
Single source of truth for plan hierarchy and normalization.
"""

# Dict mapping plan name → numeric level. Includes legacy aliases.
PLAN_ORDER = {
    "free": 0,
    "trial": 0,
    "cazador": 1,
    "competidor": 2,
    "dominador": 3,
    # Legacy aliases (same levels as their canonical equivalents)
    "alertas": 1,
    "starter": 1,
    "business": 2,
    "enterprise": 3,
}

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
    user_level = PLAN_ORDER.get(normalize_plan(user_plan), 0)
    req_level = PLAN_ORDER.get(normalize_plan(required_plan), 0)
    return user_level >= req_level
