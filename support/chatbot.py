"""
Jobper Support — AI Chatbot con OpenAI GPT-4o-mini + caché semántico.

Arquitectura:
1. Caché exacta por hash MD5 de la pregunta normalizada (TTL 7 días)
2. Si no hay caché → OpenAI GPT-4o-mini con sistema de prompts rico sobre Jobper
3. Límite de mensajes por usuario según plan (free: 5/día, cazador: 25/día, competidor+: ilimitado)
4. Fallback a keyword matching si OpenAI no está disponible
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sistema de prompts — contexto completo de Jobper
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Eres el asistente virtual oficial de Jobper, la plataforma colombiana de inteligencia de contratos.
Tu misión es ayudar a los usuarios a maximizar sus oportunidades de negocio con contratos gubernamentales y privados.

## Sobre Jobper
Jobper es una plataforma SaaS que reúne contratos de múltiples fuentes (SECOP I & II, BID, Banco Mundial, Ecopetrol, EPM, UNGM y más).
Ofrece búsqueda inteligente, Pipeline CRM, Marketplace privado, análisis con IA, alertas y exportación a Excel.

## Planes y precios (en COP, IVA incluido)
- **Observador (Gratis)**: Búsqueda básica, 5 favoritos, 3 alertas/semana, sin descripción completa
- **Cazador ($29.900/mes)**: Descripción completa, match score, alertas ilimitadas, exportar Excel (50/mes)
- **Competidor ($149.900/mes)**: Todo de Cazador + Pipeline CRM, Marketplace, Análisis IA, Push notifications, exportar 500/mes
- **Estratega ($299.900/mes)**: Todo de Competidor + historial 2 años, multi-usuario (2 personas), reportes automáticos
- **Dominador ($599.900/mes)**: Todo de Estratega + inteligencia competitiva, acceso API, soporte prioritario, exportar ilimitado

## Pagos
Aceptamos transferencia bancaria (Nequi, Bancolombia, Bre-B). El usuario sube el comprobante en la plataforma y el plan se activa en máximo 24 horas hábiles.

## Funciones clave
- **Búsqueda inteligente**: Lenguaje natural, entiende ciudad, sector, presupuesto, fuente
- **Match Score**: % de compatibilidad entre perfil del usuario y el contrato
- **Pipeline CRM**: Lead → Propuesta → Enviado → Ganado/Perdido con notas y valores (plan Competidor+)
- **Marketplace**: Publicar contratos privados y conectar con proveedores (plan Competidor+)
- **Análisis IA**: GPT-4o-mini analiza el contrato: oportunidad, complejidad, competencia, requisitos, riesgos (plan Competidor+)
- **Alertas**: Email, push, WhatsApp y Telegram cuando hay contratos relevantes
- **Exportar Excel**: Resultados de búsqueda en .xlsx (plan Cazador+)

## Consultoría y estrategia de licitación
Cuando pregunten sobre estrategia, precios de propuestas o cómo ganar contratos:
- Explica cómo calcular precios competitivos considerando AIU (Administración, Imprevistos, Utilidad)
- Qué requisitos habituales pide SECOP vs contratos internacionales BID/Banco Mundial
- Cómo diferenciarse en la propuesta técnica
- Cuándo y cómo formar consorcios para contratos grandes
- Estrategias para empresas sin experiencia previa en contratación pública

## Reglas
- Responde siempre en español, tono profesional pero cercano
- Sé directo y concreto. Máximo 3-4 párrafos o usa listas
- No inventes precios, funciones o fechas que no conoces
- Si el problema es técnico urgente, recomienda soporte@jobper.co
- Si preguntan algo fuera del alcance de Jobper, deriva a soporte@jobper.co"""

# ---------------------------------------------------------------------------
# Fallback keyword matching
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FAQ:
    keywords: tuple[str, ...]
    question: str
    answer: str


KNOWLEDGE_BASE: list[FAQ] = [
    FAQ(
        ("precio", "plan", "costo", "valor", "pagar", "suscripción", "mensual"),
        "¿Cuánto cuesta Jobper?",
        "Tenemos 5 planes:\n• Observador — Gratis\n• Cazador — $29.900/mes\n• Competidor — $149.900/mes\n• Estratega — $299.900/mes\n• Dominador — $599.900/mes\nTodos incluyen los mismos contratos; la diferencia está en las funciones habilitadas.",
    ),
    FAQ(
        ("pago", "transferencia", "nequi", "bancolombia", "breb", "comprobante", "activar"),
        "¿Cómo pago?",
        "Aceptamos Nequi, Bancolombia y Bre-B. Haz la transferencia, sube el comprobante en Configuración → Plan y tu plan se activa en máximo 24 horas hábiles.",
    ),
    FAQ(
        ("cancelar", "anular", "desuscribir", "baja"),
        "¿Puedo cancelar?",
        "Sí, escríbenos a soporte@jobper.co. Tu acceso continúa hasta el final del período pagado.",
    ),
    FAQ(
        ("contrato", "licitación", "fuente", "secop", "datos", "origen", "fuentes"),
        "¿De dónde salen los contratos?",
        "Monitoreamos SECOP I y II, BID, Banco Mundial, ONU (UNGM), Ecopetrol, EPM y más. Actualizamos varias veces al día.",
    ),
    FAQ(
        ("pipeline", "crm", "seguimiento", "propuesta", "etapa"),
        "¿Qué es el Pipeline CRM?",
        "Organiza contratos en etapas: Lead → Propuesta → Enviado → Ganado/Perdido. Agrega notas y valores. Disponible desde el plan Competidor.",
    ),
    FAQ(
        ("marketplace", "publicar", "privado", "vender", "proveedor"),
        "¿Qué es el Marketplace?",
        "Publica tus propios contratos y encuentra subcontratistas. Disponible desde el plan Competidor.",
    ),
    FAQ(
        ("alerta", "notificación", "email", "push", "whatsapp", "telegram"),
        "¿Cómo funcionan las alertas?",
        "Recibes alertas por email, push, WhatsApp y Telegram cuando aparecen contratos relevantes para tu perfil. Configúralas en Configuración.",
    ),
    FAQ(
        ("soporte", "ayuda", "contacto", "problema", "error", "falla"),
        "¿Cómo contacto soporte?",
        "Escríbenos a soporte@jobper.co. Respondemos en horario comercial (lunes a viernes).",
    ),
    FAQ(
        ("referido", "referir", "descuento", "invitar", "código"),
        "¿Cómo funcionan los referidos?",
        "Comparte tu código desde el menú Referidos. Por cada amigo suscrito obtienes descuentos acumulables en tu plan.",
    ),
    FAQ(
        ("excel", "exportar", "descargar", "xlsx"),
        "¿Puedo exportar contratos a Excel?",
        "Sí, desde la búsqueda de contratos aparece el botón Exportar. Disponible desde el plan Cazador (50/mes), Competidor (500/mes) y Dominador (ilimitado).",
    ),
]


