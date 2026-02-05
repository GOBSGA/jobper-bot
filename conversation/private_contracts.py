"""
Manejador de flujo conversacional para contratos privados.

Permite a usuarios publicar trabajos y encontrar contratistas
a través del chatbot de WhatsApp.

Flujo:
1. Usuario dice algo como "Tengo un contrato para pintar oficinas"
2. Bot detecta intención y extrae información inicial
3. Bot pregunta por presupuesto
4. Bot pregunta por fecha límite
5. Bot pregunta por ubicación
6. Bot confirma y publica
7. Sistema busca contratistas relevantes y los notifica
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple

from database.models import ConversationState, PrivateContractStatus
from database.manager import DatabaseManager

logger = logging.getLogger(__name__)


class PrivateContractHandler:
    """
    Manejador del flujo de publicación de contratos privados.
    """

    # Palabras clave que indican intención de publicar un contrato
    PUBLISH_TRIGGERS = [
        "tengo un contrato",
        "necesito contratar",
        "busco alguien",
        "busco a alguien",
        "necesito alguien",
        "necesito a alguien",
        "quiero contratar",
        "quiero publicar",
        "publicar trabajo",
        "publicar contrato",
        "ofrecer trabajo",
        "tengo trabajo",
        "requiero servicios",
        "necesito servicios",
    ]

    # Categorías comunes detectables
    CATEGORY_KEYWORDS = {
        "pintura": ["pintar", "pintura", "pintores", "pintor"],
        "construccion": ["construir", "construcción", "albañil", "obra", "remodelación", "remodelar"],
        "limpieza": ["limpiar", "limpieza", "aseo"],
        "electricidad": ["electricista", "eléctrico", "instalación eléctrica", "cableado"],
        "plomeria": ["plomero", "plomería", "tubería", "cañería"],
        "tecnologia": ["software", "aplicación", "app", "sistema", "programación", "desarrollo"],
        "diseño": ["diseño", "diseñador", "logo", "branding", "gráfico"],
        "marketing": ["marketing", "publicidad", "redes sociales", "seo", "ads"],
        "transporte": ["transporte", "mudanza", "envío", "logística"],
        "catering": ["catering", "comida", "evento", "banquete"],
        "seguridad": ["seguridad", "vigilancia", "guardias"],
        "mantenimiento": ["mantenimiento", "reparación", "arreglo"],
        "consultoria": ["consultoría", "asesoría", "consultor"],
        "legal": ["abogado", "legal", "jurídico", "contrato legal"],
        "contabilidad": ["contador", "contabilidad", "impuestos", "facturación"],
    }

    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()

    def detect_publish_intent(self, message: str) -> bool:
        """
        Detecta si el mensaje indica intención de publicar un contrato.

        Args:
            message: Texto del mensaje (ya en minúsculas)

        Returns:
            True si detecta intención de publicar
        """
        return any(trigger in message for trigger in self.PUBLISH_TRIGGERS)

    def extract_initial_info(self, message: str) -> Dict[str, Any]:
        """
        Extrae información inicial del mensaje del usuario.

        Args:
            message: Texto del mensaje

        Returns:
            Dict con título, categoría y descripción extraídos
        """
        info = {
            "title": "",
            "category": None,
            "description": message,
        }

        # Detectar categoría
        message_lower = message.lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in message_lower for kw in keywords):
                info["category"] = category
                break

        # Extraer título (después del trigger)
        for trigger in self.PUBLISH_TRIGGERS:
            if trigger in message_lower:
                # Tomar lo que viene después del trigger
                idx = message_lower.find(trigger) + len(trigger)
                rest = message[idx:].strip()
                # Limpiar "para" al inicio si existe
                if rest.lower().startswith("para "):
                    rest = rest[5:]
                if rest:
                    info["title"] = rest[:200]  # Limitar longitud
                break

        # Si no se extrajo título, usar el mensaje completo
        if not info["title"]:
            info["title"] = message[:200]

        return info

    def start_posting_flow(self, user: dict, message: str) -> str:
        """
        Inicia el flujo de publicación de contrato.

        Args:
            user: Dict con datos del usuario
            message: Mensaje inicial del usuario

        Returns:
            Respuesta del bot
        """
        phone = user['phone']

        # Extraer información inicial
        info = self.extract_initial_info(message)

        # Guardar en temp_data
        self.db.update_user_temp_data(phone, {
            "posting": {
                "title": info["title"],
                "category": info["category"],
                "description": info["description"],
                "step": "budget"
            }
        })

        # Cambiar estado
        self.db.update_user_state(phone, ConversationState.POSTING_AWAITING_BUDGET)

        # Formatear categoría para mostrar
        category_display = info["category"].replace("_", " ").title() if info["category"] else "General"

        return f"""📝 *¡Perfecto! Vamos a publicar tu contrato*

