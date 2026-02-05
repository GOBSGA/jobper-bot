"""
Manejadores de conversación para Jobper Bot v3.0
Implementa la máquina de estados del flujo conversacional
Incluye soporte para fuentes multilaterales y alertas urgentes
"""
from __future__ import annotations

import logging
from typing import Optional

from config import Config
from database.models import ConversationState
from database.manager import DatabaseManager
from conversation.messages import Messages

logger = logging.getLogger(__name__)

# Lazy imports para evitar circular imports
_scheduler = None
_private_contract_handler = None


def _get_private_contract_handler():
    """Obtiene el handler de contratos privados de forma lazy."""
    global _private_contract_handler
    if _private_contract_handler is None:
        from conversation.private_contracts import PrivateContractHandler
        _private_contract_handler = PrivateContractHandler()
    return _private_contract_handler


def _get_scheduler():
    """Obtiene el scheduler de forma lazy."""
    global _scheduler
    if _scheduler is None:
        from scheduler.jobs import get_scheduler
        _scheduler = get_scheduler()
    return _scheduler


# Rangos de presupuesto predefinidos (min, max) en COP
BUDGET_RANGES = {
    "1": (None, 50_000_000),
    "2": (50_000_000, 200_000_000),
    "3": (200_000_000, 500_000_000),
    "4": (500_000_000, 1_000_000_000),
    "5": (1_000_000_000, None),
    "6": (None, None),
}


