"""Jobper Support — FAQ Chatbot con keyword matching."""
from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Knowledge Base
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
        "Tenemos 3 planes:\n• Starter — $69.900/mes: búsqueda básica, 10 favoritos, 1 pipeline.\n• Business — $149.900/mes: búsqueda avanzada, favoritos ilimitados, pipelines ilimitados, alertas email.\n• Enterprise — $599.900/mes: todo Business + API, marketplace destacado, soporte prioritario.\nTodos incluyen 14 días de prueba gratis.",
    ),
    FAQ(
        ("prueba", "gratis", "trial", "probar", "free"),
        "¿Hay prueba gratis?",
        "Sí, todos los planes incluyen 14 días de prueba gratis sin tarjeta de crédito. Al registrarte con tu email inicias automáticamente el trial con acceso Business.",
    ),
    FAQ(
        ("pago", "wompi", "tarjeta", "pse", "nequi", "bancolombia"),
        "¿Cómo pago?",
        "Aceptamos todos los medios de pago colombianos a través de Wompi: tarjeta de crédito/débito, PSE, Nequi y Bancolombia. El cobro es mensual automático.",
    ),
    FAQ(
        ("cancelar", "anular", "desuscribir"),
        "¿Puedo cancelar mi suscripción?",
        "Sí, puedes cancelar en cualquier momento desde tu perfil. Tu acceso se mantiene hasta el final del período ya pagado.",
    ),
    FAQ(
        ("contrato", "licitación", "fuente", "secop", "datos"),
        "¿De dónde salen los contratos?",
        "Recopilamos contratos de SECOP I y II (gobierno colombiano), BID, Banco Mundial, ONU, Ecopetrol, EPM y más. Actualizamos varias veces al día.",
    ),
    FAQ(
        ("buscar", "búsqueda", "filtro", "encontrar"),
        "¿Cómo busco contratos?",
        "Escribe lo que buscas en lenguaje natural, por ejemplo: 'software en Bogotá más de 100 millones'. Nuestro motor entiende presupuesto, ciudad, fuente e industria.",
    ),
    FAQ(
        ("pipeline", "crm", "seguimiento", "propuesta"),
        "¿Qué es el Pipeline CRM?",
        "El pipeline te permite organizar contratos en etapas: Lead → Propuesta → Enviado → Ganado/Perdido. Agrega notas y lleva el control de tus oportunidades.",
    ),
    FAQ(
        ("marketplace", "publicar", "privado", "vender"),
        "¿Qué es el Marketplace?",
        "Publica tus propios contratos o servicios para que otros usuarios los encuentren. Los planes pagos pueden destacar publicaciones.",
    ),
    FAQ(
        ("referido", "referir", "descuento", "invitar", "código"),
        "¿Cómo funciona el programa de referidos?",
        "Comparte tu código de referido. Por cada amigo que se suscriba obtienes descuentos: 1 referido = 10%, 3 = 20%, 5 = 30%, 10 = 50%. Máximo 10 referidos activos por mes.",
    ),
    FAQ(
        ("alerta", "notificación", "email", "push"),
        "¿Cómo funcionan las alertas?",
        "Recibes alertas por email y notificación push cuando aparecen contratos que coinciden con tu perfil. Disponible desde el plan Business.",
    ),
    FAQ(
        ("seguridad", "datos", "privacidad"),
        "¿Mis datos están seguros?",
        "Usamos encriptación en tránsito y en reposo, autenticación sin contraseña (magic link), y nunca compartimos tu información con terceros.",
    ),
    FAQ(
        ("soporte", "ayuda", "contacto", "problema"),
        "¿Cómo contacto soporte?",
        "Escríbenos a soporte@jobper.co o usa este chat. Respondemos en menos de 24 horas (plan Enterprise: soporte prioritario).",
    ),
]


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def _normalize(text: str) -> set[str]:
    text = text.lower()
    text = re.sub(r"[^a-záéíóúñü\s]", "", text)
    return {w for w in text.split() if len(w) > 2}


def find_answer(question: str) -> dict:
    """Return best matching FAQ or a fallback message."""
    words = _normalize(question)
    if not words:
        return _fallback()

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
        return {
            "matched": True,
            "question": best.question,
            "answer": best.answer,
            "confidence": round(best_score, 2),
        }
    return _fallback()


def _fallback() -> dict:
    return {
        "matched": False,
        "answer": "No encontré una respuesta exacta. Puedes escribirnos a soporte@jobper.co o reformular tu pregunta.",
        "suggestions": [faq.question for faq in KNOWLEDGE_BASE[:5]],
    }