📋 *Trabajo:* {info["title"]}
🏷️ *Categoría:* {category_display}

💰 *¿Cuál es tu presupuesto para este trabajo?*

Puedes responder:
• Un monto fijo: "500.000" o "2 millones"
• Un rango: "entre 500.000 y 1.000.000"
• "negociable" si prefieres discutirlo

_Escribe el presupuesto o "cancelar" para salir_"""

    def handle_budget(self, user: dict, message: str) -> str:
        """
        Maneja la respuesta de presupuesto.

        Args:
            user: Dict con datos del usuario
            message: Mensaje del usuario

        Returns:
            Respuesta del bot
        """
        phone = user['phone']

        if message in ["cancelar", "cancel", "salir"]:
            return self._cancel_posting(user)

        # Parsear presupuesto
        budget_min, budget_max = self._parse_budget(message)

        # Actualizar temp_data
        temp_data = user.get('temp_data', {})
        posting = temp_data.get('posting', {})
        posting['budget_min'] = budget_min
        posting['budget_max'] = budget_max
        posting['step'] = 'deadline'

        self.db.update_user_temp_data(phone, {'posting': posting})
        self.db.update_user_state(phone, ConversationState.POSTING_AWAITING_DEADLINE)

        # Formatear presupuesto para mostrar
        if budget_min and budget_max:
            budget_display = f"${budget_min:,.0f} - ${budget_max:,.0f} COP"
        elif budget_min:
            budget_display = f"${budget_min:,.0f} COP"
        elif budget_max:
            budget_display = f"Hasta ${budget_max:,.0f} COP"
        else:
            budget_display = "Negociable"

        return f"""✅ *Presupuesto:* {budget_display}

📅 *¿Para cuándo necesitas el trabajo terminado?*

Puedes responder:
• Una fecha: "15 de febrero" o "15/02/2024"
• Un plazo: "en 2 semanas" o "1 mes"
• "flexible" si no hay fecha límite

_Escribe la fecha o plazo_"""

    def handle_deadline(self, user: dict, message: str) -> str:
        """
        Maneja la respuesta de fecha límite.

        Args:
            user: Dict con datos del usuario
            message: Mensaje del usuario

        Returns:
            Respuesta del bot
        """
        phone = user['phone']

        if message in ["cancelar", "cancel", "salir"]:
            return self._cancel_posting(user)

        # Parsear fecha
        deadline = self._parse_deadline(message)

        # Actualizar temp_data
        temp_data = user.get('temp_data', {})
        posting = temp_data.get('posting', {})
        posting['deadline'] = deadline.isoformat() if deadline else None
        posting['deadline_text'] = message
        posting['step'] = 'location'

        self.db.update_user_temp_data(phone, {'posting': posting})
        self.db.update_user_state(phone, ConversationState.POSTING_AWAITING_LOCATION)

        # Formatear fecha para mostrar
        if deadline:
            deadline_display = deadline.strftime("%d de %B de %Y")
        else:
            deadline_display = "Flexible"

        return f"""✅ *Fecha límite:* {deadline_display}

📍 *¿Dónde se realizará el trabajo?*

Puedes responder:
• Una ciudad: "Bogotá", "Medellín"
• "remoto" si es trabajo a distancia
• Tu ubicación actual

