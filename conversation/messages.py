"""
Plantillas de mensajes para el bot Jobper
Todos los mensajes de WhatsApp centralizados
"""

from __future__ import annotations

from config import Config


class Messages:
    """Plantillas de mensajes del bot."""

    # =========================================================================
    # SALUDO Y BIENVENIDA
    # =========================================================================

    WELCOME_NEW = """🚀 *¡Bienvenido a Jobper!*

Soy tu asistente para encontrar las mejores oportunidades de licitaciones gubernamentales.

Te ayudaré a configurar alertas personalizadas para que no te pierdas ningún contrato relevante para tu negocio.

📋 *Empecemos con tu perfil*

¿En qué *industria* te desarrollas o quieres monitorear contratos?

{industries}

_Responde con el número de tu elección_"""

    WELCOME_BACK = """👋 *¡Hola de nuevo!*

Tu perfil actual:
{profile_summary}

¿Qué deseas hacer?

1️⃣ Ver mis alertas pendientes
2️⃣ Modificar mis preferencias
3️⃣ Pausar/Reanudar alertas
4️⃣ Ver estadísticas
5️⃣ Ver fuentes disponibles

_Responde con el número o escribe "buscar"_"""

    # =========================================================================
    # FLUJO DE REGISTRO
    # =========================================================================

    ASK_INDUSTRY = """📊 *Selección de Industria*

¿En qué industria te desarrollas?

{industries}

_Responde con el número de tu elección_"""

    INDUSTRY_SELECTED = """✅ *Industria seleccionada:* {industry}

Ahora necesito saber más sobre lo que buscas."""

    ASK_INCLUDE = """🎯 *¿Qué tipo de contratos te interesan?*

Ya incluí las palabras clave de tu industria. ¿Hay algo *específico* que quieras agregar?

*Ejemplos:*
- "aplicaciones móviles, inteligencia artificial"
- "consultoría SAP, ERP"
- "redes, ciberseguridad"

_Escribe las palabras clave separadas por comas, o escribe "ninguna" para continuar solo con las de tu industria_"""

    ASK_EXCLUDE = """🚫 *¿Qué NO quieres ver?*

¿Hay algo que quieras *excluir* de las búsquedas?

*Ejemplos:*
- "mantenimiento, soporte técnico"
- "hardware, equipos"
- "aseo, cafetería"

_Escribe las palabras a excluir separadas por comas, o escribe "ninguna" si no quieres excluir nada_"""

    ASK_BUDGET = """💰 *Rango de Presupuesto*

¿Qué rango de presupuesto te interesa?

1️⃣ Menos de $50 millones COP
2️⃣ $50 - $200 millones COP
3️⃣ $200 - $500 millones COP
4️⃣ $500 millones - $1.000 millones COP
5️⃣ Más de $1.000 millones COP
6️⃣ Cualquier presupuesto

_Responde con el número de tu elección_"""

    ASK_COUNTRY = """🌎 *Selección de País*

¿De qué país(es) quieres recibir oportunidades?

1️⃣ 🇨🇴 Colombia (SECOP II + Ecopetrol, EPM)
2️⃣ 🇺🇸 Estados Unidos (SAM.gov)
3️⃣ 🇧🇷 Brasil (ComprasNet + Petrobras)
4️⃣ 🇲🇽 México (CompraNet)
5️⃣ 🇨🇱 Chile (ChileCompra)
6️⃣ 🇵🇪 Perú (SEACE)
7️⃣ 🇦🇷 Argentina (COMPR.AR)
8️⃣ 🌎 LATAM (todos los anteriores)
9️⃣ 🌍 Global (todos + multilaterales)

_Incluye fuentes multilaterales: BID, Banco Mundial, ONU_

_Responde con el número de tu elección_"""

    # =========================================================================
    # CONFIRMACIÓN
    # =========================================================================

    REGISTRATION_COMPLETE = """🎉 *¡Configuración Completa!*

Tu perfil de Jobper está listo:

{profile_summary}

📅 *Recibirás un reporte semanal* con las mejores oportunidades cada lunes a las 9:00 AM.

━━━━━━━━━━━━━━━━━━━━

💡 *Comandos disponibles:*
• "menu" - Ver opciones
• "pausar" - Pausar alertas
• "reanudar" - Reanudar alertas
• "perfil" - Ver/editar preferencias
• "buscar" - Buscar ahora

¡Estoy buscando oportunidades para ti! 🔍"""

    PROFILE_SUMMARY = """━━━━━━━━━━━━━━━━━━━━
📊 *Industria:* {industry}
🎯 *Incluir:* {include}
🚫 *Excluir:* {exclude}
💰 *Presupuesto:* {budget}
🌎 *Países:* {countries}
━━━━━━━━━━━━━━━━━━━━"""

    # =========================================================================
    # CONTRATOS Y ALERTAS
    # =========================================================================

    CONTRACT_ALERT = """🚀 *NUEVA OPORTUNIDAD*

📋 *{title}*

📝 {description}

🏛️ *Entidad:* {entity}
💰 *Valor:* {amount}
🌎 *País:* {country}
📅 *Fecha límite:* {deadline}

🔗 {url}

━━━━━━━━━━━━━━━━━━━━
⭐ Relevancia: {score}%
🤖 _Jobper Bot_"""

    WEEKLY_REPORT_HEADER = """📊 *REPORTE SEMANAL JOBPER*
_{date}_

Encontré *{count} oportunidades* que coinciden con tu perfil:

"""

    WEEKLY_REPORT_ITEM = """━━━━━━━━━━━━━━━━━━━━
{number}. *{title}*
💰 {amount} | {country}
⭐ Relevancia: {score}%
🔗 {url}
"""

    WEEKLY_REPORT_FOOTER = """
━━━━━━━━━━━━━━━━━━━━

💡 Responde con el *número* del contrato para ver más detalles.

_Próximo reporte: {next_date}_
🤖 _Jobper Bot_"""

    NO_CONTRACTS_FOUND = """📭 *Sin nuevas oportunidades*

Esta semana no encontré contratos que coincidan con tus criterios.

💡 *Sugerencias:*
• Amplía tu rango de presupuesto
• Agrega más palabras clave
• Considera incluir ambos países

Escribe "perfil" para ajustar tus preferencias."""

    # =========================================================================
    # ERRORES Y ESTADOS
    # =========================================================================

    INVALID_OPTION = """❌ *Opción no válida*

Por favor, responde con una de las opciones mostradas.

_Si necesitas ayuda, escribe "menu"_"""

    ERROR_GENERIC = """⚠️ *Algo salió mal*

Hubo un error procesando tu solicitud. Por favor intenta de nuevo.

_Si el problema persiste, escribe "ayuda"_"""

    PAUSED = """⏸️ *Alertas pausadas*

No recibirás más notificaciones hasta que escribas "reanudar".

_Tus preferencias se han guardado_"""

    RESUMED = """▶️ *Alertas reactivadas*

Volverás a recibir oportunidades según tu perfil.

_Próximo reporte: {next_date}_"""

    HELP = """❓ *Ayuda de Jobper v3.0*

*Comandos disponibles:*

📋 "menu" - Ver menú principal
👤 "perfil" - Ver/editar preferencias
🔍 "buscar" - Buscar oportunidades ahora
🌐 "fuentes" - Ver portales disponibles
⏸️ "pausar" - Pausar alertas
▶️ "reanudar" - Reanudar alertas
📊 "stats" - Ver estadísticas
❓ "ayuda" - Ver esta ayuda

*Buscar por país:*
🔍 "buscar secop" - Colombia (SECOP II)
🔍 "buscar sam" - Estados Unidos
🔍 "buscar brasil" - Brasil (ComprasNet)
🔍 "buscar petrobras" - Brasil (Petrobras)
🔍 "buscar mexico" - México (CompraNet)
🔍 "buscar chile" - Chile (ChileCompra)
🔍 "buscar peru" - Perú (SEACE)
🔍 "buscar argentina" - Argentina (COMPR.AR)

*Fuentes multilaterales:*
🔍 "buscar idb" - BID
🔍 "buscar worldbank" - Banco Mundial
🔍 "buscar ungm" - ONU

*¿Problemas?*
Contacta soporte en: support@jobper.co"""

    # =========================================================================
    # ALERTAS URGENTES (v3.0)
    # =========================================================================

    URGENT_ALERT_HEADER = """🚨 *ALERTA URGENTE*

{emoji} *{urgency_label}*

"""

    URGENT_ALERT_CONTRACT = """📋 *{title}*

🏛️ {entity}
💰 {amount}
⏰ *Cierra: {deadline}*

🔗 {url}
"""

    URGENT_ALERT_FOOTER = """
━━━━━━━━━━━━━━━━━━━━
⚡ Esta oportunidad tiene deadline próximo.
_Jobper Premium Alerts_"""

    # =========================================================================
    # ANÁLISIS DE IA (v3.0)
    # =========================================================================

    AI_ANALYSIS_HEADER = """🤖 *Análisis Inteligente*

"""

    AI_ANALYSIS_RECOMMENDATION = """{emoji} *{recommendation}*

📝 {summary}

⭐ *Compatibilidad:* {score}%

"""

    AI_ANALYSIS_REASONS = """*¿Por qué?*
{reasons}

"""

    AI_ANALYSIS_NEXT_STEPS = """*Próximos pasos:*
{steps}
"""

    AI_ANALYSIS_FOOTER = """
━━━━━━━━━━━━━━━━━━━━
_Análisis generado por IA - Jobper Pro_"""

    # =========================================================================
    # MÉTODOS HELPER
    # =========================================================================

    @staticmethod
    def format_industries() -> str:
        """Formatea la lista de industrias para mostrar."""
        lines = []
        for i, (key, data) in enumerate(Config.INDUSTRIES.items(), 1):
            lines.append(f"{i}️⃣ {data['emoji']} {data['name']}")
        return "\n".join(lines)

    @staticmethod
    def format_budget_range(min_val: float = None, max_val: float = None) -> str:
        """Formatea el rango de presupuesto."""
        if min_val is None and max_val is None:
            return "Cualquier presupuesto"
        if min_val and max_val:
            return f"${min_val:,.0f} - ${max_val:,.0f} COP"
        if min_val:
            return f"Más de ${min_val:,.0f} COP"
        if max_val:
            return f"Menos de ${max_val:,.0f} COP"
        return "No especificado"

    @staticmethod
    def format_countries(country: str) -> str:
        """Formatea la selección de países."""
        country_map = {
            "colombia": "🇨🇴 Colombia",
            "usa": "🇺🇸 Estados Unidos",
            "brasil": "🇧🇷 Brasil",
            "mexico": "🇲🇽 México",
            "chile": "🇨🇱 Chile",
            "peru": "🇵🇪 Perú",
            "argentina": "🇦🇷 Argentina",
            "both": "🇨🇴 Colombia + 🇺🇸 EEUU",
            "latam": "🌎 LATAM (7 países)",
            "global": "🌍 Global (todos)",
        }
        return country_map.get(country, country)

    @staticmethod
    def format_keywords(keywords: list, max_show: int = 5) -> str:
        """Formatea lista de keywords para mostrar."""
        if not keywords:
            return "Ninguna especificada"
        if len(keywords) <= max_show:
            return ", ".join(keywords)
        return ", ".join(keywords[:max_show]) + f" (+{len(keywords) - max_show} más)"

    @staticmethod
    def format_currency(amount: float, currency: str = "COP") -> str:
        """Formatea un valor monetario."""
        currency_formats = {
            "COP": ("$", " COP", "."),  # Peso colombiano
            "USD": ("$", " USD", ","),  # Dólar
            "BRL": ("R$", " BRL", "."),  # Real brasileño
            "MXN": ("$", " MXN", ","),  # Peso mexicano
            "CLP": ("$", " CLP", "."),  # Peso chileno
            "PEN": ("S/", " PEN", ","),  # Sol peruano
            "ARS": ("$", " ARS", "."),  # Peso argentino
        }

        if currency in currency_formats:
            prefix, suffix, sep = currency_formats[currency]
            formatted = f"{amount:,.0f}"
            if sep == ".":
                formatted = formatted.replace(",", ".")
            return f"{prefix}{formatted}{suffix}"

        return f"{amount:,.0f} {currency}"
