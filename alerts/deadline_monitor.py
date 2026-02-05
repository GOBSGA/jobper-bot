"""
Monitor de deadlines para Jobper Bot v3.0
Detecta y notifica contratos con fechas límite próximas
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from config import Config
from database.manager import DatabaseManager

logger = logging.getLogger(__name__)


class UrgencyLevel:
    """Niveles de urgencia para alertas de deadline."""

    # Nivel 1: Cierra HOY
    TODAY = 1

    # Nivel 2: Cierra MAÑANA
    TOMORROW = 2

    # Nivel 3: Cierra en 3 días o menos
    SOON = 3

    LABELS = {
        1: {"emoji": "🔴", "label": "URGENTE - Cierra HOY", "priority": "critical"},
        2: {"emoji": "🟠", "label": "Cierra MAÑANA", "priority": "high"},
        3: {"emoji": "🟡", "label": "Cierra en 3 días", "priority": "medium"},
    }

    @classmethod
    def get_label(cls, level: int) -> Dict[str, str]:
        """Obtiene la etiqueta para un nivel de urgencia."""
        return cls.LABELS.get(level, {"emoji": "⚪", "label": "Sin urgencia", "priority": "low"})


class DeadlineMonitor:
    """
    Monitor de fechas límite para contratos.

    Detecta contratos con deadlines próximos y envía alertas
    a usuarios que tienen esos contratos como relevantes.
    """

    def __init__(self, db: Optional[DatabaseManager] = None, whatsapp=None):
        """
        Inicializa el monitor de deadlines.

        Args:
            db: Instancia de DatabaseManager (opcional, se crea si no se provee)
            whatsapp: Cliente de WhatsApp para enviar notificaciones
        """
        self.db = db or DatabaseManager()
        self.whatsapp = whatsapp

    def check_urgent_deadlines(self, days_threshold: int = None) -> Dict[str, Any]:
        """
        Revisa todos los contratos con deadlines próximos y envía alertas.

        Args:
            days_threshold: Días máximo para considerar urgente (default: Config)

        Returns:
            Dict con estadísticas de alertas enviadas
        """
        if days_threshold is None:
            days_threshold = Config.URGENT_DEADLINE_DAYS

        stats = {
            "contracts_checked": 0,
            "alerts_sent": 0,
            "users_notified": 0,
            "errors": 0,
            "by_urgency": {1: 0, 2: 0, 3: 0}
        }

        try:
            # Obtener contratos con deadline próximo
            contracts = self.db.get_contracts_with_deadline_soon(days=days_threshold)
            stats["contracts_checked"] = len(contracts)

            if not contracts:
                logger.info("No hay contratos con deadlines próximos")
                return stats

            # Obtener usuarios activos
            active_users = self.db.get_active_users()

            if not active_users:
                logger.info("No hay usuarios activos para notificar")
                return stats

            # Para cada contrato con deadline próximo
            users_notified = set()

            for contract in contracts:
                urgency_level = self._calculate_urgency(contract.get("deadline"))

                if urgency_level is None:
                    continue

                # Buscar usuarios que tengan este contrato como relevante
                for user in active_users:
                    # Verificar si ya se envió esta alerta
                    if self.db.is_deadline_alert_sent(
                        user_id=user["id"],
                        contract_id=contract["id"],
                        urgency_level=urgency_level
                    ):
                        continue

                    # Verificar si el contrato es relevante para el usuario
                    if not self._is_relevant_for_user(contract, user):
                        continue

                    # Enviar alerta
                    success = self._send_deadline_alert(
                        user=user,
                        contract=contract,
                        urgency_level=urgency_level
                    )

                    if success:
                        # Marcar como enviada
                        self.db.mark_deadline_alert_sent(
                            user_id=user["id"],
                            contract_id=contract["id"],
                            urgency_level=urgency_level
                        )
                        stats["alerts_sent"] += 1
                        stats["by_urgency"][urgency_level] += 1
                        users_notified.add(user["id"])
                    else:
                        stats["errors"] += 1

            stats["users_notified"] = len(users_notified)

            logger.info(
                f"Deadline check: {stats['contracts_checked']} contratos, "
                f"{stats['alerts_sent']} alertas enviadas a {stats['users_notified']} usuarios"
            )

        except Exception as e:
            logger.error(f"Error en check_urgent_deadlines: {e}")
            stats["errors"] += 1

        return stats

    def _calculate_urgency(self, deadline: Optional[datetime]) -> Optional[int]:
        """
        Calcula el nivel de urgencia basado en el deadline.

        Args:
            deadline: Fecha límite del contrato

        Returns:
            Nivel de urgencia (1, 2, 3) o None si no es urgente
        """
        if not deadline:
            return None

        if isinstance(deadline, str):
            try:
                deadline = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
            except ValueError:
                return None

        now = datetime.now()

        # Asegurar que deadline no tenga timezone si now no lo tiene
        if deadline.tzinfo is not None:
            deadline = deadline.replace(tzinfo=None)

        days_until = (deadline - now).days

        if days_until < 0:
            # Ya venció
            return None
        elif days_until == 0:
            return UrgencyLevel.TODAY
        elif days_until == 1:
            return UrgencyLevel.TOMORROW
        elif days_until <= 3:
            return UrgencyLevel.SOON
        else:
            return None

    def _is_relevant_for_user(self, contract: Dict[str, Any], user: Dict[str, Any]) -> bool:
        """
        Verifica si un contrato es relevante para un usuario.

        Criterios:
        - País coincide
        - Ya fue enviado anteriormente (está en historial)
        - O tiene match de keywords

        Args:
            contract: Diccionario del contrato
            user: Diccionario del usuario

        Returns:
            True si el contrato es relevante
        """
        # Verificar país
        user_countries = user.get("countries", "all")
        contract_country = contract.get("country", "")

        if user_countries not in ("all", "both"):
            if contract_country == "multilateral":
                pass  # Multilaterales siempre relevantes
            elif user_countries != contract_country:
                return False

        # Verificar si el contrato ya fue enviado a este usuario
        if self.db.is_contract_sent_to_user(user["id"], contract["id"]):
            return True

        # Verificar keywords
        user_keywords = self._get_user_keywords(user)
        if not user_keywords:
            return False

        contract_text = (
            (contract.get("title") or "") + " " +
            (contract.get("description") or "")
        ).lower()

        return any(kw.lower() in contract_text for kw in user_keywords)

    def _get_user_keywords(self, user: Dict[str, Any]) -> List[str]:
        """Obtiene todas las keywords del usuario."""
        keywords = []

        # Keywords de industria
        industry = user.get("industry")
        if industry and industry in Config.INDUSTRIES:
            keywords.extend(Config.INDUSTRIES[industry].get("keywords", []))

        # Keywords personalizadas
        include_kw = user.get("include_keywords", [])
        if include_kw:
            keywords.extend(include_kw)

        return keywords

    def _send_deadline_alert(
        self,
        user: Dict[str, Any],
        contract: Dict[str, Any],
        urgency_level: int
    ) -> bool:
        """
        Envía una alerta de deadline a un usuario.

        Args:
            user: Diccionario del usuario
            contract: Diccionario del contrato
            urgency_level: Nivel de urgencia (1, 2, 3)

        Returns:
            True si se envió exitosamente
        """
        if not self.whatsapp:
            logger.debug("WhatsApp client no disponible, alerta no enviada")
            return False

        try:
            urgency_info = UrgencyLevel.get_label(urgency_level)

            # Formatear mensaje
            message = self._format_alert_message(contract, urgency_info)

            # Enviar
            success = self.whatsapp.send_message(
                to=user["phone"],
                body=message
            )

            if success:
                logger.info(
                    f"Alerta enviada a {user['phone']}: "
                    f"{contract.get('title', '')[:50]} - {urgency_info['label']}"
                )

            return success

        except Exception as e:
            logger.error(f"Error enviando alerta: {e}")
            return False

    def _format_alert_message(
        self,
        contract: Dict[str, Any],
        urgency_info: Dict[str, str]
    ) -> str:
        """Formatea el mensaje de alerta."""
        deadline = contract.get("deadline")
        if isinstance(deadline, datetime):
            deadline_str = deadline.strftime("%d/%m/%Y %H:%M")
        else:
            deadline_str = str(deadline) if deadline else "No especificado"

        # Formatear monto
        amount = contract.get("amount")
        if amount:
            currency = contract.get("currency", "COP")
            if currency == "COP":
                amount_str = f"${amount:,.0f} COP"
            else:
                amount_str = f"${amount:,.2f} {currency}"
        else:
            amount_str = "No especificado"

        message = f"""
{urgency_info['emoji']} *ALERTA DE DEADLINE*
{urgency_info['label']}