_Escribe la ubicación_"""

    def handle_location(self, user: dict, message: str) -> str:
        """
        Maneja la respuesta de ubicación.

        Args:
            user: Dict con datos del usuario
            message: Mensaje del usuario

        Returns:
            Respuesta del bot
        """
        phone = user['phone']

        if message in ["cancelar", "cancel", "salir"]:
            return self._cancel_posting(user)

        # Detectar si es remoto
        is_remote = message.lower() in ["remoto", "remote", "virtual", "online", "a distancia"]

        # Actualizar temp_data
        temp_data = user.get('temp_data', {})
        posting = temp_data.get('posting', {})
        posting['city'] = None if is_remote else message.title()
        posting['is_remote'] = is_remote
        posting['step'] = 'confirm'

        self.db.update_user_temp_data(phone, {'posting': posting})
        self.db.update_user_state(phone, ConversationState.POSTING_AWAITING_CONFIRM)

        # Generar resumen para confirmar
        return self._generate_confirmation_message(posting)

    def handle_confirmation(self, user: dict, message: str) -> str:
        """
        Maneja la confirmación de publicación.

        Args:
            user: Dict con datos del usuario
            message: Mensaje del usuario

        Returns:
            Respuesta del bot
        """
        phone = user['phone']

        if message in ["cancelar", "cancel", "salir", "no", "2"]:
            return self._cancel_posting(user)

        if message in ["si", "sí", "confirmar", "publicar", "1", "ok", "dale"]:
            return self._publish_contract(user)

        if message in ["editar", "modificar", "3"]:
            # Reiniciar el flujo
            temp_data = user.get('temp_data', {})
            posting = temp_data.get('posting', {})
            return self.start_posting_flow(user, posting.get('description', ''))

        return """❓ No entendí tu respuesta.

Por favor responde:
• *1* o *Sí* para publicar
• *2* o *No* para cancelar
• *3* o *Editar* para modificar"""

    def _parse_budget(self, message: str) -> Tuple[Optional[float], Optional[float]]:
        """Parsea el presupuesto del mensaje."""
        message = message.lower().strip()

        # Negociable
        if message in ["negociable", "a convenir", "por definir"]:
            return None, None

        # Remover puntos de miles y comas
        clean = message.replace(".", "").replace(",", "")

        # Detectar "millones"
        multiplier = 1
        if "millon" in clean or "millón" in clean:
            multiplier = 1_000_000
            clean = re.sub(r"millon(es)?", "", clean)

        # Buscar rango "entre X y Y"
        range_match = re.search(r"entre\s*(\d+)\s*y\s*(\d+)", clean)
        if range_match:
            return float(range_match.group(1)) * multiplier, float(range_match.group(2)) * multiplier

        # Buscar rango "X - Y" o "X a Y"
        range_match = re.search(r"(\d+)\s*[-a]\s*(\d+)", clean)
        if range_match:
            return float(range_match.group(1)) * multiplier, float(range_match.group(2)) * multiplier

        # Buscar número simple
        numbers = re.findall(r"\d+", clean)
        if numbers:
            amount = float(numbers[0]) * multiplier
            return amount, amount

        return None, None

    def _parse_deadline(self, message: str) -> Optional[datetime]:
        """Parsea la fecha límite del mensaje."""
        message = message.lower().strip()

        # Flexible
        if message in ["flexible", "sin fecha", "no hay fecha", "cuando se pueda"]:
            return None

        now = datetime.now()

        # "en X días/semanas/meses"
        time_match = re.search(r"en\s*(\d+)\s*(día|dias|semana|semanas|mes|meses)", message)
        if time_match:
            amount = int(time_match.group(1))
            unit = time_match.group(2)
            if "día" in unit or "dia" in unit:
                return now + timedelta(days=amount)
            elif "semana" in unit:
                return now + timedelta(weeks=amount)
            elif "mes" in unit:
                return now + timedelta(days=amount * 30)

        # Fecha específica DD/MM/YYYY o DD-MM-YYYY
        date_match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", message)
        if date_match:
            day = int(date_match.group(1))
            month = int(date_match.group(2))
            year = int(date_match.group(3))
            if year < 100:
                year += 2000
            try:
                return datetime(year, month, day)
            except ValueError:
                pass

        # "mañana", "pasado mañana"
        if "mañana" in message:
            if "pasado" in message:
                return now + timedelta(days=2)
            return now + timedelta(days=1)

        # "próxima semana", "próximo mes"
        if "próxima semana" in message or "proxima semana" in message:
            return now + timedelta(weeks=1)
        if "próximo mes" in message or "proximo mes" in message:
            return now + timedelta(days=30)

        # Default: 2 semanas si no se puede parsear
        return now + timedelta(weeks=2)

    def _generate_confirmation_message(self, posting: dict) -> str:
        """Genera mensaje de confirmación con resumen."""

        title = posting.get('title', 'Sin título')
        category = posting.get('category', 'general')
        category_display = category.replace("_", " ").title() if category else "General"

        # Presupuesto
        budget_min = posting.get('budget_min')
        budget_max = posting.get('budget_max')
        if budget_min and budget_max and budget_min != budget_max:
            budget_display = f"${budget_min:,.0f} - ${budget_max:,.0f} COP"
        elif budget_min:
            budget_display = f"${budget_min:,.0f} COP"
        else:
            budget_display = "Negociable"

        # Fecha
        deadline_str = posting.get('deadline')
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str)
                deadline_display = deadline.strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                deadline_display = posting.get('deadline_text', 'Flexible')
        else:
            deadline_display = "Flexible"

        # Ubicación
        if posting.get('is_remote'):
            location_display = "🌐 Remoto"
        else:
            location_display = f"📍 {posting.get('city', 'Por definir')}"

        return f"""📋 *Resumen de tu Contrato*

