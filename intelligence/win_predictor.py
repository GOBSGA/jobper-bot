"""
Win Predictor
Sistema de predicción de probabilidad de ganar contratos.

Utiliza factores históricos y características del contrato/usuario
para estimar la probabilidad de éxito en una licitación.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class WinFactor:
    """Factor que influye en la probabilidad de ganar."""

    name: str
    weight: float  # Peso en el modelo
    value: float  # Valor calculado (0-1)
    impact: str  # "positive", "negative", "neutral"
    explanation: str
    recommendations: List[str] = field(default_factory=list)


@dataclass
class WinPrediction:
    """Predicción de probabilidad de ganar."""

    # Probabilidad calculada
    win_probability: float  # 0-100

    # Nivel de confianza
    confidence: str  # "low", "medium", "high"
    confidence_score: float  # 0-100

    # Factores analizados
    factors: List[WinFactor] = field(default_factory=list)

    # Factores principales
    top_positive_factors: List[str] = field(default_factory=list)
    top_negative_factors: List[str] = field(default_factory=list)

    # Recomendaciones para mejorar
    improvement_actions: List[str] = field(default_factory=list)

    # Comparación con competencia
    competitive_position: str = "moderate"  # "strong", "moderate", "weak"

    # Escenarios
    best_case: float = 0.0
    worst_case: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return {
            "win_probability": round(self.win_probability, 1),
            "confidence": self.confidence,
            "confidence_score": round(self.confidence_score, 1),
            "competitive_position": self.competitive_position,
            "factors": [{"name": f.name, "impact": f.impact, "explanation": f.explanation} for f in self.factors],
            "top_positive_factors": self.top_positive_factors,
            "top_negative_factors": self.top_negative_factors,
            "improvement_actions": self.improvement_actions,
            "scenarios": {
                "best_case": round(self.best_case, 1),
                "expected": round(self.win_probability, 1),
                "worst_case": round(self.worst_case, 1),
            },
        }


class WinPredictor:
    """
    Predictor de probabilidad de éxito en licitaciones.

    Analiza múltiples factores para estimar la probabilidad
    de que un usuario gane un contrato específico.
    """

    # Pesos de factores (deben sumar aproximadamente 1.0)
    FACTOR_WEIGHTS = {
        "experience_match": 0.20,  # Experiencia relevante
        "financial_capacity": 0.15,  # Capacidad financiera
        "technical_fit": 0.15,  # Fit técnico
        "competition_level": 0.12,  # Nivel de competencia
        "requirements_met": 0.12,  # Requisitos cumplidos
        "timing": 0.08,  # Tiempo de preparación
        "entity_relationship": 0.08,  # Relación con entidad
        "price_competitiveness": 0.05,  # Competitividad precio
        "proposal_quality": 0.05,  # Calidad estimada propuesta
    }

    # Probabilidades base por tipo de contratación
    BASE_PROBABILITIES = {
        "minima_cuantia": 0.25,  # Muchos competidores
        "seleccion_abreviada": 0.15,  # Competencia media
        "licitacion_publica": 0.08,  # Alta competencia
        "contratacion_directa": 0.40,  # Invitación directa
        "concurso_meritos": 0.12,  # Evalúa calidad
        "default": 0.12,  # Por defecto
    }

    def __init__(self):
        """Inicializa el predictor."""
        logger.info("WinPredictor inicializado")

    def predict(
        self,
        contract: Dict[str, Any],
        user_profile: Dict[str, Any],
        user_history: Optional[List[Dict[str, Any]]] = None,
    ) -> WinPrediction:
        """
        Predice la probabilidad de ganar un contrato.

        Args:
            contract: Datos del contrato
            user_profile: Perfil del usuario
            user_history: Historial de contratos del usuario (opcional)

        Returns:
            WinPrediction con probabilidad y análisis
        """
        # Inicializar predicción
        prediction = WinPrediction(
            win_probability=0, confidence="medium", confidence_score=50, competitive_position="moderate"
        )

        # Calcular cada factor
        factors = []

        factors.append(self._evaluate_experience_match(contract, user_profile, user_history))
        factors.append(self._evaluate_financial_capacity(contract, user_profile))
        factors.append(self._evaluate_technical_fit(contract, user_profile))
        factors.append(self._evaluate_competition_level(contract))
        factors.append(self._evaluate_requirements_met(contract, user_profile))
        factors.append(self._evaluate_timing(contract))
        factors.append(self._evaluate_entity_relationship(contract, user_history))
        factors.append(self._evaluate_price_competitiveness(contract, user_profile))
        factors.append(self._evaluate_proposal_quality(contract, user_profile))

        prediction.factors = factors

        # Calcular probabilidad base
        base_prob = self._get_base_probability(contract)

        # Calcular probabilidad ajustada
        weighted_sum = sum(f.value * f.weight for f in factors)
        multiplier = 1 + (weighted_sum - 0.5) * 2  # Convertir a multiplicador

        prediction.win_probability = max(5, min(80, base_prob * 100 * multiplier))

        # Calcular confianza
        prediction.confidence, prediction.confidence_score = self._calculate_confidence(contract, user_profile, factors)

        # Extraer factores principales
        prediction.top_positive_factors = [
            f.name
            for f in sorted(factors, key=lambda x: x.value * x.weight, reverse=True)[:3]
            if f.impact == "positive"
        ]

        prediction.top_negative_factors = [
            f.name
            for f in sorted(factors, key=lambda x: (1 - x.value) * x.weight, reverse=True)[:3]
            if f.impact == "negative"
        ]

        # Generar recomendaciones
        prediction.improvement_actions = self._generate_improvement_actions(factors)

        # Determinar posición competitiva
        prediction.competitive_position = self._determine_competitive_position(prediction.win_probability)

        # Calcular escenarios
        prediction.best_case = min(95, prediction.win_probability * 1.5)
        prediction.worst_case = max(2, prediction.win_probability * 0.5)

        return prediction

    def predict_batch(
        self,
        contracts: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        user_history: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Tuple[Dict[str, Any], WinPrediction]]:
        """
        Predice probabilidades para múltiples contratos.

        Returns:
            Lista de (contrato, predicción) ordenada por probabilidad
        """
        results = []

        for contract in contracts:
            prediction = self.predict(contract, user_profile, user_history)
            results.append((contract, prediction))

        # Ordenar por probabilidad descendente
        results.sort(key=lambda x: x[1].win_probability, reverse=True)

        return results

    # =========================================================================
    # Evaluadores de factores
    # =========================================================================

    def _evaluate_experience_match(
        self, contract: Dict[str, Any], user_profile: Dict[str, Any], user_history: Optional[List[Dict[str, Any]]]
    ) -> WinFactor:
        """Evalúa match de experiencia."""
        text = self._get_contract_text(contract).lower()
        value = 0.5  # Base neutral

        recommendations = []

        # Buscar requisitos de experiencia
        import re

        exp_match = re.search(r"(\d+)\s*a[ñn]os?\s*(?:de\s+)?experiencia", text)

        if exp_match:
            required_years = int(exp_match.group(1))

            # Estimar años de experiencia del usuario (heurística)
            # Esto debería venir del perfil real
            user_years = user_profile.get("years_experience", 5)

            if user_years >= required_years:
                value = 0.8
                explanation = f"Cumples {user_years} años vs {required_years} requeridos"
            elif user_years >= required_years * 0.7:
                value = 0.5
                explanation = f"Experiencia cercana: {user_years} años vs {required_years} requeridos"
                recommendations.append("Considerar alianza con empresa más experimentada")
            else:
                value = 0.2
                explanation = f"Experiencia insuficiente: {user_years} años vs {required_years} requeridos"
                recommendations.append("Este contrato requiere más experiencia de la que tienes")
        else:
            value = 0.6
            explanation = "Sin requisito específico de años de experiencia"

        # Bonus por historial similar
        if user_history:
            similar = sum(1 for h in user_history if self._contracts_similar(h, contract))
            if similar > 0:
                value = min(1.0, value + 0.1 * similar)
                explanation += f" + {similar} contratos similares previos"

        return WinFactor(
            name="Experiencia Relevante",
            weight=self.FACTOR_WEIGHTS["experience_match"],
            value=value,
            impact="positive" if value > 0.5 else "negative" if value < 0.5 else "neutral",
            explanation=explanation,
            recommendations=recommendations,
        )

    def _evaluate_financial_capacity(self, contract: Dict[str, Any], user_profile: Dict[str, Any]) -> WinFactor:
        """Evalúa capacidad financiera."""
        amount = contract.get("amount", 0) or 0
        max_budget = user_profile.get("max_budget") or float("inf")

        recommendations = []

        if amount == 0:
            value = 0.5
            explanation = "Monto no especificado - asumiendo capacidad neutral"
        elif amount <= max_budget:
            # Calcular qué tan cómodo es el monto
            ratio = amount / max_budget if max_budget else 0
            if ratio < 0.5:
                value = 0.9
                explanation = "Monto muy dentro de tu capacidad financiera"
            elif ratio < 0.8:
                value = 0.7
                explanation = "Monto dentro de tu capacidad financiera"
            else:
                value = 0.5
                explanation = "Monto al límite de tu capacidad financiera"
                recommendations.append("Considerar consorcio para compartir riesgo financiero")
        else:
            # Monto excede capacidad
            over_ratio = amount / max_budget if max_budget else 2
            if over_ratio < 1.5:
                value = 0.3
                explanation = f"Monto {over_ratio:.1f}x tu capacidad - considerar consorcio"
                recommendations.append("Buscar socio financiero o consorcio")
            else:
                value = 0.1
                explanation = f"Monto significativamente sobre tu capacidad ({over_ratio:.1f}x)"
                recommendations.append("Este contrato requiere mayor capacidad financiera")

        return WinFactor(
            name="Capacidad Financiera",
            weight=self.FACTOR_WEIGHTS["financial_capacity"],
            value=value,
            impact="positive" if value > 0.5 else "negative" if value < 0.5 else "neutral",
            explanation=explanation,
            recommendations=recommendations,
        )

    def _evaluate_technical_fit(self, contract: Dict[str, Any], user_profile: Dict[str, Any]) -> WinFactor:
        """Evalúa fit técnico entre usuario y contrato."""
        text = self._get_contract_text(contract).lower()
        user_industry = user_profile.get("industry", "")
        user_keywords = [kw.lower() for kw in user_profile.get("include_keywords", [])]

        value = 0.5
        matches = []
        recommendations = []

        # Match de industria
        industry_match = self._industry_matches_contract(user_industry, text)
        if industry_match:
            value += 0.2
            matches.append(f"industria {user_industry}")

        # Match de keywords
        keyword_matches = sum(1 for kw in user_keywords if kw in text)
        if keyword_matches > 0:
            keyword_bonus = min(0.3, keyword_matches * 0.1)
            value += keyword_bonus
            matches.append(f"{keyword_matches} palabras clave")

        # Tecnologías específicas (si aplica IT)
        if user_industry == "tecnologia":
            tech_keywords = ["python", "java", "aws", "azure", ".net", "cloud"]
            tech_matches = sum(1 for t in tech_keywords if t in text)
            if tech_matches > 0:
                value = min(1.0, value + 0.1)
                matches.append(f"{tech_matches} tecnologías")

        if matches:
            explanation = f"Match técnico: {', '.join(matches)}"
        else:
            explanation = "Sin match técnico específico con tu perfil"
            recommendations.append("Considerar si tienes las capacidades técnicas requeridas")

        return WinFactor(
            name="Fit Técnico",
            weight=self.FACTOR_WEIGHTS["technical_fit"],
            value=min(1.0, value),
            impact="positive" if value > 0.5 else "negative" if value < 0.5 else "neutral",
            explanation=explanation,
            recommendations=recommendations,
        )

    def _evaluate_competition_level(self, contract: Dict[str, Any]) -> WinFactor:
        """Evalúa nivel de competencia esperado."""
        amount = contract.get("amount", 0) or 0
        text = self._get_contract_text(contract).lower()

        # Factores que reducen competencia
        low_competition_signals = [
            "consorcio",
            "experiencia específica",
            "certificación",
            "iso",
            "cmmi",
            "presencia local",
        ]

        barriers = sum(1 for s in low_competition_signals if s in text)

        # Estimar competencia
        if amount > 5_000_000_000:  # > 5B
            base_competitors = 3
        elif amount > 1_000_000_000:  # > 1B
            base_competitors = 5
        elif amount > 100_000_000:  # > 100M
            base_competitors = 10
        elif amount > 50_000_000:  # > 50M
            base_competitors = 15
        else:
            base_competitors = 25

        # Ajustar por barreras
        estimated_competitors = max(1, base_competitors - barriers * 2)

        # Convertir a valor (menos competidores = mayor valor)
        if estimated_competitors <= 3:
            value = 0.9
            explanation = f"Competencia baja estimada (~{estimated_competitors} competidores)"
        elif estimated_competitors <= 7:
            value = 0.7
            explanation = f"Competencia moderada (~{estimated_competitors} competidores)"
        elif estimated_competitors <= 15:
            value = 0.4
            explanation = f"Competencia alta (~{estimated_competitors} competidores)"
        else:
            value = 0.2
            explanation = f"Competencia muy alta (~{estimated_competitors}+ competidores)"

        recommendations = []
        if value < 0.5:
            recommendations.append("Enfocar en diferenciación técnica o precio competitivo")

        return WinFactor(
            name="Nivel de Competencia",
            weight=self.FACTOR_WEIGHTS["competition_level"],
            value=value,
            impact="positive" if value > 0.5 else "negative",
            explanation=explanation,
            recommendations=recommendations,
        )

    def _evaluate_requirements_met(self, contract: Dict[str, Any], user_profile: Dict[str, Any]) -> WinFactor:
        """Evalúa qué porcentaje de requisitos se cumplen."""
        text = self._get_contract_text(contract).lower()

        # Requisitos comunes a verificar
        requirements = {
            "certificacion": ("iso", "certificación", "certificado"),
            "experiencia": ("años de experiencia", "experiencia mínima"),
            "financiero": ("capacidad financiera", "patrimonio"),
            "local": ("presencia local", "oficina en"),
        }

        met = 0
        total = 0
        unmet = []

        for req_name, patterns in requirements.items():
            if any(p in text for p in patterns):
                total += 1
                # Heurística: asumimos que el usuario cumple requisitos básicos
                # En producción, esto debería verificarse contra el perfil real
                if req_name in ["certificacion"]:
                    met += 0.5  # Parcial
                    unmet.append(req_name)
                else:
                    met += 1

        if total == 0:
            value = 0.7
            explanation = "Sin requisitos específicos identificados"
        else:
            value = met / total
            if value >= 0.8:
                explanation = f"Cumples la mayoría de requisitos ({met:.0f}/{total})"
            elif value >= 0.5:
                explanation = f"Cumples parcialmente los requisitos ({met:.0f}/{total})"
            else:
                explanation = f"Varios requisitos no cumplidos ({met:.0f}/{total})"

        recommendations = []
        if unmet:
            recommendations.append(f"Verificar cumplimiento de: {', '.join(unmet)}")

        return WinFactor(
            name="Requisitos Cumplidos",
            weight=self.FACTOR_WEIGHTS["requirements_met"],
            value=value,
            impact="positive" if value > 0.5 else "negative",
            explanation=explanation,
            recommendations=recommendations,
        )

    def _evaluate_timing(self, contract: Dict[str, Any]) -> WinFactor:
        """Evalúa si hay tiempo suficiente para preparar propuesta."""
        deadline = contract.get("deadline")
        amount = contract.get("amount", 0) or 0

        # Tiempo de preparación recomendado según monto
        if amount > 1_000_000_000:
            recommended_days = 21
        elif amount > 100_000_000:
            recommended_days = 14
        else:
            recommended_days = 7

        if not deadline:
            value = 0.5
            explanation = "Sin deadline especificado"
            recommendations = []
        else:
            try:
                if isinstance(deadline, str):
                    deadline = datetime.fromisoformat(deadline.replace("Z", "+00:00"))

                days_left = (deadline - datetime.now()).days

                if days_left < 0:
                    value = 0
                    explanation = "Deadline vencido"
                    recommendations = ["Este contrato ya cerró"]
                elif days_left >= recommended_days:
                    value = 0.9
                    explanation = f"{days_left} días disponibles - tiempo suficiente"
                    recommendations = []
                elif days_left >= recommended_days * 0.5:
                    value = 0.5
                    explanation = f"{days_left} días - tiempo ajustado"
                    recommendations = ["Iniciar preparación inmediatamente"]
                else:
                    value = 0.2
                    explanation = f"Solo {days_left} días - muy poco tiempo"
                    recommendations = ["Evaluar si es realista participar con tan poco tiempo"]
            except (ValueError, TypeError):
                value = 0.5
                explanation = "Error procesando deadline"
                recommendations = []

        return WinFactor(
            name="Tiempo de Preparación",
            weight=self.FACTOR_WEIGHTS["timing"],
            value=value,
            impact="positive" if value > 0.5 else "negative" if value < 0.5 else "neutral",
            explanation=explanation,
            recommendations=recommendations,
        )

    def _evaluate_entity_relationship(
        self, contract: Dict[str, Any], user_history: Optional[List[Dict[str, Any]]]
    ) -> WinFactor:
        """Evalúa relación previa con la entidad contratante."""
        entity = (contract.get("entity", "") or "").lower()

        if not user_history or not entity:
            value = 0.5
            explanation = "Sin historial con esta entidad"
            recommendations = ["Construir relación con esta entidad para futuras oportunidades"]
        else:
            # Buscar contratos previos con la entidad
            previous = sum(1 for h in user_history if entity in (h.get("entity", "") or "").lower())

            if previous >= 3:
                value = 0.9
                explanation = f"Relación establecida: {previous} contratos previos con esta entidad"
                recommendations = []
            elif previous >= 1:
                value = 0.7
                explanation = f"Relación existente: {previous} contrato(s) previo(s)"
                recommendations = ["Aprovechar la relación existente"]
            else:
                value = 0.5
                explanation = "Sin historial con esta entidad específica"
                recommendations = ["Primera vez con esta entidad - propuesta impecable es clave"]

        return WinFactor(
            name="Relación con Entidad",
            weight=self.FACTOR_WEIGHTS["entity_relationship"],
            value=value,
            impact="positive" if value > 0.5 else "neutral",
            explanation=explanation,
            recommendations=recommendations,
        )

    def _evaluate_price_competitiveness(self, contract: Dict[str, Any], user_profile: Dict[str, Any]) -> WinFactor:
        """Evalúa competitividad de precio estimada."""
        # Sin información de precios históricos, usamos heurísticas

        text = self._get_contract_text(contract).lower()

        # Contratos donde precio es más importante
        price_sensitive = any(
            kw in text for kw in ["menor precio", "mejor precio", "precio más bajo", "subasta", "mínima cuantía"]
        )

        # Contratos donde calidad es más importante
        quality_focused = any(
            kw in text
            for kw in ["concurso de méritos", "mejor propuesta", "evaluación técnica", "calidad", "experiencia"]
        )

        if price_sensitive:
            value = 0.4
            explanation = "Contrato sensible a precio - competencia por precio es clave"
            recommendations = ["Optimizar costos para ser competitivo en precio"]
        elif quality_focused:
            value = 0.6
            explanation = "Contrato enfocado en calidad - propuesta técnica es clave"
            recommendations = ["Enfocar en propuesta técnica superior"]
        else:
            value = 0.5
            explanation = "Balance precio-calidad típico"
            recommendations = []

        return WinFactor(
            name="Competitividad de Precio",
            weight=self.FACTOR_WEIGHTS["price_competitiveness"],
            value=value,
            impact="neutral",
            explanation=explanation,
            recommendations=recommendations,
        )

    def _evaluate_proposal_quality(self, contract: Dict[str, Any], user_profile: Dict[str, Any]) -> WinFactor:
        """Evalúa calidad estimada de propuesta."""
        # Heurística basada en perfil del usuario

        industry = user_profile.get("industry", "")
        keywords = user_profile.get("include_keywords", [])

        # Usuarios con perfil más completo probablemente hacen mejores propuestas
        profile_completeness = 0
        if industry:
            profile_completeness += 0.3
        if keywords:
            profile_completeness += 0.3
        if user_profile.get("min_budget"):
            profile_completeness += 0.2
        if user_profile.get("max_budget"):
            profile_completeness += 0.2

        value = 0.5 + profile_completeness * 0.3

        if profile_completeness >= 0.8:
            explanation = "Perfil completo sugiere capacidad de propuesta sólida"
            recommendations = []
        elif profile_completeness >= 0.5:
            explanation = "Capacidad de propuesta moderada"
            recommendations = ["Completar tu perfil para mejores recomendaciones"]
        else:
            explanation = "Perfil incompleto - difícil evaluar capacidad de propuesta"
            recommendations = ["Completar perfil con industria y palabras clave", "Definir rangos de presupuesto"]

        return WinFactor(
            name="Calidad de Propuesta",
            weight=self.FACTOR_WEIGHTS["proposal_quality"],
            value=value,
            impact="positive" if value > 0.5 else "neutral",
            explanation=explanation,
            recommendations=recommendations,
        )

    # =========================================================================
    # Métodos auxiliares
    # =========================================================================

    def _get_contract_text(self, contract: Dict[str, Any]) -> str:
        """Obtiene texto del contrato."""
        parts = [contract.get("title", ""), contract.get("description", ""), contract.get("entity", "")]
        return " ".join(filter(None, parts))

    def _get_base_probability(self, contract: Dict[str, Any]) -> float:
        """Obtiene probabilidad base según tipo de contratación."""
        text = self._get_contract_text(contract).lower()

        if "mínima cuantía" in text:
            return self.BASE_PROBABILITIES["minima_cuantia"]
        if "selección abreviada" in text:
            return self.BASE_PROBABILITIES["seleccion_abreviada"]
        if "licitación pública" in text:
            return self.BASE_PROBABILITIES["licitacion_publica"]
        if "contratación directa" in text:
            return self.BASE_PROBABILITIES["contratacion_directa"]
        if "concurso de méritos" in text:
            return self.BASE_PROBABILITIES["concurso_meritos"]

        return self.BASE_PROBABILITIES["default"]

    def _contracts_similar(self, contract1: Dict[str, Any], contract2: Dict[str, Any]) -> bool:
        """Determina si dos contratos son similares."""
        text1 = self._get_contract_text(contract1).lower()
        text2 = self._get_contract_text(contract2).lower()

        # Comparación simple por palabras comunes
        words1 = set(text1.split())
        words2 = set(text2.split())

        # Remover palabras comunes
        stopwords = {"de", "la", "el", "en", "y", "a", "los", "las", "del", "para", "con"}
        words1 -= stopwords
        words2 -= stopwords

        if not words1 or not words2:
            return False

        intersection = words1 & words2
        similarity = len(intersection) / min(len(words1), len(words2))

        return similarity > 0.3

    def _industry_matches_contract(self, industry: str, text: str) -> bool:
        """Verifica si la industria del usuario coincide con el contrato."""
        industry_keywords = {
            "tecnologia": ["software", "sistema", "desarrollo", "aplicación", "digital"],
            "construccion": ["construcción", "obra", "edificio", "infraestructura"],
            "consultoria": ["consultoría", "asesoría", "estudio", "diagnóstico"],
            "salud": ["salud", "médico", "hospital", "farmacéutico"],
            "educacion": ["educación", "capacitación", "formación"],
        }

        keywords = industry_keywords.get(industry, [])
        return any(kw in text for kw in keywords)

    def _calculate_confidence(
        self, contract: Dict[str, Any], user_profile: Dict[str, Any], factors: List[WinFactor]
    ) -> Tuple[str, float]:
        """Calcula nivel de confianza en la predicción."""
        score = 50.0  # Base

        # Más información = más confianza
        if contract.get("amount"):
            score += 10
        if contract.get("deadline"):
            score += 10
        if contract.get("description"):
            score += 10

        if user_profile.get("industry"):
            score += 10
        if user_profile.get("include_keywords"):
            score += 10

        # Factores extremos = más confianza
        extreme_factors = sum(1 for f in factors if f.value > 0.8 or f.value < 0.2)
        score += extreme_factors * 3

        score = min(95, score)

        if score >= 70:
            confidence = "high"
        elif score >= 50:
            confidence = "medium"
        else:
            confidence = "low"

        return confidence, score

    def _generate_improvement_actions(self, factors: List[WinFactor]) -> List[str]:
        """Genera acciones de mejora basadas en factores débiles."""
        actions = []

        # Ordenar por impacto negativo
        negative_factors = [f for f in factors if f.impact == "negative" and f.recommendations]

        negative_factors.sort(key=lambda x: x.value)

        # Tomar recomendaciones de los 3 peores factores
        for factor in negative_factors[:3]:
            actions.extend(factor.recommendations[:1])

        return actions[:5]  # Máximo 5 acciones

    def _determine_competitive_position(self, probability: float) -> str:
        """Determina posición competitiva basada en probabilidad."""
        if probability >= 40:
            return "strong"
        elif probability >= 20:
            return "moderate"
        else:
            return "weak"


# Singleton
_win_predictor = None


def get_win_predictor() -> WinPredictor:
    """Obtiene la instancia singleton del predictor."""
    global _win_predictor
    if _win_predictor is None:
        _win_predictor = WinPredictor()
    return _win_predictor