def _normalize(text: str) -> set[str]:
    text = text.lower()
    text = re.sub(r"[^a-záéíóúñü\s]", "", text)
    return {w for w in text.split() if len(w) > 2}


def _keyword_fallback(question: str) -> dict:
    words = _normalize(question)
    if not words:
        return _default_fallback()
    best, best_score = None, 0.0
    for faq in KNOWLEDGE_BASE:
        kw_set = set(faq.keywords)
        overlap = len(words & kw_set)
        if overlap == 0:
            continue
        score = overlap / len(kw_set)
        if score > best_score:
            best, best_score = faq, score
    if best and best_score >= 0.15:
        return {"matched": True, "answer": best.answer, "confidence": round(best_score, 2)}
    return _default_fallback()


def _default_fallback() -> dict:
    return {
        "matched": False,
        "answer": "No encontré una respuesta exacta. Escríbenos a soporte@jobper.co o reformula tu consulta.",
        "suggestions": [faq.question for faq in KNOWLEDGE_BASE[:5]],
    }


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


def _cache_key(question: str) -> str:
    return f"support_cache:{hashlib.md5(question.lower().strip().encode()).hexdigest()}"


def _get_cached(question: str) -> dict | None:
    try:
        from core.cache import cache
        return cache.get_json(_cache_key(question))
    except Exception:
        return None


def _set_cached(question: str, result: dict, ttl: int = 604_800) -> None:
    try:
        from core.cache import cache
        cache.set_json(_cache_key(question), result, ttl=ttl)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Daily rate limiting per user
# ---------------------------------------------------------------------------

DAILY_LIMITS: dict[str, int | None] = {
    "free": 5,
    "trial": 5,
    "cazador": 25,
    "alertas": 25,
    "starter": 25,
    "competidor": None,
    "estratega": None,
    "business": None,
    "dominador": None,
    "enterprise": None,
}


def _check_rate_limit(user_id: int, user_plan: str) -> tuple[bool, int | None]:
    limit = DAILY_LIMITS.get(user_plan, 5)
    if limit is None:
        return True, None
    try:
        from core.cache import cache
        import datetime
        today = datetime.date.today().isoformat()
        key = f"support_msgs:{user_id}:{today}"
        raw = cache.get(key)
        count = int(raw) if raw else 0
        if count >= limit:
            return False, 0
        cache.client.incr(key)
        cache.client.expire(key, 86_400)
        return True, limit - count - 1
    except Exception:
        return True, None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def find_answer(question: str, user_id: int | None = None, user_plan: str = "free") -> dict:
    """
    1. Check rate limit
    2. Check cache (exact question hash)
    3. Call OpenAI GPT-4o-mini
    4. Cache and return result
    5. Fallback to keyword matching if OpenAI unavailable
    """
    # Rate limit
    if user_id:
        allowed, remaining = _check_rate_limit(user_id, user_plan)
        if not allowed:
            limit = DAILY_LIMITS.get(user_plan, 5)
            return {
                "matched": False,
                "answer": (
                    f"Alcanzaste el límite de {limit} consultas diarias del plan {user_plan.title()}. "
                    "Actualiza tu plan para consultas ilimitadas, o vuelve mañana."
                ),
                "rate_limited": True,
                "upgrade_url": "/payments",
            }
    else:
        remaining = None

    # Cache hit
    cached = _get_cached(question)
    if cached:
        result = {**cached, "cached": True}
        if remaining is not None:
            result["messages_remaining"] = remaining
        return result

    # OpenAI
    try:
        from config import Config
        api_key = getattr(Config, "OPENAI_API_KEY", None)
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not configured")

        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            max_tokens=600,
            temperature=0.3,
        )
        answer = response.choices[0].message.content.strip()
        result = {"matched": True, "answer": answer, "ai": True}
        _set_cached(question, result)

    except Exception as e:
        logger.warning(f"[chatbot] OpenAI unavailable ({e}), using keyword fallback")
        result = _keyword_fallback(question)

    if remaining is not None:
        result["messages_remaining"] = remaining
    return result
