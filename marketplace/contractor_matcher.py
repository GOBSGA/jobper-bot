"""
Sistema de matching de contratistas para el marketplace de Jobper.

Encuentra y notifica a contratistas relevantes cuando se publica
un nuevo trabajo privado en la plataforma.

Algoritmo de matching:
1. Filtro por país/ciudad
2. Match por industria/categoría
3. Match por keywords en perfil
4. Score de relevancia
5. Notificación a los mejores candidatos
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import Config
from database.manager import DatabaseManager

logger = logging.getLogger(__name__)

# Lazy import para evitar circular imports
_whatsapp_client = None


def _get_whatsapp_client():
    """Obtiene el cliente de WhatsApp de forma lazy."""
    global _whatsapp_client
    if _whatsapp_client is None:
        from notifications.whatsapp import WhatsAppClient

        _whatsapp_client = WhatsAppClient()
    return _whatsapp_client


class ContractorMatcher:
    """
    Sistema de matching entre contratos privados y contratistas.

    Encuentra los mejores candidatos para un trabajo y los notifica.
    """

    # Mapeo de categorías a industrias relacionadas
    CATEGORY_TO_INDUSTRY = {
        "tecnologia": ["tecnologia", "software"],
        "software": ["tecnologia", "software"],
        "construccion": ["construccion", "ingenieria"],
        "ingenieria": ["ingenieria", "construccion"],
        "pintura": ["construccion"],
        "electricidad": ["construccion", "ingenieria"],
        "plomeria": ["construccion"],
        "consultoria": ["consultoria", "legal"],
        "legal": ["legal", "consultoria"],
        "contabilidad": ["legal", "consultoria"],
        "diseño": ["publicidad", "marketing"],
        "marketing": ["marketing", "publicidad"],
        "transporte": ["logistica", "transporte"],
        "seguridad": ["seguridad"],
        "limpieza": ["servicios"],
        "catering": ["servicios", "alimentos"],
        "mantenimiento": ["construccion", "servicios"],
    }

    # Keywords relacionadas por categoría
    CATEGORY_KEYWORDS = {
        "tecnologia": ["software", "desarrollo", "programación", "app", "sistema", "web"],
        "construccion": ["obra", "construcción", "albañil", "edificio"],
        "pintura": ["pintar", "pintura", "pintores"],
        "diseño": ["diseño", "gráfico", "logo", "branding", "ui", "ux"],
        "marketing": ["marketing", "publicidad", "redes", "seo", "ads", "digital"],
        "consultoria": ["consultoría", "asesoría", "estrategia"],
        "legal": ["abogado", "legal", "contrato", "jurídico"],
        "contabilidad": ["contador", "impuestos", "facturación", "nómina"],
    }

    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()

    def find_and_notify(self, contract_id: int, posting: Dict[str, Any], max_notifications: int = 20) -> Dict[str, Any]:
        """
        Encuentra contratistas relevantes y los notifica.

        Args:
            contract_id: ID del contrato privado
            posting: Datos del contrato
            max_notifications: Máximo de notificaciones a enviar

        Returns:
            Dict con estadísticas del proceso
        """
        logger.info(f"🔍 Buscando contratistas para contrato #{contract_id}")

        stats = {"contract_id": contract_id, "candidates_found": 0, "notifications_sent": 0, "errors": 0}

        try:
            # Obtener candidatos
            candidates = self.find_candidates(posting, limit=max_notifications * 2)
            stats["candidates_found"] = len(candidates)

            if not candidates:
                logger.info(f"No se encontraron candidatos para contrato #{contract_id}")
                return stats

            # Ordenar por score y tomar los mejores
            candidates.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            top_candidates = candidates[:max_notifications]

            # Notificar
            whatsapp = _get_whatsapp_client()
            for candidate in top_candidates:
                try:
                    success = self._notify_candidate(whatsapp, candidate, contract_id, posting)
                    if success:
                        stats["notifications_sent"] += 1
                except Exception as e:
                    logger.error(f"Error notificando a {candidate.get('phone')}: {e}")
                    stats["errors"] += 1

            logger.info(f"✅ Contrato #{contract_id}: {stats['notifications_sent']} notificaciones enviadas")

        except Exception as e:
            logger.error(f"Error en find_and_notify: {e}")
            stats["errors"] += 1

        return stats

    def find_candidates(self, posting: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        """
        Encuentra candidatos relevantes para un trabajo.

        Args:
            posting: Datos del contrato
            limit: Máximo de candidatos a retornar

        Returns:
            Lista de candidatos con match_score
        """
        category = posting.get("category")
        country = posting.get("country", "colombia")
        city = posting.get("city")
        is_remote = posting.get("is_remote", False)

        # Obtener usuarios activos
        if is_remote:
            # Para trabajo remoto, buscar en todo el país
            users = self.db.get_active_users()
        else:
            # Filtrar por país
            users = self.db.get_users_by_country(country)

        candidates = []
        for user in users:
            score = self._calculate_match_score(user, posting)

            if score > 0:
                candidate = {**user, "match_score": score}
                candidates.append(candidate)

        return candidates[:limit]

    def _calculate_match_score(self, user: Dict[str, Any], posting: Dict[str, Any]) -> float:
        """
        Calcula el score de match entre un usuario y un trabajo.

        Args:
            user: Datos del usuario
            posting: Datos del contrato

        Returns:
            Score entre 0 y 100
        """
        score = 0.0
        category = posting.get("category", "").lower()
        title = posting.get("title", "").lower()
        description = posting.get("description", "").lower()

        # 1. Match por industria (40 puntos máx)
        user_industry = user.get("industry", "").lower()
        related_industries = self.CATEGORY_TO_INDUSTRY.get(category, [category])

        if user_industry in related_industries:
            score += 40
        elif user_industry and category and user_industry in category:
            score += 30

        # 2. Match por keywords del usuario (30 puntos máx)
        user_keywords = user.get("include_keywords") or []
        text_to_search = f"{title} {description} {category}"

        keyword_matches = sum(1 for kw in user_keywords if kw.lower() in text_to_search)
        if keyword_matches > 0:
            score += min(30, keyword_matches * 10)

        # 3. Match por keywords de categoría (20 puntos máx)
        category_keywords = self.CATEGORY_KEYWORDS.get(category, [])
        for kw in category_keywords:
            if kw in user_industry or any(kw in uk.lower() for uk in user_keywords):
                score += 5
                if score >= 90:
                    break

        # 4. Bonus por ubicación (10 puntos)
        user_country = user.get("countries", "")
        posting_country = posting.get("country", "colombia")

        if user_country == posting_country or user_country in ["all", "global"]:
            score += 10

        return min(100, score)

    def _notify_candidate(self, whatsapp, candidate: Dict[str, Any], contract_id: int, posting: Dict[str, Any]) -> bool:
        """
        Envía notificación a un candidato sobre una oportunidad.

        Args:
            whatsapp: Cliente de WhatsApp
            candidate: Datos del candidato
            contract_id: ID del contrato
            posting: Datos del contrato

        Returns:
            True si se envió correctamente
        """
        phone = candidate.get("phone")
        if not phone:
            return False

        # Formatear mensaje
        title = posting.get("title", "Nueva oportunidad")

        # Presupuesto
        budget_min = posting.get("budget_min")
        budget_max = posting.get("budget_max")
        if budget_min and budget_max and budget_min != budget_max:
            budget_str = f"${budget_min:,.0f} - ${budget_max:,.0f} COP"
        elif budget_min:
            budget_str = f"${budget_min:,.0f} COP"
        else:
            budget_str = "Negociable"

        # Ubicación
        if posting.get("is_remote"):
            location_str = "🌐 Remoto"
        else:
            location_str = f"📍 {posting.get('city', 'Por definir')}"

        # Fecha límite
        deadline = posting.get("deadline")
        if deadline:
            try:
                if isinstance(deadline, str):
                    deadline = datetime.fromisoformat(deadline)
                deadline_str = deadline.strftime("%d/%m/%Y")
            except (ValueError, TypeError, AttributeError):
                deadline_str = "Flexible"
        else:
            deadline_str = "Flexible"

        # Score de match
        match_score = candidate.get("match_score", 0)

        message = f"""💼 *Nueva Oportunidad de Trabajo*