━━━━━━━━━━━━━━━━━━━━
📝 *Trabajo:* {title}
🏷️ *Categoría:* {category_display}
💰 *Presupuesto:* {budget_display}
📅 *Fecha límite:* {deadline_display}
{location_display}
━━━━━━━━━━━━━━━━━━━━

*¿Todo correcto?*

1️⃣ *Sí* - Publicar contrato
2️⃣ *No* - Cancelar
3️⃣ *Editar* - Modificar datos

_Responde con tu elección_"""

    def _publish_contract(self, user: dict) -> str:
        """Publica el contrato y notifica a contratistas."""
        phone = user['phone']
        temp_data = user.get('temp_data', {})
        posting = temp_data.get('posting', {})

        # Parsear deadline
        deadline = None
        deadline_str = posting.get('deadline')
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str)
            except (ValueError, TypeError):
                pass

        # Crear contrato en DB
        contract_id = self.db.create_private_contract(
            publisher_phone=phone,
            title=posting.get('title', ''),
            description=posting.get('description'),
            category=posting.get('category'),
            budget_min=posting.get('budget_min'),
            budget_max=posting.get('budget_max'),
            deadline=deadline,
            city=posting.get('city'),
            is_remote=posting.get('is_remote', False)
        )

        # Limpiar temp_data y volver a estado activo
        self.db.clear_user_temp_data(phone)
        self.db.update_user_state(phone, ConversationState.ACTIVE)

        # Buscar y notificar contratistas (async en background)
        self._notify_relevant_contractors(contract_id, posting)

        return f"""🎉 *¡Contrato Publicado!*

Tu trabajo ha sido publicado exitosamente.

📋 *ID:* #{contract_id}
📊 *Estado:* Activo

🔔 *¿Qué sigue?*
Estamos buscando contratistas relevantes y les notificaremos de tu oportunidad. Recibirás un mensaje cuando alguien esté interesado.

━━━━━━━━━━━━━━━━━━━━

💡 *Comandos útiles:*
• "mis contratos" - Ver tus publicaciones
• "eliminar #{contract_id}" - Cancelar este contrato

_¡Gracias por usar Jobper!_"""

    def _cancel_posting(self, user: dict) -> str:
        """Cancela el flujo de publicación."""
        phone = user['phone']
        self.db.clear_user_temp_data(phone)
        self.db.update_user_state(phone, ConversationState.ACTIVE)

        return """❌ *Publicación cancelada*

No te preocupes, puedes publicar un contrato cuando quieras.

Solo escribe algo como:
• "Tengo un contrato para..."
• "Necesito contratar..."

_Escribe "menu" para ver opciones_"""

    def _notify_relevant_contractors(self, contract_id: int, posting: dict) -> None:
        """
        Busca y notifica a contratistas relevantes.
        Se ejecuta en background después de publicar.
        """
        # Importar aquí para evitar circular imports
        try:
            from marketplace.contractor_matcher import ContractorMatcher
            matcher = ContractorMatcher(self.db)
            matcher.find_and_notify(contract_id, posting)
        except ImportError:
            logger.warning("ContractorMatcher no disponible, omitiendo notificaciones")
        except Exception as e:
            logger.error(f"Error notificando contratistas: {e}")
