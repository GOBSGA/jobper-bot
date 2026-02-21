"""
Jobper Services — CRM Pipeline (Lead → Proposal → Submitted → Won → Lost)
"""

from __future__ import annotations

import logging
from datetime import datetime

from core.database import Contract, PipelineEntry, UnitOfWork

logger = logging.getLogger(__name__)

STAGES = ["lead", "proposal", "submitted", "won", "lost"]


def get_pipeline(user_id: int) -> dict:
    """Get full pipeline grouped by stage."""
    with UnitOfWork() as uow:
        entries = uow.pipeline.get_for_user(user_id)
        grouped = {stage: [] for stage in STAGES}

        # Batch-load contract titles
        contract_ids = [e.contract_id for e in entries if e.contract_id]
        titles = {}
        if contract_ids:
            contracts = uow.session.query(Contract.id, Contract.title).filter(Contract.id.in_(contract_ids)).all()
            titles = {c.id: c.title for c in contracts}

        for entry in entries:
            stage = entry.stage if entry.stage in STAGES else "lead"
            title = titles.get(entry.contract_id) if entry.contract_id else None
            grouped[stage].append(_entry_to_dict(entry, contract_title=title))

        totals = {
            stage: {
                "count": len(items),
                "value": sum(e.get("value") or 0 for e in items),
            }
            for stage, items in grouped.items()
        }

    return {"stages": grouped, "totals": totals}


def add_to_pipeline(
    user_id: int,
    contract_id: int | None = None,
    private_contract_id: int | None = None,
    stage: str = "lead",
    value: float | None = None,
) -> dict:
    """Add a contract to user's pipeline."""
    if stage not in STAGES:
        return {"error": f"Stage inválido. Opciones: {', '.join(STAGES)}"}

    if not contract_id and not private_contract_id:
        return {"error": "Debes indicar un contrato (contract_id o private_contract_id)"}

    with UnitOfWork() as uow:
        entry = PipelineEntry(
            user_id=user_id,
            contract_id=contract_id,
            private_contract_id=private_contract_id,
            stage=stage,
            value=value,
        )
        uow.pipeline.create(entry)
        uow.commit()

        return _entry_to_dict(entry)


def move_stage(user_id: int, entry_id: int, new_stage: str) -> dict:
    """Move pipeline entry to a new stage."""
    if new_stage not in STAGES:
        return {"error": f"Stage inválido. Opciones: {', '.join(STAGES)}"}

    with UnitOfWork() as uow:
        entry = uow.pipeline.get(entry_id)
        if not entry or entry.user_id != user_id:
            return {"error": "Entrada no encontrada"}

        entry.stage = new_stage
        entry.updated_at = datetime.utcnow()
        uow.commit()

        return _entry_to_dict(entry)


def add_note(user_id: int, entry_id: int, text: str) -> dict:
    """Add a note to a pipeline entry."""
    with UnitOfWork() as uow:
        entry = uow.pipeline.get(entry_id)
        if not entry or entry.user_id != user_id:
            return {"error": "Entrada no encontrada"}

        notes = list(entry.notes or [])
        notes.append(
            {
                "text": text,
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        entry.notes = notes
        entry.updated_at = datetime.utcnow()
        uow.commit()

        return _entry_to_dict(entry)


def get_stats(user_id: int) -> dict:
    """Pipeline statistics: won value, conversion rates, etc."""
    with UnitOfWork() as uow:
        entries = uow.pipeline.get_for_user(user_id)

        by_stage = {}
        for e in entries:
            stage = e.stage or "lead"
            by_stage.setdefault(stage, []).append(e)

        total = len(entries)
        won = by_stage.get("won", [])
        lost = by_stage.get("lost", [])
        won_value = sum(e.value or 0 for e in won)

        conversion = (len(won) / total * 100) if total > 0 else 0

    return {
        "total_entries": total,
        "by_stage": {s: len(by_stage.get(s, [])) for s in STAGES},
        "won_count": len(won),
        "won_value": won_value,
        "lost_count": len(lost),
        "conversion_rate": round(conversion, 1),
    }


def get_renewals(user_id: int, days: int = 30) -> list[dict]:
    """Get won contracts expiring within N days."""
    from datetime import timedelta

    with UnitOfWork() as uow:
        won = uow.pipeline.get_by_stage(user_id, "won")
        now = datetime.utcnow()
        limit = now + timedelta(days=days)

        renewals = []
        for entry in won:
            if entry.follow_up_date and now <= entry.follow_up_date <= limit:
                renewals.append(_entry_to_dict(entry))

    return renewals


# =============================================================================
# HELPERS
# =============================================================================


def _entry_to_dict(entry: PipelineEntry, contract_title: str | None = None) -> dict:
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "contract_id": entry.contract_id,
        "contract_title": contract_title,
        "private_contract_id": entry.private_contract_id,
        "stage": entry.stage,
        "notes": entry.notes or [],
        "follow_up_date": entry.follow_up_date.isoformat() if entry.follow_up_date else None,
        "value": entry.value,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    }