━━━━━━━━━━━━━━━━━━━━
📋 *{title}*

💰 *Presupuesto:* {budget_str}
{location_str}
📅 *Fecha límite:* {deadline_str}
⭐ *Compatibilidad:* {match_score:.0f}%
━━━━━━━━━━━━━━━━━━━━

Este trabajo coincide con tu perfil en Jobper.

*¿Te interesa?*
Responde "aplicar #{contract_id}" para mostrar interés.

_Jobper Marketplace_"""

        return whatsapp.send_message(phone, message)

    def get_contract_matches(self, user_phone: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene contratos privados que coinciden con el perfil de un usuario.

        Args:
            user_phone: Teléfono del usuario
            limit: Máximo de resultados

        Returns:
            Lista de contratos con match_score
        """
        user = self.db.get_user_by_phone(user_phone)
        if not user:
            return []

        # Obtener contratos activos
        contracts = self.db.get_active_private_contracts(country=user.get("countries"), limit=limit * 3)

        matches = []
        for contract in contracts:
            # Construir posting dict
            posting = {
                "category": contract.get("category"),
                "title": contract.get("title"),
                "description": contract.get("description"),
                "country": contract.get("country"),
                "city": contract.get("city"),
                "is_remote": contract.get("is_remote"),
            }

            score = self._calculate_match_score(user, posting)

            if score > 20:  # Umbral mínimo
                matches.append({**contract, "match_score": score})

        # Ordenar por score
        matches.sort(key=lambda x: x["match_score"], reverse=True)

        return matches[:limit]