*{contract.get('title', 'Sin título')[:200]}*

Entidad: {contract.get('entity', 'No especificada')}
Valor: {amount_str}
Fuente: {contract.get('source', 'N/A')}

Fecha limite: {deadline_str}

{contract.get('url', '')}

---
Responde "silenciar" para pausar alertas urgentes.
""".strip()

        return message

    def get_pending_deadlines_for_user(
        self,
        user_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Obtiene contratos con deadlines próximos para un usuario específico.

        Args:
            user_id: ID del usuario
            days: Días hacia adelante para buscar

        Returns:
            Lista de contratos con deadline info
        """
        user = self.db.get_user_by_id(user_id)
        if not user:
            return []

        contracts = self.db.get_contracts_with_deadline_soon(days=days)

        relevant = []
        for contract in contracts:
            if self._is_relevant_for_user(contract, user):
                urgency = self._calculate_urgency(contract.get("deadline"))
                contract["urgency_level"] = urgency
                contract["urgency_info"] = UrgencyLevel.get_label(urgency) if urgency else None
                relevant.append(contract)

        # Ordenar por deadline
        relevant.sort(key=lambda x: x.get("deadline") or datetime.max)

        return relevant


def get_deadline_monitor(whatsapp=None) -> DeadlineMonitor:
    """Obtiene una instancia del monitor de deadlines."""
    return DeadlineMonitor(whatsapp=whatsapp)
