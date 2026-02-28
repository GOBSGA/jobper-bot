"""
Bridge module: provides analyze_contract() using ContractIntelligence.
Imported by services/contracts.py and core/tasks.py.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from core.database import UnitOfWork

logger = logging.getLogger(__name__)

# Lazy singleton
_engine: Optional["ContractIntelligence"] = None


def _get_engine():
    global _engine
    if _engine is None:
        from intelligence.contract_intelligence import ContractIntelligence

        _engine = ContractIntelligence()
    return _engine


def analyze_contract(contract_id: int, user_id: int) -> Dict[str, Any]:
    """Run AI analysis on a contract for a specific user."""
    with UnitOfWork() as uow:
        contract = uow.contracts.get(contract_id)
        if not contract:
            return {"error": "Contrato no encontrado"}

        user = uow.users.get(user_id)

        contract_dict = {
            "id": contract.id,
            "external_id": contract.external_id,
            "title": contract.title,
            "description": contract.description or "",
            "entity": contract.entity,
            "amount": contract.amount,
            "currency": contract.currency,
            "country": contract.country,
            "source": contract.source,
            "publication_date": contract.publication_date.isoformat() if contract.publication_date else None,
            "deadline": contract.deadline.isoformat() if contract.deadline else None,
        }

        user_profile = None
        if user:
            user_profile = {
                "sector": user.sector,
                "keywords": user.keywords or [],
                "city": user.city,
                "budget_min": user.budget_min,
                "budget_max": user.budget_max,
            }

        engine = _get_engine()
        analysis = engine.analyze(contract_dict, user_profile)

        # Convert dataclass to dict for JSON serialization
        return {
            "contract_id": analysis.contract_id,
            "contract_type": analysis.contract_type.value if hasattr(analysis.contract_type, "value") else str(analysis.contract_type),
            "complexity": analysis.complexity.value if hasattr(analysis.complexity, "value") else str(analysis.complexity),
            "competition_level": analysis.competition_level.value if hasattr(analysis.competition_level, "value") else str(analysis.competition_level),
            "opportunity_score": analysis.opportunity_score,
            "fit_score": analysis.fit_score,
            # ContractRequirement objects → plain strings for frontend
            "requirements": [r.description for r in analysis.requirements] if analysis.requirements else [],
            "key_technologies": analysis.key_technologies,
            "certifications_required": analysis.certifications_required,
            "key_deliverables": analysis.key_deliverables,
            "mentioned_standards": analysis.mentioned_standards,
            "min_experience_years": analysis.min_experience_years,
            "estimated_duration_days": analysis.estimated_duration_days,
            "requires_consortium": analysis.requires_consortium,
            "allows_foreign_companies": analysis.allows_foreign_companies,
            "requires_local_presence": analysis.requires_local_presence,
            # Map ContractInsight objects (no warnings/recommendations fields in dataclass)
            "warnings": [i.description for i in analysis.insights if i.type == "risk"],
            "recommendations": [i.description for i in analysis.insights if i.type in ("recommendation", "opportunity")],
        }