class ConversationHandler:
    """
    Manejador del flujo conversacional.
    Procesa mensajes entrantes y genera respuestas según el estado del usuario.

    Nota: user es siempre un dict, no un objeto ORM.
    """

    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()

    def handle_message(self, phone: str, message: str) -> str:
        """
        Punto de entrada principal. Procesa un mensaje y retorna la respuesta.

        Args:
            phone: Número de teléfono del usuario (formato: +573001234567)
            message: Texto del mensaje recibido

        Returns:
            str: Mensaje de respuesta para enviar al usuario
        """
        # Normalizar mensaje
        message = message.strip().lower()

        # Obtener o crear usuario (retorna dict)
        user, is_new = self.db.get_or_create_user(phone)

        logger.info(f"Mensaje de {phone} (state={user['state']}): {message[:50]}")

        # Comandos globales (funcionan en cualquier estado)
        global_response = self._handle_global_commands(user, message)
        if global_response:
            return global_response

        # Manejar según estado actual
        state = user['state']

        if state == ConversationState.NEW:
            return self._handle_new_user(user, message)
        elif state == ConversationState.AWAITING_INDUSTRY:
            return self._handle_industry_selection(user, message)
        elif state == ConversationState.AWAITING_INCLUDE:
            return self._handle_include_keywords(user, message)
        elif state == ConversationState.AWAITING_EXCLUDE:
            return self._handle_exclude_keywords(user, message)
        elif state == ConversationState.AWAITING_BUDGET:
            return self._handle_budget_selection(user, message)
        elif state == ConversationState.AWAITING_COUNTRY:
            return self._handle_country_selection(user, message)
        elif state == ConversationState.ACTIVE:
            return self._handle_active_user(user, message)
        elif state == ConversationState.PAUSED:
            return self._handle_paused_user(user, message)
        # Estados de publicación de contratos privados
        elif state == ConversationState.POSTING_AWAITING_BUDGET:
            return self._handle_posting_budget(user, message)
        elif state == ConversationState.POSTING_AWAITING_DEADLINE:
            return self._handle_posting_deadline(user, message)
        elif state == ConversationState.POSTING_AWAITING_LOCATION:
            return self._handle_posting_location(user, message)
        elif state == ConversationState.POSTING_AWAITING_CONFIRM:
            return self._handle_posting_confirm(user, message)
        else:
            return self._handle_unknown_state(user, message)

    # =========================================================================
    # COMANDOS GLOBALES
    # =========================================================================

    def _handle_global_commands(self, user: dict, message: str) -> Optional[str]:
        """Maneja comandos que funcionan en cualquier estado."""
        phone = user['phone']

        if message in ["ayuda", "help", "?"]:
            return Messages.HELP

        if message in ["menu", "inicio", "start"]:
            if user['state'] == ConversationState.ACTIVE:
                return self._get_welcome_back_message(user)
            else:
                return self._start_registration(user)

        if message in ["pausar", "pause", "stop"]:
            self.db.update_user_state(phone, ConversationState.PAUSED)
            return Messages.PAUSED

        if message in ["reanudar", "resume", "continuar"]:
            if user['industry']:  # Si tiene configuración
                self.db.update_user_state(phone, ConversationState.ACTIVE)
                return Messages.RESUMED.format(next_date="próximo lunes")
            else:
                return self._start_registration(user)

        if message in ["perfil", "profile", "config"]:
            return self._show_profile_with_edit_options(user)

        # v3.0: Comando para ver fuentes disponibles
        if message in ["fuentes", "sources", "portales"]:
            return self._show_available_sources()

        return None  # No es comando global

    # =========================================================================
    # HANDLERS POR ESTADO
    # =========================================================================

    def _handle_new_user(self, user: dict, message: str) -> str:
        """Maneja usuarios nuevos - inicia el flujo de registro."""
        return self._start_registration(user)

    def _handle_industry_selection(self, user: dict, message: str) -> str:
        """Maneja la selección de industria."""
        phone = user['phone']
        industries = list(Config.INDUSTRIES.keys())

        try:
            selection = int(message)
            if 1 <= selection <= len(industries):
                industry_key = industries[selection - 1]
                industry_data = Config.INDUSTRIES[industry_key]

                # Guardar industria
                self.db.update_user_preferences(phone, industry=industry_key)
                self.db.update_user_state(phone, ConversationState.AWAITING_INCLUDE)

                return (
                    Messages.INDUSTRY_SELECTED.format(
                        industry=f"{industry_data['emoji']} {industry_data['name']}"
                    )
                    + "\n\n"
                    + Messages.ASK_INCLUDE
                )
        except ValueError:
            pass

        # También aceptar nombre de industria
        for key, data in Config.INDUSTRIES.items():
            if key in message or data["name"].lower() in message:
                self.db.update_user_preferences(phone, industry=key)
                self.db.update_user_state(phone, ConversationState.AWAITING_INCLUDE)

                return (
                    Messages.INDUSTRY_SELECTED.format(
                        industry=f"{data['emoji']} {data['name']}"
                    )
                    + "\n\n"
                    + Messages.ASK_INCLUDE
                )

        return Messages.INVALID_OPTION + "\n\n" + Messages.ASK_INDUSTRY.format(
            industries=Messages.format_industries()
        )

    def _handle_include_keywords(self, user: dict, message: str) -> str:
        """Maneja la entrada de palabras clave a incluir."""
        phone = user['phone']

        if message in ["ninguna", "ninguno", "no", "skip", "omitir"]:
            keywords = []
        else:
            # Parsear keywords separadas por comas
            keywords = [kw.strip() for kw in message.split(",") if kw.strip()]

        self.db.update_user_preferences(phone, include_keywords=keywords)
        self.db.update_user_state(phone, ConversationState.AWAITING_EXCLUDE)

        return Messages.ASK_EXCLUDE

    def _handle_exclude_keywords(self, user: dict, message: str) -> str:
        """Maneja la entrada de palabras clave a excluir."""
        phone = user['phone']

        if message in ["ninguna", "ninguno", "no", "skip", "omitir"]:
            keywords = []
        else:
            keywords = [kw.strip() for kw in message.split(",") if kw.strip()]

        self.db.update_user_preferences(phone, exclude_keywords=keywords)
        self.db.update_user_state(phone, ConversationState.AWAITING_BUDGET)

        return Messages.ASK_BUDGET

    def _handle_budget_selection(self, user: dict, message: str) -> str:
        """Maneja la selección de rango de presupuesto."""
        phone = user['phone']

        if message in BUDGET_RANGES:
            min_budget, max_budget = BUDGET_RANGES[message]

            self.db.update_user_preferences(
                phone,
                min_budget=min_budget,
                max_budget=max_budget
            )
            self.db.update_user_state(phone, ConversationState.AWAITING_COUNTRY)

            return Messages.ASK_COUNTRY

        return Messages.INVALID_OPTION + "\n\n" + Messages.ASK_BUDGET

    def _handle_country_selection(self, user: dict, message: str) -> str:
        """Maneja la selección de país."""
        phone = user['phone']

        # Mapeo de opciones a países
        country_map = {
            # Por número
            "1": "colombia",
            "2": "usa",
            "3": "brasil",
            "4": "mexico",
            "5": "chile",
            "6": "peru",
            "7": "argentina",
            "8": "latam",
            "9": "global",
            # Por nombre
            "colombia": "colombia",
            "usa": "usa",
            "eeuu": "usa",
            "estados unidos": "usa",
            "brasil": "brasil",
            "brazil": "brasil",
            "mexico": "mexico",
            "méxico": "mexico",
            "chile": "chile",
            "peru": "peru",
            "perú": "peru",
            "argentina": "argentina",
            "latam": "latam",
            "latinoamerica": "latam",
            "global": "global",
            "todos": "global",
            "all": "global",
            # Legacy
            "ambos": "latam",
            "both": "latam",
        }

        country = country_map.get(message)

        if country:
            self.db.update_user_preferences(phone, countries=country)
            self.db.update_user_state(phone, ConversationState.ACTIVE)
            self.db.clear_user_temp_data(phone)

            # Obtener usuario actualizado para el resumen
            updated_user = self.db.get_user_by_phone(phone)

            return Messages.REGISTRATION_COMPLETE.format(
                profile_summary=self._format_profile_summary(updated_user)
            )

        return Messages.INVALID_OPTION + "\n\n" + Messages.ASK_COUNTRY

    def _handle_active_user(self, user: dict, message: str) -> str:
        """Maneja usuarios activos (ya registrados)."""
        phone = user['phone']

        # Detectar intención de publicar contrato privado
        private_handler = _get_private_contract_handler()
        if private_handler.detect_publish_intent(message):
            return private_handler.start_posting_flow(user, message)

        # Comando para ver contratos publicados
        if message in ["mis contratos", "mis publicaciones", "my contracts"]:
            return self._show_user_contracts(user)

        # Comando para buscar ahora
        if message in ["buscar", "search", "buscar ahora"]:
            scheduler = _get_scheduler()
            result = scheduler.search_now_for_user(phone)
            return result

        # v3.0: Buscar en fuente específica
        if message.startswith("buscar "):
            source_key = message.replace("buscar ", "").strip()
            valid_sources = [
                # Gobierno
                "secop", "sam",
                # LATAM
                "brasil", "mexico", "chile", "peru", "argentina",
                # Empresas públicas
                "petrobras", "ecopetrol", "epm",
                # Multilaterales
                "idb", "worldbank", "ungm",
            ]
            if source_key in valid_sources:
                scheduler = _get_scheduler()
                return scheduler.search_specific_source(phone, source_key)
            else:
                return f"⚠️ Fuente '{source_key}' no reconocida.\n\nEscribe *fuentes* para ver las disponibles."

        # Menú de opciones
        if message in ["1", "alertas", "pendientes"]:
            return "📋 Consultando alertas pendientes..."

        if message in ["2", "modificar", "editar", "preferencias"]:
            return self._start_registration(user)

        if message in ["3"]:
            current_state = user['state']
            if current_state == ConversationState.ACTIVE:
                self.db.update_user_state(phone, ConversationState.PAUSED)
                return Messages.PAUSED
            else:
                self.db.update_user_state(phone, ConversationState.ACTIVE)
                return Messages.RESUMED.format(next_date="próximo lunes")

        if message in ["4", "stats", "estadisticas"]:
            stats = self.db.get_stats()
            return f"""📊 *Estadísticas de Jobper*

👥 Usuarios activos: {stats['active_users']}
📄 Contratos indexados: {stats['total_contracts']}
📨 Alertas enviadas: {stats['total_notifications_sent']}

_Tu próximo reporte: lunes 9:00 AM_"""

        # v3.0: Ver fuentes
        if message in ["5", "fuentes"]:
            return self._show_available_sources()

        return self._get_welcome_back_message(user)

    def _handle_paused_user(self, user: dict, message: str) -> str:
        """Maneja usuarios con alertas pausadas."""
        return """⏸️ *Tus alertas están pausadas*

Escribe "reanudar" para volver a recibir oportunidades.

_Tu perfil sigue guardado_"""

    def _handle_unknown_state(self, user: dict, message: str) -> str:
        """Maneja estados desconocidos - reinicia el flujo."""
        logger.warning(f"Estado desconocido para {user['phone']}: {user['state']}")
        return self._start_registration(user)

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _start_registration(self, user: dict) -> str:
        """Inicia o reinicia el flujo de registro."""
        self.db.update_user_state(user['phone'], ConversationState.AWAITING_INDUSTRY)

        return Messages.WELCOME_NEW.format(
            industries=Messages.format_industries()
        )

    def _get_welcome_back_message(self, user: dict) -> str:
        """Genera mensaje de bienvenida para usuario existente."""
        return Messages.WELCOME_BACK.format(
            profile_summary=self._format_profile_summary(user)
        )

    def _format_profile_summary(self, user: dict) -> str:
        """Formatea el resumen del perfil del usuario."""
        industry_name = "No configurada"
        industry = user.get('industry')
        if industry and industry in Config.INDUSTRIES:
            data = Config.INDUSTRIES[industry]
            industry_name = f"{data['emoji']} {data['name']}"

        # Manejar countries que puede ser enum o string
        countries = user.get('countries')
        if countries:
            countries_val = countries.value if hasattr(countries, 'value') else str(countries)
        else:
            countries_val = "both"

        return Messages.PROFILE_SUMMARY.format(
            industry=industry_name,
            include=Messages.format_keywords(user.get('include_keywords') or []),
            exclude=Messages.format_keywords(user.get('exclude_keywords') or []),
            budget=Messages.format_budget_range(user.get('min_budget'), user.get('max_budget')),
            countries=Messages.format_countries(countries_val)
        )

    def _show_profile_with_edit_options(self, user: dict) -> str:
        """Muestra el perfil con opciones de edición."""
        summary = self._format_profile_summary(user)

        return f"""👤 *Tu Perfil Jobper*

{summary}

*¿Qué deseas modificar?*

1️⃣ Cambiar industria
2️⃣ Editar palabras clave
3️⃣ Ajustar presupuesto
4️⃣ Cambiar países
5️⃣ Volver al menú

_Responde con el número de tu elección_"""

    # =========================================================================
    # HANDLERS PARA CONTRATOS PRIVADOS
    # =========================================================================

    def _handle_posting_budget(self, user: dict, message: str) -> str:
        """Maneja la entrada de presupuesto para contrato privado."""
        handler = _get_private_contract_handler()
        return handler.handle_budget(user, message)

    def _handle_posting_deadline(self, user: dict, message: str) -> str:
        """Maneja la entrada de fecha límite para contrato privado."""
        handler = _get_private_contract_handler()
        return handler.handle_deadline(user, message)

    def _handle_posting_location(self, user: dict, message: str) -> str:
        """Maneja la entrada de ubicación para contrato privado."""
        handler = _get_private_contract_handler()
        return handler.handle_location(user, message)

    def _handle_posting_confirm(self, user: dict, message: str) -> str:
        """Maneja la confirmación de publicación de contrato privado."""
        handler = _get_private_contract_handler()
        return handler.handle_confirmation(user, message)

    def _show_user_contracts(self, user: dict) -> str:
        """Muestra los contratos privados publicados por el usuario."""
        contracts = self.db.get_user_private_contracts(user['phone'])

        if not contracts:
            return """📋 *Mis Contratos Publicados*

No tienes contratos publicados aún.

💡 Para publicar un trabajo, escribe algo como:
• "Tengo un contrato para pintar oficinas"
• "Necesito contratar un desarrollador"
• "Busco alguien para diseño gráfico"

_¡Es fácil y rápido!_"""

        msg = f"""📋 *Mis Contratos Publicados* ({len(contracts)})

"""
        for i, c in enumerate(contracts[:10], 1):
            status_emoji = {
                "active": "🟢",
                "in_progress": "🔵",
                "completed": "✅",
                "cancelled": "❌",
            }.get(c['status'], "⚪")

            budget_str = ""
            if c['budget_min'] and c['budget_max']:
                budget_str = f"${c['budget_min']:,.0f}-${c['budget_max']:,.0f}"
            elif c['budget_min']:
                budget_str = f"${c['budget_min']:,.0f}"
            else:
                budget_str = "Negociable"

            msg += f"""{status_emoji} *#{c['id']}* {c['title'][:40]}
   💰 {budget_str} | 📍 {c.get('city') or 'Remoto'}

"""

        msg += """━━━━━━━━━━━━━━━━━━━━

💡 *Comandos:*
• "eliminar #ID" - Cancelar contrato
• "ver #ID" - Ver detalles y aplicantes"""

        return msg

    def _show_available_sources(self) -> str:
        """Muestra las fuentes de datos disponibles (v3.0)."""
        scheduler = _get_scheduler()
        sources = scheduler.get_available_sources()

        country_flags = {
            "colombia": "🇨🇴",
            "usa": "🇺🇸",
            "brasil": "🇧🇷",
            "mexico": "🇲🇽",
            "chile": "🇨🇱",
            "peru": "🇵🇪",
            "argentina": "🇦🇷",
        }

        msg = """🌐 *Fuentes de Datos Disponibles*

*Gobierno:*"""

        # Fuentes gubernamentales
        for _, info in sources.get("government", {}).items():
            status = "✅" if info.get("available", False) else "❌"
            flag = country_flags.get(info['country'], "🏛️")
            msg += f"\n  {status} {flag} *{info['name']}*"

        # Fuentes LATAM
        if sources.get("latam"):
            msg += "\n\n*LATAM:*"
            for _, info in sources["latam"].items():
                flag = country_flags.get(info['country'], "🌎")
                msg += f"\n  ✅ {flag} *{info['name']}*"

        # Fuentes multilaterales
        if sources.get("multilateral"):
            msg += "\n\n*Multilaterales:*"
            for _, info in sources["multilateral"].items():
                msg += f"\n  ✅ 🌍 *{info['name']}*"

        # Fuentes privadas
        if sources.get("private"):
            msg += "\n\n*Sector Privado (Colombia):*"
            for _, info in sources["private"].items():
                msg += f"\n  ✅ 🏢 *{info['name']}*"

        msg += """

*Buscar por país:*
"buscar mexico", "buscar chile", "buscar peru", "buscar argentina"

*Buscar por fuente:*
"buscar secop", "buscar sam", "buscar idb", etc.

_Todas las fuentes se incluyen en tu reporte semanal_"""

        return msg
