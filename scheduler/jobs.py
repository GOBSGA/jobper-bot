"""
Scheduler de tareas para Jobper Bot v3.0
Maneja reportes semanales, alertas urgentes y tareas programadas
"""
from __future__ import annotations

import logging
import threading
import time
from typing import List, Dict, Any, Optional

import schedule

from config import Config
from database.manager import DatabaseManager
from database.models import ConversationState, Country
from scrapers.sam import CombinedScraper
from matching.engine import get_matching_engine
from notifications.whatsapp import WhatsAppClient
from alerts.deadline_monitor import get_deadline_monitor

logger = logging.getLogger(__name__)


class JobScheduler:
    """
    Programador de tareas para el bot v3.0.
    Maneja reportes semanales, alertas urgentes y búsquedas periódicas.
    """

    def __init__(self, use_semantic: bool = True):
        """
        Inicializa el scheduler.

        Args:
            use_semantic: Si True, usa matching semántico (requiere modelo NLP)
        """
        self.db = DatabaseManager()
        # v3.0: CombinedScraper con fuentes multilaterales y privadas
        self.scraper = CombinedScraper(include_multilateral=True, include_private=True)
        # v3.0: MatchingEngine con soporte semántico
        self.matcher = get_matching_engine(use_semantic=use_semantic)
        self.whatsapp = WhatsAppClient()
        # v3.0: Monitor de deadlines urgentes (con WhatsApp para enviar alertas)
        self.deadline_monitor = get_deadline_monitor(whatsapp=self.whatsapp)
        self._running = False
        self._thread = None

    def send_weekly_reports(self):
        """
        Envía reportes semanales a todos los usuarios activos.
        Esta es la tarea principal programada.
        """
        logger.info("=" * 50)
        logger.info("📊 Iniciando envío de reportes semanales...")

        # Obtener usuarios activos (retorna lista de dicts)
        active_users = self.db.get_active_users()
        logger.info(f"👥 Usuarios activos: {len(active_users)}")

        if not active_users:
            logger.info("No hay usuarios activos para enviar reportes")
            return

        # Procesar por país para optimizar llamadas a APIs
        # v3.0: Incluir fuentes multilaterales para todos los usuarios
        self._process_country_users(active_users, Country.COLOMBIA.value, ["colombia", "multilateral"])
        self._process_country_users(active_users, Country.USA.value, ["usa", "multilateral"])
        self._process_country_users(active_users, Country.BOTH.value, ["colombia", "usa", "multilateral"])

        logger.info("✅ Reportes semanales completados")

    def _process_country_users(
        self,
        all_users: List[Dict[str, Any]],
        country_filter: str,
        countries_to_fetch: List[str]
    ):
        """Procesa usuarios de un país específico."""

        # Filtrar usuarios por país (dict access)
        users = [u for u in all_users if u.get("countries") == country_filter]

        if not users:
            return

        logger.info(f"Procesando {len(users)} usuarios para {country_filter}")

        # Obtener todos los keywords únicos de estos usuarios
        all_keywords = set()
        for user in users:
            industry = user.get("industry")
            if industry and industry in Config.INDUSTRIES:
                all_keywords.update(Config.INDUSTRIES[industry].get("keywords", []))
            include_kw = user.get("include_keywords") or []
            if include_kw:
                all_keywords.update(include_kw)

        # Fetch contracts una sola vez con todas las keywords
        contracts = self.scraper.fetch_all(
            keywords=list(all_keywords),
            countries=countries_to_fetch,
            days_back=7
        )

        if not contracts:
            logger.info(f"No se encontraron contratos para {country_filter}")
            return

        # Procesar cada usuario
        for user in users:
            try:
                self._send_report_to_user(user, contracts)
            except Exception as e:
                logger.error(f"Error enviando reporte a {user.get('phone')}: {e}")

    def _send_report_to_user(self, user: Dict[str, Any], contracts):
        """Envía reporte personalizado a un usuario."""

        # Calcular matches para este usuario
        top_contracts = self.matcher.get_top_contracts(
            user=user,
            contracts=contracts,
            limit=10,
            min_score=25
        )

        if not top_contracts:
            # Enviar mensaje de que no hay contratos
            self.whatsapp.send_message(
                user["phone"],
                "📭 *Reporte Semanal*\n\nEsta semana no encontré oportunidades que coincidan con tu perfil. "
                "Considera ampliar tus criterios escribiendo \"perfil\"."
            )
            return

        # Filtrar contratos ya enviados
        new_contracts = []
        for sc in top_contracts:
            contract_record = self.db.get_contract_by_external_id(sc.contract.external_id)

            if contract_record:
                # Verificar si ya se envió a este usuario
                if not self.db.is_contract_sent_to_user(user["id"], contract_record["id"]):
                    new_contracts.append(sc)
            else:
                # Crear registro del contrato
                contract_record, _ = self.db.get_or_create_contract(
                    external_id=sc.contract.external_id,
                    **sc.contract.to_dict()
                )
                new_contracts.append(sc)

        if not new_contracts:
            logger.info(f"Usuario {user['phone']}: todos los contratos ya fueron enviados")
            return

        # Construir perfil del usuario para análisis IA
        user_profile = self._build_user_profile(user)

        # Enviar reporte con análisis IA
        success = self.whatsapp.send_weekly_report(
            to=user["phone"],
            scored_contracts=new_contracts,
            user_profile=user_profile,
            include_ai_analysis=True
        )

        if success:
            # Marcar contratos como enviados
            for sc in new_contracts:
                contract_record = self.db.get_contract_by_external_id(sc.contract.external_id)
                if contract_record:
                    self.db.mark_contract_sent(
                        user_id=user["id"],
                        contract_id=contract_record["id"],
                        relevance_score=sc.score
                    )

            logger.info(f"✅ Reporte enviado a {user['phone']}: {len(new_contracts)} contratos")

    def _build_user_profile(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construye el perfil del usuario para el análisis de IA.

        Args:
            user: Diccionario del usuario

        Returns:
            Dict con el perfil del usuario
        """
        return {
            "industry": user.get("industry"),
            "include_keywords": user.get("include_keywords") or [],
            "exclude_keywords": user.get("exclude_keywords") or [],
            "min_budget": user.get("min_budget"),
            "max_budget": user.get("max_budget"),
            "countries": user.get("countries", "both"),
        }

    def search_now_for_user(self, phone: str) -> str:
        """
        Ejecuta una búsqueda inmediata para un usuario específico.

        Args:
            phone: Número de teléfono del usuario

        Returns:
            Mensaje de respuesta
        """
        user = self.db.get_user_by_phone(phone)

        if not user or user.get("state") != ConversationState.ACTIVE.value:
            return "⚠️ Primero completa tu configuración escribiendo \"menu\""

        # Determinar países a buscar (v3.0: siempre incluir multilateral)
        user_countries = user.get("countries", "")
        if user_countries == Country.COLOMBIA.value:
            countries = ["colombia", "multilateral"]
        elif user_countries == Country.USA.value:
            countries = ["usa", "multilateral"]
        else:
            countries = ["colombia", "usa", "multilateral"]

        # Obtener keywords
        keywords = list(self.matcher._get_user_keywords(user))

        # Buscar contratos
        contracts = self.scraper.fetch_all(
            keywords=keywords,
            min_amount_cop=user.get("min_budget"),
            max_amount_cop=user.get("max_budget"),
            countries=countries,
            days_back=7
        )

        if not contracts:
            return "📭 No encontré oportunidades con tus criterios actuales."

        # Calcular matches
        top_contracts = self.matcher.get_top_contracts(
            user=user,
            contracts=contracts,
            limit=5,
            min_score=20
        )

        if not top_contracts:
            return "📭 Encontré contratos pero ninguno coincide bien con tu perfil."

        # Enviar como reporte
        self.whatsapp.send_weekly_report(
            to=phone,
            scored_contracts=top_contracts
        )

        return f"🔍 ¡Encontré {len(top_contracts)} oportunidades! Te las envío ahora."

    def start(self):
        """Inicia el scheduler en un thread separado."""
        if self._running:
            return

        # Programar reporte semanal
        schedule.every().monday.at("09:00").do(self.send_weekly_reports)

        # v3.0: Checks de deadlines urgentes 2x/día (mañana y tarde)
        schedule.every().day.at("08:00").do(self.check_urgent_deadlines)
        schedule.every().day.at("18:00").do(self.check_urgent_deadlines)

        # Check diario al mediodía (legacy)
        schedule.every().day.at("12:00").do(self._daily_check)

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        logger.info("⏰ Scheduler v3.0 iniciado")
        logger.info(f"   - Reporte semanal: Lunes 09:00")
        logger.info(f"   - Alertas urgentes: 08:00 y 18:00")
        logger.info(f"   - Check diario: 12:00")

    def _run_loop(self):
        """Loop principal del scheduler."""
        while self._running:
            schedule.run_pending()
            time.sleep(60)  # Check cada minuto

    def _daily_check(self):
        """Check diario ligero para contratos urgentes (deadline próximo)."""
        logger.info("🔔 Ejecutando check diario de deadlines...")
        self.check_urgent_deadlines()

    def check_urgent_deadlines(self, days_threshold: int = 3) -> Dict[str, Any]:
        """
        Verifica y envía alertas de contratos con deadline urgente.

        Args:
            days_threshold: Días límite para considerar urgente (default: 3)

        Returns:
            Dict con estadísticas del proceso
        """
        logger.info(f"🚨 Verificando deadlines urgentes (< {days_threshold} días)...")

        try:
            result = self.deadline_monitor.check_urgent_deadlines(days_threshold)

            logger.info(f"✅ Alertas de deadline completadas:")
            logger.info(f"   - Contratos revisados: {result['contracts_checked']}")
            logger.info(f"   - Usuarios notificados: {result['users_notified']}")
            logger.info(f"   - Alertas enviadas: {result['alerts_sent']}")
            logger.info(f"   - Errores: {result['errors']}")

            return result

        except Exception as e:
            logger.error(f"Error en check de deadlines urgentes: {e}")
            return {
                "contracts_checked": 0,
                "users_notified": 0,
                "alerts_sent": 0,
                "errors": 1
            }

    def stop(self):
        """Detiene el scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Scheduler detenido")

    def get_available_sources(self) -> Dict[str, Any]:
        """
        Retorna información sobre las fuentes de datos disponibles.

        Returns:
            Dict con fuentes agrupadas por tipo (government, multilateral, private)
        """
        return self.scraper.get_available_sources()

    def search_specific_source(
        self,
        phone: str,
        source_key: str,
        keywords: Optional[List[str]] = None
    ) -> str:
        """
        Busca contratos en una fuente específica.

        Args:
            phone: Número de teléfono del usuario
            source_key: Clave de la fuente (secop, sam, idb, worldbank, etc.)
            keywords: Keywords opcionales (si None, usa las del perfil)

        Returns:
            Mensaje de respuesta
        """
        user = self.db.get_user_by_phone(phone)

        if not user or user.get("state") != ConversationState.ACTIVE.value:
            return "⚠️ Primero completa tu configuración escribiendo \"menu\""

        # Obtener keywords del perfil si no se especifican
        if keywords is None:
            keywords = list(self.matcher._get_user_keywords(user))

        # Buscar solo en la fuente específica
        contracts = self.scraper.fetch_all(
            keywords=keywords,
            min_amount_cop=user.get("min_budget"),
            max_amount_cop=user.get("max_budget"),
            countries=["all"],  # No filtrar por país
            days_back=7,
            include_sources=[source_key]  # Solo esta fuente
        )

        if not contracts:
            return f"📭 No encontré oportunidades en {source_key.upper()} con tus criterios."

        # Calcular matches
        top_contracts = self.matcher.get_top_contracts(
            user=user,
            contracts=contracts,
            limit=5,
            min_score=15  # Score más bajo para fuente específica
        )

        if not top_contracts:
            return f"📭 Encontré contratos en {source_key.upper()} pero ninguno coincide con tu perfil."

        # Enviar resultados
        self.whatsapp.send_weekly_report(
            to=phone,
            scored_contracts=top_contracts
        )

        return f"🔍 ¡Encontré {len(top_contracts)} oportunidades en {source_key.upper()}! Te las envío ahora."

    def trigger_manual_deadline_check(self) -> Dict[str, Any]:
        """
        Ejecuta manualmente un check de deadlines (útil para testing).

        Returns:
            Dict con estadísticas del proceso
        """
        logger.info("🔧 Check manual de deadlines iniciado...")
        return self.check_urgent_deadlines(days_threshold=3)


# =============================================================================
# SINGLETON Y HELPERS
# =============================================================================

_scheduler_instance: Optional[JobScheduler] = None


def get_scheduler(use_semantic: bool = True) -> JobScheduler:
    """
    Obtiene la instancia singleton del scheduler.

    Args:
        use_semantic: Si True, usa matching semántico

    Returns:
        Instancia de JobScheduler
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = JobScheduler(use_semantic=use_semantic)
    return _scheduler_instance
