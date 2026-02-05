"""
Smart Alerts System
Sistema de alertas inteligentes en tiempo real.

Detecta oportunidades relevantes, cambios importantes,
y genera notificaciones personalizadas para cada usuario.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
import threading
import queue

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    """Tipos de alertas."""
    NEW_OPPORTUNITY = "new_opportunity"      # Nueva oportunidad relevante
    HIGH_MATCH = "high_match"                # Oportunidad con alto match
    DEADLINE_URGENT = "deadline_urgent"      # Deadline próximo
    DEADLINE_TODAY = "deadline_today"        # Vence hoy
    PRICE_DROP = "price_drop"                # Reducción de precio/presupuesto
    NEW_ADDENDUM = "new_addendum"            # Adenda publicada
    MARKET_TREND = "market_trend"            # Tendencia de mercado
    COMPETITOR_ACTIVITY = "competitor_activity"  # Actividad en sector
    WEEKLY_DIGEST = "weekly_digest"          # Resumen semanal


class AlertPriority(str, Enum):
    """Prioridad de alertas."""
    CRITICAL = "critical"    # Requiere acción inmediata
    HIGH = "high"            # Importante
    NORMAL = "normal"        # Informativo
    LOW = "low"              # Puede esperar


class AlertChannel(str, Enum):
    """Canales de entrega."""
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"


@dataclass
class Alert:
    """Alerta generada."""
    id: str
    type: AlertType
    priority: AlertPriority
    user_phone: str

    # Contenido
    title: str
    message: str
    summary: str  # Versión corta para WhatsApp

    # Datos relacionados
    contract_id: Optional[str] = None
    contract_title: Optional[str] = None
    contract_url: Optional[str] = None
    score: Optional[float] = None
    deadline: Optional[datetime] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered: bool = False
    read: bool = False

    # Acciones
    action_url: Optional[str] = None
    action_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "contract_id": self.contract_id,
            "score": self.score,
            "created_at": self.created_at.isoformat()
        }

    def format_whatsapp(self) -> str:
        """Formatea para WhatsApp."""
        lines = []

        # Emoji por tipo
        type_emoji = {
            AlertType.NEW_OPPORTUNITY: "🆕",
            AlertType.HIGH_MATCH: "⭐",
            AlertType.DEADLINE_URGENT: "⚠️",
            AlertType.DEADLINE_TODAY: "🚨",
            AlertType.PRICE_DROP: "💰",
            AlertType.NEW_ADDENDUM: "📝",
            AlertType.MARKET_TREND: "📈",
            AlertType.COMPETITOR_ACTIVITY: "👀",
            AlertType.WEEKLY_DIGEST: "📊"
        }

        emoji = type_emoji.get(self.type, "📌")

        # Prioridad
        priority_indicator = {
            AlertPriority.CRITICAL: "🔴",
            AlertPriority.HIGH: "🟠",
            AlertPriority.NORMAL: "🟢",
            AlertPriority.LOW: "⚪"
        }

        priority = priority_indicator.get(self.priority, "")

        lines.append(f"{emoji} *{self.title}* {priority}")
        lines.append("")
        lines.append(self.summary)

        if self.score:
            lines.append(f"\n📊 Match: {self.score:.0f}%")

        if self.deadline:
            days_left = (self.deadline - datetime.now()).days
            if days_left == 0:
                lines.append("⏰ *Vence HOY*")
            elif days_left == 1:
                lines.append("⏰ Vence mañana")
            elif days_left > 0:
                lines.append(f"⏰ Vence en {days_left} días")

        if self.contract_url:
            lines.append(f"\n🔗 {self.contract_url}")

        if self.action_text:
            lines.append(f"\n💡 {self.action_text}")

        return "\n".join(lines)


@dataclass
class AlertRule:
    """Regla para generación de alertas."""
    id: str
    name: str
    enabled: bool = True

    # Condiciones
    alert_type: AlertType = AlertType.NEW_OPPORTUNITY
    min_score: float = 0
    max_score: float = 100
    keywords: List[str] = field(default_factory=list)
    countries: List[str] = field(default_factory=list)
    sectors: List[str] = field(default_factory=list)
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None

    # Timing
    time_window_hours: int = 24  # Solo contratos de las últimas N horas
    cooldown_minutes: int = 60   # No repetir alerta similar en N minutos

    # Delivery
    channels: List[AlertChannel] = field(default_factory=lambda: [AlertChannel.WHATSAPP])
    priority: AlertPriority = AlertPriority.NORMAL


class SmartAlertEngine:
    """
    Motor de alertas inteligentes.

    Procesa contratos y genera alertas personalizadas
    basadas en reglas y preferencias de usuario.
    """

    def __init__(self):
        """Inicializa el motor."""
        self._alert_queue: queue.Queue = queue.Queue()
        self._sent_alerts: Dict[str, datetime] = {}  # Para cooldown
        self._handlers: Dict[AlertChannel, Callable] = {}
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None

        # Reglas por defecto
        self._default_rules = self._create_default_rules()

        logger.info("SmartAlertEngine inicializado")

    def register_handler(self, channel: AlertChannel, handler: Callable):
        """
        Registra un handler para un canal de alertas.

        Args:
            channel: Canal de entrega
            handler: Función que recibe (alert: Alert) y envía
        """
        self._handlers[channel] = handler
        logger.info(f"Handler registrado para {channel.value}")

    def start(self):
        """Inicia el worker de alertas."""
        if self._running:
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
        logger.info("Alert engine worker iniciado")

    def stop(self):
        """Detiene el worker."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)

    def process_new_contracts(
        self,
        contracts: List[Any],
        users: List[Dict[str, Any]]
    ) -> int:
        """
        Procesa contratos nuevos y genera alertas.

        Args:
            contracts: Lista de contratos normalizados
            users: Lista de usuarios a evaluar

        Returns:
            Número de alertas generadas
        """
        alerts_generated = 0

        for user in users:
            if not user.get("notifications_enabled", True):
                continue

            user_alerts = self._evaluate_contracts_for_user(contracts, user)
            alerts_generated += len(user_alerts)

            for alert in user_alerts:
                self._queue_alert(alert)

        logger.info(f"Generadas {alerts_generated} alertas para {len(users)} usuarios")
        return alerts_generated

    def process_deadlines(
        self,
        contracts: List[Any],
        users: List[Dict[str, Any]]
    ) -> int:
        """
        Procesa deadlines próximos y genera alertas.

        Returns:
            Número de alertas generadas
        """
        alerts_generated = 0
        now = datetime.now()

        for contract in contracts:
            deadline = getattr(contract, 'deadline', None)
            if not deadline:
                continue

            days_until = (deadline - now).days

            if days_until < 0:
                continue  # Ya pasó

            # Determinar tipo de alerta según urgencia
            if days_until == 0:
                alert_type = AlertType.DEADLINE_TODAY
                priority = AlertPriority.CRITICAL
            elif days_until <= 2:
                alert_type = AlertType.DEADLINE_URGENT
                priority = AlertPriority.HIGH
            elif days_until <= 5:
                alert_type = AlertType.DEADLINE_URGENT
                priority = AlertPriority.NORMAL
            else:
                continue  # Aún hay tiempo

            # Generar alertas para usuarios relevantes
            for user in users:
                if self._is_contract_relevant_for_user(contract, user):
                    alert = self._create_deadline_alert(
                        contract, user, alert_type, priority, days_until
                    )
                    if alert and not self._is_in_cooldown(alert):
                        self._queue_alert(alert)
                        alerts_generated += 1

        return alerts_generated

    def generate_weekly_digest(
        self,
        user: Dict[str, Any],
        contracts: List[Any],
        stats: Dict[str, Any]
    ) -> Optional[Alert]:
        """
        Genera resumen semanal para un usuario.

        Args:
            user: Perfil del usuario
            contracts: Top contratos de la semana
            stats: Estadísticas del período

        Returns:
            Alert con el digest
        """
        if not contracts:
            return None

        phone = user.get("phone", "")

        # Construir mensaje
        summary_parts = [
            f"Esta semana encontramos {len(contracts)} oportunidades para ti.",
            f"📈 Sector más activo: {stats.get('top_sector', 'Tecnología')}",
            f"💰 Valor total: ${stats.get('total_value', 0)/1_000_000:.0f}M"
        ]

        # Top 3 contratos
        message_parts = ["*Top Oportunidades:*\n"]
        for i, contract in enumerate(contracts[:3], 1):
            title = getattr(contract, 'title', 'Sin título')[:50]
            score = getattr(contract, 'score', 0) if hasattr(contract, 'score') else 0
            message_parts.append(f"{i}. {title}")
            if score:
                message_parts.append(f"   Match: {score:.0f}%")

        alert = Alert(
            id=f"digest_{phone}_{datetime.now().strftime('%Y%m%d')}",
            type=AlertType.WEEKLY_DIGEST,
            priority=AlertPriority.NORMAL,
            user_phone=phone,
            title="Resumen Semanal de Oportunidades",
            message="\n".join(message_parts),
            summary="\n".join(summary_parts),
            action_text="Responde 'ver todas' para más detalles"
        )

        return alert

    def send_alert(self, alert: Alert, channel: AlertChannel = AlertChannel.WHATSAPP) -> bool:
        """
        Envía una alerta por un canal específico.

        Returns:
            True si se envió correctamente
        """
        handler = self._handlers.get(channel)
        if not handler:
            logger.warning(f"No hay handler para {channel.value}")
            return False

        try:
            handler(alert)
            alert.sent_at = datetime.now()
            alert.delivered = True

            # Registrar para cooldown
            cooldown_key = f"{alert.user_phone}:{alert.type.value}:{alert.contract_id}"
            self._sent_alerts[cooldown_key] = datetime.now()

            logger.info(f"Alerta enviada: {alert.type.value} a {alert.user_phone}")
            return True

        except Exception as e:
            logger.error(f"Error enviando alerta: {e}")
            return False

    def _evaluate_contracts_for_user(
        self,
        contracts: List[Any],
        user: Dict[str, Any]
    ) -> List[Alert]:
        """Evalúa contratos y genera alertas para un usuario."""
        alerts = []
        phone = user.get("phone", "")

        # Obtener scorer
        try:
            from intelligence.opportunity_scorer import get_opportunity_scorer
            scorer = get_opportunity_scorer()
        except ImportError:
            scorer = None

        for contract in contracts:
            # Calcular score si tenemos scorer
            score = 0
            if scorer:
                try:
                    contract_dict = contract.to_dict() if hasattr(contract, 'to_dict') else contract
                    result = scorer.score(contract_dict, user)
                    score = result.total_score
                except Exception:
                    pass

            # Verificar si es relevante
            if not self._is_contract_relevant_for_user(contract, user, score):
                continue

            # Determinar tipo y prioridad
            if score >= 80:
                alert_type = AlertType.HIGH_MATCH
                priority = AlertPriority.HIGH
            elif score >= 60:
                alert_type = AlertType.NEW_OPPORTUNITY
                priority = AlertPriority.NORMAL
            else:
                alert_type = AlertType.NEW_OPPORTUNITY
                priority = AlertPriority.LOW

            # Crear alerta
            alert = self._create_opportunity_alert(contract, user, score, alert_type, priority)

            if alert and not self._is_in_cooldown(alert):
                alerts.append(alert)

        return alerts

    def _is_contract_relevant_for_user(
        self,
        contract: Any,
        user: Dict[str, Any],
        score: float = 0
    ) -> bool:
        """Determina si un contrato es relevante para un usuario."""
        # Score mínimo
        if score > 0 and score < 40:
            return False

        # País
        user_countries = user.get("countries", "all")
        contract_country = getattr(contract, 'country', '') or ''

        if user_countries != "all":
            if contract_country.lower() not in user_countries.lower():
                # Permitir multilaterales siempre
                if contract_country.lower() != "multilateral":
                    return False

        # Presupuesto
        contract_amount = getattr(contract, 'amount', 0) or 0
        min_budget = user.get("min_budget")
        max_budget = user.get("max_budget")

        if contract_amount > 0:
            if min_budget and contract_amount < min_budget:
                return False
            if max_budget and contract_amount > max_budget:
                return False

        # Keywords de exclusión
        exclude_keywords = user.get("exclude_keywords", [])
        if exclude_keywords:
            text = f"{getattr(contract, 'title', '')} {getattr(contract, 'description', '')}".lower()
            if any(kw.lower() in text for kw in exclude_keywords):
                return False

        return True

    def _create_opportunity_alert(
        self,
        contract: Any,
        user: Dict[str, Any],
        score: float,
        alert_type: AlertType,
        priority: AlertPriority
    ) -> Alert:
        """Crea alerta de oportunidad."""
        phone = user.get("phone", "")
        contract_id = getattr(contract, 'external_id', '') or getattr(contract, 'id', '')
        title = getattr(contract, 'title', 'Sin título')
        url = getattr(contract, 'url', '')
        deadline = getattr(contract, 'deadline', None)
        amount = getattr(contract, 'amount', 0)
        currency = getattr(contract, 'currency', 'COP')

        # Formatear monto
        if amount:
            if amount >= 1_000_000_000:
                amount_str = f"${amount/1_000_000_000:.1f}B"
            elif amount >= 1_000_000:
                amount_str = f"${amount/1_000_000:.0f}M"
            else:
                amount_str = f"${amount:,.0f}"
            amount_str += f" {currency}"
        else:
            amount_str = "No especificado"

        # Construir mensaje
        summary = f"{title[:80]}..."
        if score >= 70:
            summary = f"🎯 {summary}"

        message = f"""
*{title}*

💰 Valor: {amount_str}
📊 Match con tu perfil: {score:.0f}%
"""

        if deadline:
            days_left = (deadline - datetime.now()).days
            if days_left >= 0:
                message += f"⏰ Cierra en {days_left} días\n"

        message += f"\n🔗 {url}" if url else ""

        return Alert(
            id=f"opp_{phone}_{contract_id}_{datetime.now().strftime('%Y%m%d%H%M')}",
            type=alert_type,
            priority=priority,
            user_phone=phone,
            title="Nueva Oportunidad" if alert_type == AlertType.NEW_OPPORTUNITY else "Oportunidad Destacada",
            message=message.strip(),
            summary=summary,
            contract_id=contract_id,
            contract_title=title,
            contract_url=url,
            score=score,
            deadline=deadline,
            action_text="Responde 'info' para más detalles"
        )

    def _create_deadline_alert(
        self,
        contract: Any,
        user: Dict[str, Any],
        alert_type: AlertType,
        priority: AlertPriority,
        days_until: int
    ) -> Alert:
        """Crea alerta de deadline."""
        phone = user.get("phone", "")
        contract_id = getattr(contract, 'external_id', '') or getattr(contract, 'id', '')
        title = getattr(contract, 'title', 'Sin título')
        url = getattr(contract, 'url', '')
        deadline = getattr(contract, 'deadline', None)

        if days_until == 0:
            urgency = "VENCE HOY"
        elif days_until == 1:
            urgency = "Vence mañana"
        else:
            urgency = f"Vence en {days_until} días"

        summary = f"⏰ {urgency}: {title[:60]}..."

        message = f"""
*{urgency}*

{title}

⏰ Fecha límite: {deadline.strftime('%d/%m/%Y %H:%M') if deadline else 'No especificada'}
"""

        if url:
            message += f"\n🔗 {url}"

        return Alert(
            id=f"deadline_{phone}_{contract_id}_{days_until}",
            type=alert_type,
            priority=priority,
            user_phone=phone,
            title=f"Deadline: {urgency}",
            message=message.strip(),
            summary=summary,
            contract_id=contract_id,
            contract_title=title,
            contract_url=url,
            deadline=deadline,
            action_text="¡No dejes pasar esta oportunidad!"
        )

    def _is_in_cooldown(self, alert: Alert, cooldown_minutes: int = 60) -> bool:
        """Verifica si una alerta similar está en cooldown."""
        cooldown_key = f"{alert.user_phone}:{alert.type.value}:{alert.contract_id}"
        last_sent = self._sent_alerts.get(cooldown_key)

        if last_sent:
            elapsed = (datetime.now() - last_sent).total_seconds() / 60
            if elapsed < cooldown_minutes:
                return True

        return False

    def _queue_alert(self, alert: Alert):
        """Agrega alerta a la cola de envío."""
        self._alert_queue.put(alert)

    def _process_queue(self):
        """Procesa la cola de alertas (worker thread)."""
        while self._running:
            try:
                alert = self._alert_queue.get(timeout=1)
                self.send_alert(alert)
                self._alert_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error procesando alerta: {e}")

    def _create_default_rules(self) -> List[AlertRule]:
        """Crea reglas por defecto."""
        return [
            AlertRule(
                id="high_match",
                name="Oportunidades con alto match",
                alert_type=AlertType.HIGH_MATCH,
                min_score=75,
                priority=AlertPriority.HIGH
            ),
            AlertRule(
                id="deadline_urgent",
                name="Deadlines urgentes",
                alert_type=AlertType.DEADLINE_URGENT,
                time_window_hours=72,
                priority=AlertPriority.HIGH
            ),
            AlertRule(
                id="new_opportunities",
                name="Nuevas oportunidades relevantes",
                alert_type=AlertType.NEW_OPPORTUNITY,
                min_score=50,
                priority=AlertPriority.NORMAL
            )
        ]


# Singleton
_alert_engine = None


def get_smart_alert_engine() -> SmartAlertEngine:
    """Obtiene la instancia singleton del motor de alertas."""
    global _alert_engine
    if _alert_engine is None:
        _alert_engine = SmartAlertEngine()
    return _alert_engine
