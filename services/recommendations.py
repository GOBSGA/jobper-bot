"""
Jobper — AI Contract Recommendations
Finds the top contracts for a user's company profile using a single GPT-4o-mini call.

Cost architecture (near-zero):
1. Pre-filter top 10 contracts using free algorithmic match score
2. Single GPT-4o-mini call for all 10 contracts → 1 ranking + 1-sentence reasoning each
3. Cache result 24h per user — AI cost ~$0.001/user/day
4. Falls back to sorted match scores if OpenAI unavailable (free, always works)
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, datetime, timezone

logger = logging.getLogger(__name__)

_CACHE_TTL = 86_400  # 24 hours


def _cache_key(user_id: int) -> str:
    today = date.today().isoformat()
    return f"ai_recs:{user_id}:{today}"


def _get_cached(user_id: int) -> dict | None:
    try:
        from core.cache import cache
        return cache.get_json(_cache_key(user_id))
    except Exception:
        return None


def _set_cached(user_id: int, result: dict) -> None:
    try:
        from core.cache import cache
        cache.set_json(_cache_key(user_id), result, ttl=_CACHE_TTL)
    except Exception:
        pass


def get_recommendations(user_id: int, limit: int = 5) -> dict:
    """
    Return top contracts for the user with AI reasoning.
    Cached 24h. Falls back to pure match-score ranking if OpenAI unavailable.
    """
    # Cache hit
    cached = _get_cached(user_id)
    if cached:
        return {**cached, "cached": True}

    # Load user + top matches
    try:
        from core.database import UnitOfWork
        with UnitOfWork() as uow:
            user = uow.users.get(user_id)
            if not user:
                return {"error": "Usuario no encontrado"}

            user_profile = {
                "company_name": user.company_name or "",
                "sector": user.sector or "",
                "keywords": user.keywords or [],
                "city": user.city or "",
                "budget_min": user.budget_min,
                "budget_max": user.budget_max,
            }

        # Get top matched contracts (free algorithmic score)
        from services.matching import get_matched_contracts
        contracts = get_matched_contracts(user_id, min_score=0, limit=20)

        if not contracts:
            return {
                "contracts": [],
                "summary": "Configura tu perfil con sector y palabras clave para recibir recomendaciones.",
                "ai": False,
            }

        # Sort by match_score desc, take top N for AI analysis
        top = sorted(contracts, key=lambda c: c.get("match_score", 0), reverse=True)[:10]

    except Exception as e:
        logger.error(f"[recommendations] Failed to load contracts: {e}")
        return {"error": "Error cargando contratos"}

    # Try AI ranking
    try:
        from config import Config
        api_key = getattr(Config, "OPENAI_API_KEY", None)
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        import openai
        client = openai.OpenAI(api_key=api_key)

        # Build compact contract list for the prompt
        contracts_text = "\n".join(
            f"{i+1}. [{c.get('source','?')}] {c.get('title','?')} | "
            f"Entidad: {c.get('entity','?')} | "
            f"Presupuesto: ${c.get('amount') or '?'} COP | "
            f"Score compatibilidad: {c.get('match_score', 0)}% | "
            f"Descripción: {str(c.get('description') or '')[:300]}"
            for i, c in enumerate(top)
        )

        keywords_str = ", ".join(user_profile["keywords"]) if user_profile["keywords"] else "no especificadas"

        system = (
            "Eres el asistente de inteligencia de contratos de Jobper. "
            "Tu tarea es ayudar a empresas colombianas a priorizar oportunidades de licitación. "
            "Responde SIEMPRE en español, de forma directa y concreta."
        )

        user_msg = (
            f"Empresa: {user_profile['company_name'] or 'Sin nombre'}\n"
            f"Sector: {user_profile['sector'] or 'No especificado'}\n"
            f"Ciudad: {user_profile['city'] or 'No especificada'}\n"
            f"Palabras clave: {keywords_str}\n"
            f"Presupuesto objetivo: ${user_profile['budget_min'] or 0} – ${user_profile['budget_max'] or '∞'} COP\n\n"
            f"Contratos disponibles:\n{contracts_text}\n\n"
            f"Analiza estos contratos y devuelve un JSON con esta estructura exacta:\n"
            '{\n'
            '  "ranking": [\n'
            '    {"index": 1, "reason": "Explicación de 1 oración por qué este contrato es ideal"}\n'
            '  ],\n'
            '  "summary": "Resumen de 1-2 oraciones sobre el panorama de oportunidades para esta empresa"\n'
            '}\n\n'
            f"Ordena los {min(5, len(top))} mejores contratos por oportunidad real para esta empresa específica. "
            "El índice corresponde al número en la lista de contratos. Solo JSON, sin texto adicional."
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=500,
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content.strip()
        ai_data = json.loads(raw)
        ranking = ai_data.get("ranking", [])
        summary = ai_data.get("summary", "")

        # Build final result: reorder contracts by AI ranking
        ranked_contracts = []
        used_indices = set()
        for item in ranking:
            idx = item.get("index", 0) - 1  # Convert 1-based to 0-based
            if 0 <= idx < len(top) and idx not in used_indices:
                used_indices.add(idx)
                contract = dict(top[idx])
                contract["ai_reason"] = item.get("reason", "")
                ranked_contracts.append(contract)

        # Append any unranked contracts at the end (no AI reason)
        for i, c in enumerate(top[:limit]):
            if i not in used_indices and len(ranked_contracts) < limit:
                ranked_contracts.append(dict(c))

        result = {
            "contracts": ranked_contracts[:limit],
            "summary": summary,
            "ai": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        _set_cached(user_id, result)
        return result

    except Exception as e:
        logger.warning(f"[recommendations] OpenAI unavailable ({e}), using score-only ranking")

    # Fallback: return top by score without AI reasoning
    result = {
        "contracts": top[:limit],
        "summary": "Contratos ordenados por compatibilidad con tu perfil.",
        "ai": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    _set_cached(user_id, result)
    return result
