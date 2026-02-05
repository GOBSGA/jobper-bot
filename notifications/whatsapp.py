"""
Cliente de WhatsApp usando Twilio para Jobper Bot
Incluye integración con análisis de IA para resúmenes ejecutivos
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from config import Config
from conversation.messages import Messages
from matching.engine import ScoredContract

# Lazy import para evitar circular imports y si no está disponible
_contract_analyzer = None

def _get_contract_analyzer():
    """Obtiene el analizador de contratos de forma lazy."""
    global _contract_analyzer
    if _contract_analyzer is None:
        try:
            from nlp.contract_analyzer import ContractAnalyzer
            _contract_analyzer = ContractAnalyzer()
        except ImportError:
            pass
    return _contract_analyzer

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """Cliente para enviar mensajes de WhatsApp via Twilio."""

    def __init__(self):
        self.from_number = Config.TWILIO_FROM
        self.client: Optional[Client] = None

        if Config.TWILIO_SID and Config.TWILIO_TOKEN:
            try:
                self.client = Client(Config.TWILIO_SID, Config.TWILIO_TOKEN)
                logger.info("✅ Cliente Twilio inicializado")
            except Exception as e:
                logger.error(f"❌ Error inicializando Twilio: {e}")

    def is_available(self) -> bool:
        """Verifica si el cliente está disponible."""
        return self.client is not None

    def send_message(self, to: str, body: str) -> bool:
        """
        Envía un mensaje de WhatsApp.

        Args:
            to: Número destino (formato: +573001234567)
            body: Cuerpo del mensaje

        Returns:
            True si se envió correctamente
        """
        if not self.is_available():
            logger.error("Cliente Twilio no disponible")
            return False

        try:
            # Asegurar formato WhatsApp
            from_whatsapp = f"whatsapp:{self.from_number}"
            to_whatsapp = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to

            message = self.client.messages.create(
                body=body,
                from_=from_whatsapp,
                to=to_whatsapp
            )

            logger.info(f"📱 Mensaje enviado a {to}. SID: {message.sid}")
            return True

        except TwilioRestException as e:
            logger.error(f"❌ Error Twilio: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje: {e}")
            return False

    def send_contract_alert(
        self,
        to: str,
        scored_contract: ScoredContract,
        user_profile: Dict[str, Any] = None,
        use_ai_analysis: bool = True
    ) -> bool:
        """
        Envía una alerta de contrato individual con análisis de IA opcional.

        Args:
            to: Número destino
            scored_contract: Contrato con score calculado
            user_profile: Perfil del usuario para análisis personalizado
            use_ai_analysis: Si True, incluye resumen ejecutivo de IA

        Returns:
            True si se envió correctamente
        """
        contract = scored_contract.contract

        # Intentar análisis con IA si está disponible
        ai_summary = ""
        if use_ai_analysis and user_profile:
            ai_summary = self._get_ai_analysis(contract, user_profile)

        # Formatear el mensaje base
        message = Messages.CONTRACT_ALERT.format(
            title=self._truncate(contract.title, 100),
            description=self._truncate(contract.description or "Sin descripción", 200),
            entity=contract.entity or "No especificada",
            amount=Messages.format_currency(contract.amount or 0, contract.currency),
            country=self._get_country_flag(contract.country),
            deadline=self._format_date(contract.deadline),
            url=contract.url or "No disponible",
            score=int(scored_contract.score)
        )

        # Agregar análisis de IA si existe
        if ai_summary:
            message += f"\n\n{ai_summary}"

        return self.send_message(to, message)

    def _get_ai_analysis(
        self,
        contract,
        user_profile: Dict[str, Any]
    ) -> str:
        """
        Obtiene análisis de IA para un contrato.

        Args:
            contract: Datos del contrato
            user_profile: Perfil del usuario

        Returns:
            Texto formateado del análisis o string vacío si falla
        """
        analyzer = _get_contract_analyzer()
        if not analyzer:
            return ""

        try:
            # Convertir contrato a dict si es necesario
            contract_dict = contract.to_dict() if hasattr(contract, 'to_dict') else {
                "title": contract.title,
                "description": contract.description,
                "entity": contract.entity,
                "amount": contract.amount,
                "currency": contract.currency,
                "country": contract.country,
                "deadline": str(contract.deadline) if contract.deadline else None,
                "source": contract.source,
            }

            analysis = analyzer.analyze(contract_dict, user_profile)

            if analysis:
                from nlp.contract_analyzer import format_analysis_for_whatsapp
                return format_analysis_for_whatsapp(analysis)

        except Exception as e:
            logger.warning(f"Error en análisis IA: {e}")

        return ""

    def send_weekly_report(
        self,
        to: str,
        scored_contracts: List[ScoredContract],
        next_date: str = "próximo lunes",
        user_profile: Dict[str, Any] = None,
        include_ai_analysis: bool = True
    ) -> bool:
        """
        Envía el reporte semanal con múltiples contratos.

        Args:
            to: Número destino
            scored_contracts: Lista de contratos con score
            next_date: Fecha del próximo reporte
            user_profile: Perfil del usuario para análisis IA
            include_ai_analysis: Si True, incluye análisis IA para top 3

        Returns:
            True si se envió correctamente
        """
        if not scored_contracts:
            return self.send_message(to, Messages.NO_CONTRACTS_FOUND)

        from datetime import datetime

        # Header
        message = Messages.WEEKLY_REPORT_HEADER.format(
            date=datetime.now().strftime("%d/%m/%Y"),
            count=len(scored_contracts)
        )

        # Agregar cada contrato (máximo 5 en un mensaje)
        for i, sc in enumerate(scored_contracts[:5], 1):
            contract = sc.contract

            message += Messages.WEEKLY_REPORT_ITEM.format(
                number=i,
                title=self._truncate(contract.title, 60),
                amount=Messages.format_currency(contract.amount or 0, contract.currency),
                country=self._get_country_flag(contract.country),
                score=int(sc.score),
                url=contract.url or "#"
            )

        # Footer
        message += Messages.WEEKLY_REPORT_FOOTER.format(next_date=next_date)

        success = self.send_message(to, message)

        # Enviar análisis de IA para los top 3 contratos (si está habilitado)
        if success and include_ai_analysis and user_profile:
            self._send_ai_insights(to, scored_contracts[:3], user_profile)

        # Si hay más de 5, enviar el resto en mensajes adicionales
        if success and len(scored_contracts) > 5:
            remaining = scored_contracts[5:]
            chunks = [remaining[i:i+5] for i in range(0, len(remaining), 5)]

            for chunk in chunks:
                additional = "📄 *Más oportunidades:*\n\n"
                for i, sc in enumerate(chunk, 6):
                    contract = sc.contract
                    additional += f"{i}. {self._truncate(contract.title, 50)}\n"
                    additional += f"   💰 {Messages.format_currency(contract.amount or 0, contract.currency)}\n"
                    additional += f"   🔗 {contract.url}\n\n"

                self.send_message(to, additional)

        return success

    def _send_ai_insights(
        self,
        to: str,
        scored_contracts: List[ScoredContract],
        user_profile: Dict[str, Any]
    ) -> None:
        """
        Envía análisis de IA detallado para los mejores contratos.

        Args:
            to: Número destino
            scored_contracts: Top contratos para analizar
            user_profile: Perfil del usuario
        """
        analyzer = _get_contract_analyzer()
        if not analyzer:
            return

        try:
            from nlp.contract_analyzer import format_analysis_for_whatsapp

            insights_message = "🤖 *Análisis Inteligente - Top Oportunidades*\n\n"
            has_insights = False

            for i, sc in enumerate(scored_contracts, 1):
                contract = sc.contract

                # Convertir contrato a dict
                contract_dict = contract.to_dict() if hasattr(contract, 'to_dict') else {
                    "title": contract.title,
                    "description": contract.description,
                    "entity": contract.entity,
                    "amount": contract.amount,
                    "currency": contract.currency,
                    "country": contract.country,
                    "deadline": str(contract.deadline) if contract.deadline else None,
                    "source": contract.source,
                }

                analysis = analyzer.analyze(contract_dict, user_profile)

                if analysis:
                    has_insights = True
                    insights_message += f"━━━━━━━━━━━━━━━━━━━━\n"
                    insights_message += f"*{i}. {self._truncate(contract.title, 50)}*\n\n"
                    insights_message += format_analysis_for_whatsapp(analysis)
                    insights_message += "\n\n"

            if has_insights:
                insights_message += "━━━━━━━━━━━━━━━━━━━━\n"
                insights_message += "_Análisis generado por IA - Jobper Pro_"
                self.send_message(to, insights_message)

        except Exception as e:
            logger.warning(f"Error enviando insights IA: {e}")

    def _truncate(self, text: str, max_length: int) -> str:
        """Trunca texto a longitud máxima."""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."

    def _get_country_flag(self, country: str) -> str:
        """Obtiene bandera emoji del país."""
        flags = {
            "colombia": "🇨🇴 Colombia",
            "usa": "🇺🇸 EEUU",
        }
        return flags.get(country, country)

    def _format_date(self, dt) -> str:
        """Formatea fecha para mostrar."""
        if not dt:
            return "No especificada"
        try:
            return dt.strftime("%d/%m/%Y")
        except:
            return str(dt)[:10]
