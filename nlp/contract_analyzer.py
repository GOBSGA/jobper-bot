"""
Analizador de contratos con IA para Jobper Bot.

Usa Claude API para generar:
- Resumen ejecutivo del contrato
- Score de compatibilidad con perfil del usuario
- Recomendación: APLICAR / REVISAR / IGNORAR

Costo estimado: ~$0.01 por contrato analizado
Valor agregado: +$40-50/mes en pricing
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Intentar importar Anthropic
try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("anthropic no instalado. Instalar con: pip install anthropic")


@dataclass
class ContractAnalysis:
    """Resultado del análisis de un contrato."""

    # Resumen ejecutivo (2-3 oraciones)
    executive_summary: str

    # Score de compatibilidad (0-100)
    match_score: int

    # Recomendación
    recommendation: str  # "APLICAR" | "REVISAR" | "IGNORAR"

    # Razones clave (bullet points)
    key_reasons: List[str]

    # Requisitos identificados
    requirements: List[str]

    # Riesgos potenciales
    risks: List[str]

    # Próximos pasos sugeridos
    next_steps: List[str]

    # Metadata
    analysis_cost_usd: float = 0.0
    model_used: str = "claude-3-haiku-20240307"


class ContractAnalyzer:
    """
    Analizador de contratos usando Claude API.

    Genera insights accionables para cada contrato:
    - ¿Vale la pena aplicar?
    - ¿Qué necesito para aplicar?
    - ¿Cuáles son los riesgos?

    Uso:
        analyzer = ContractAnalyzer()
        analysis = analyzer.analyze(contract, user_profile)
        print(analysis.executive_summary)
        print(f"Recomendación: {analysis.recommendation}")
    """

    # Modelo a usar (Haiku es más económico para análisis masivo)
    DEFAULT_MODEL = "claude-3-haiku-20240307"

    # Costo aproximado por 1K tokens (input + output)
    COST_PER_1K_TOKENS = 0.00025  # Haiku pricing

    def __init__(self, api_key: str = None, model: str = None):
        """
        Inicializa el analizador.

        Args:
            api_key: API key de Anthropic (o usa ANTHROPIC_API_KEY env var)
            model: Modelo a usar (default: claude-3-haiku)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model or self.DEFAULT_MODEL
        self._client = None

        if not ANTHROPIC_AVAILABLE:
            logger.error("anthropic package no disponible")
        elif not self.api_key:
            logger.warning("ANTHROPIC_API_KEY no configurada")

    @property
    def client(self):
        """Lazy initialization del cliente Anthropic."""
        if self._client is None and ANTHROPIC_AVAILABLE and self.api_key:
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def analyze(self, contract: Dict[str, Any], user_profile: Dict[str, Any]) -> Optional[ContractAnalysis]:
        """
        Analiza un contrato para un perfil de usuario específico.

        Args:
            contract: Datos del contrato (title, description, amount, entity, etc.)
            user_profile: Perfil del usuario (industry, keywords, budget, etc.)

        Returns:
            ContractAnalysis con insights accionables, o None si falla
        """
        if not self.client:
            logger.warning("Cliente Anthropic no disponible, usando análisis básico")
            return self._basic_analysis(contract, user_profile)

        try:
            prompt = self._build_prompt(contract, user_profile)

            response = self.client.messages.create(
                model=self.model, max_tokens=1024, messages=[{"role": "user", "content": prompt}]
            )

            # Parsear respuesta
            analysis = self._parse_response(response.content[0].text)

            # Calcular costo aproximado
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens
            analysis.analysis_cost_usd = (total_tokens / 1000) * self.COST_PER_1K_TOKENS
            analysis.model_used = self.model

            logger.info(
                f"Contrato analizado: score={analysis.match_score}, "
                f"rec={analysis.recommendation}, cost=${analysis.analysis_cost_usd:.4f}"
            )

            return analysis

        except Exception as e:
            logger.error(f"Error analizando contrato: {e}")
            return self._basic_analysis(contract, user_profile)

    def analyze_batch(
        self, contracts: List[Dict[str, Any]], user_profile: Dict[str, Any], max_contracts: int = 20
    ) -> List[ContractAnalysis]:
        """
        Analiza múltiples contratos.

        Args:
            contracts: Lista de contratos
            user_profile: Perfil del usuario
            max_contracts: Máximo de contratos a analizar (control de costos)

        Returns:
            Lista de ContractAnalysis
        """
        results = []

        for contract in contracts[:max_contracts]:
            analysis = self.analyze(contract, user_profile)
            if analysis:
                results.append(analysis)

        # Ordenar por score descendente
        results.sort(key=lambda x: x.match_score, reverse=True)

        return results

    def _build_prompt(self, contract: Dict[str, Any], user_profile: Dict[str, Any]) -> str:
        """Construye el prompt para Claude."""

        # Extraer datos del contrato
        title = contract.get("title", "Sin título")
        description = contract.get("description", "")[:2000]  # Limitar para costos
        entity = contract.get("entity", "Desconocida")
        amount = contract.get("amount")
        currency = contract.get("currency", "COP")
        deadline = contract.get("deadline", "No especificada")
        country = contract.get("country", "")
        source = contract.get("source", "")

        # Formatear monto
        amount_str = f"{amount:,.0f} {currency}" if amount else "No especificado"

        # Extraer perfil del usuario
        industry = user_profile.get("industry", "general")
        include_kw = user_profile.get("include_keywords", [])
        exclude_kw = user_profile.get("exclude_keywords", [])
        min_budget = user_profile.get("min_budget")
        max_budget = user_profile.get("max_budget")

        # Formatear rango de presupuesto
        if min_budget and max_budget:
            budget_range = f"{min_budget:,.0f} - {max_budget:,.0f} COP"
        elif min_budget:
            budget_range = f"Más de {min_budget:,.0f} COP"
        elif max_budget:
            budget_range = f"Menos de {max_budget:,.0f} COP"
        else:
            budget_range = "Sin restricción"

        prompt = f"""Analiza este contrato gubernamental para determinar si es una buena oportunidad para el usuario.

## CONTRATO
- **Título:** {title}
- **Entidad:** {entity}
- **Valor:** {amount_str}
- **País:** {country}
- **Fuente:** {source}
- **Fecha límite:** {deadline}
- **Descripción:** {description}

## PERFIL DEL USUARIO
- **Industria:** {industry}
- **Palabras clave de interés:** {', '.join(include_kw) if include_kw else 'No especificadas'}
- **Palabras clave a evitar:** {', '.join(exclude_kw) if exclude_kw else 'Ninguna'}
- **Rango de presupuesto:** {budget_range}

## INSTRUCCIONES
Responde en formato estructurado:

RESUMEN: [2-3 oraciones describiendo la oportunidad y su relevancia]

SCORE: [número 0-100 indicando compatibilidad con el perfil]

RECOMENDACION: [APLICAR | REVISAR | IGNORAR]

RAZONES:
- [Razón 1]
- [Razón 2]
- [Razón 3]

REQUISITOS:
- [Requisito probable 1]
- [Requisito probable 2]

RIESGOS:
- [Riesgo 1]
- [Riesgo 2]

PROXIMOS_PASOS:
- [Paso 1]
- [Paso 2]

Sé conciso y accionable. El usuario necesita decidir rápidamente si vale la pena investigar más."""

        return prompt

    def _parse_response(self, response_text: str) -> ContractAnalysis:
        """Parsea la respuesta de Claude en un ContractAnalysis."""

        lines = response_text.strip().split("\n")

        # Valores por defecto
        summary = ""
        score = 50
        recommendation = "REVISAR"
        reasons = []
        requirements = []
        risks = []
        next_steps = []

        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("RESUMEN:"):
                summary = line.replace("RESUMEN:", "").strip()
                current_section = None

            elif line.startswith("SCORE:"):
                try:
                    score_str = line.replace("SCORE:", "").strip()
                    # Extraer solo números
                    score_num = "".join(c for c in score_str if c.isdigit())
                    score = int(score_num) if score_num else 50
                    score = max(0, min(100, score))  # Clamp 0-100
                except ValueError:
                    score = 50
                current_section = None

            elif line.startswith("RECOMENDACION:"):
                rec = line.replace("RECOMENDACION:", "").strip().upper()
                if "APLICAR" in rec:
                    recommendation = "APLICAR"
                elif "IGNORAR" in rec:
                    recommendation = "IGNORAR"
                else:
                    recommendation = "REVISAR"
                current_section = None

            elif line.startswith("RAZONES:"):
                current_section = "reasons"

            elif line.startswith("REQUISITOS:"):
                current_section = "requirements"

            elif line.startswith("RIESGOS:"):
                current_section = "risks"

            elif line.startswith("PROXIMOS_PASOS:"):
                current_section = "next_steps"

            elif line.startswith("- ") and current_section:
                item = line[2:].strip()
                if item:
                    if current_section == "reasons":
                        reasons.append(item)
                    elif current_section == "requirements":
                        requirements.append(item)
                    elif current_section == "risks":
                        risks.append(item)
                    elif current_section == "next_steps":
                        next_steps.append(item)

        return ContractAnalysis(
            executive_summary=summary or "Análisis no disponible",
            match_score=score,
            recommendation=recommendation,
            key_reasons=reasons or ["Sin razones específicas"],
            requirements=requirements or ["Verificar requisitos en portal oficial"],
            risks=risks or ["Evaluar según criterios propios"],
            next_steps=next_steps or ["Revisar documentos completos en el portal"],
        )

    def _basic_analysis(self, contract: Dict[str, Any], user_profile: Dict[str, Any]) -> ContractAnalysis:
        """
        Análisis básico sin IA (fallback).

        Usa heurísticas simples para generar un análisis básico
        cuando la API no está disponible.
        """
        title = contract.get("title", "").lower()
        description = contract.get("description", "").lower()
        amount = contract.get("amount")

        text = f"{title} {description}"

        # Calcular score básico
        score = 50  # Base
        reasons = []

        # Verificar keywords de inclusión
        include_kw = user_profile.get("include_keywords", [])
        matches = [kw for kw in include_kw if kw.lower() in text]
        if matches:
            score += min(30, len(matches) * 10)
            reasons.append(f"Coincide con: {', '.join(matches)}")

        # Verificar keywords de exclusión
        exclude_kw = user_profile.get("exclude_keywords", [])
        excludes = [kw for kw in exclude_kw if kw.lower() in text]
        if excludes:
            score -= min(40, len(excludes) * 15)
            reasons.append(f"Contiene términos excluidos: {', '.join(excludes)}")

        # Verificar presupuesto
        min_budget = user_profile.get("min_budget")
        max_budget = user_profile.get("max_budget")

        if amount:
            if min_budget and amount < min_budget:
                score -= 20
                reasons.append("Presupuesto por debajo del mínimo deseado")
            elif max_budget and amount > max_budget:
                score -= 10
                reasons.append("Presupuesto por encima del máximo deseado")
            else:
                score += 10
                reasons.append("Presupuesto dentro del rango deseado")

        # Clamp score
        score = max(0, min(100, score))

        # Determinar recomendación
        if score >= 70:
            recommendation = "APLICAR"
        elif score >= 40:
            recommendation = "REVISAR"
        else:
            recommendation = "IGNORAR"

        return ContractAnalysis(
            executive_summary=f"Contrato de {contract.get('entity', 'entidad desconocida')}. "
            f"{'Alta' if score >= 70 else 'Media' if score >= 40 else 'Baja'} "
            f"compatibilidad con tu perfil.",
            match_score=score,
            recommendation=recommendation,
            key_reasons=reasons or ["Análisis básico - sin IA disponible"],
            requirements=["Verificar requisitos en portal oficial"],
            risks=["Evaluar según criterios propios"],
            next_steps=["Revisar documentos completos en el portal"],
            analysis_cost_usd=0.0,
            model_used="basic_heuristics",
        )


def format_analysis_for_whatsapp(analysis: ContractAnalysis) -> str:
    """
    Formatea el análisis para enviar por WhatsApp.

    Args:
        analysis: Resultado del análisis

    Returns:
        Texto formateado para WhatsApp
    """
    # Emoji según recomendación
    rec_emoji = {"APLICAR": "✅", "REVISAR": "🔍", "IGNORAR": "⏭️"}

    # Emoji según score
    if analysis.match_score >= 80:
        score_emoji = "🔥"
    elif analysis.match_score >= 60:
        score_emoji = "⭐"
    elif analysis.match_score >= 40:
        score_emoji = "📊"
    else:
        score_emoji = "📉"

    emoji = rec_emoji.get(analysis.recommendation, "🔍")

    # Formatear razones (máximo 3)
    reasons_text = "\n".join(f"  • {r}" for r in analysis.key_reasons[:3])

    # Formatear próximos pasos (máximo 2)
    steps_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(analysis.next_steps[:2]))

    message = f"""{emoji} *{analysis.recommendation}*

📝 {analysis.executive_summary}

{score_emoji} *Compatibilidad:* {analysis.match_score}%

*¿Por qué?*
{reasons_text}

*Próximos pasos:*
{steps_text}"""

    return message
