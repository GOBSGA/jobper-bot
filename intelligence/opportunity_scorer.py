"""
Opportunity Scorer
Sistema de scoring multi-dimensional para oportunidades de contratación.

Este módulo implementa un algoritmo de scoring sofisticado que considera
múltiples factores para determinar qué tan buena es una oportunidad
para un usuario específico.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ScoreDimension(str, Enum):
    """Dimensiones del scoring."""
    RELEVANCE = "relevance"           # Qué tan relevante es para el usuario
    OPPORTUNITY = "opportunity"        # Qué tan buena es la oportunidad
    FEASIBILITY = "feasibility"        # Qué tan factible es ganar
    TIMING = "timing"                  # Timing (deadline, preparación)
    VALUE = "value"                    # Valor económico
    STRATEGIC = "strategic"            # Valor estratégico


@dataclass
class DimensionScore:
    """Score de una dimensión específica."""
    dimension: ScoreDimension
    score: float                       # 0-100
    weight: float                      # Peso relativo
    factors: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""


@dataclass
class OpportunityScore:
    """Score completo de una oportunidad."""
    # Scores por dimensión
    dimensions: Dict[ScoreDimension, DimensionScore] = field(default_factory=dict)

    # Score final ponderado
    total_score: float = 0.0           # 0-100

    # Ranking relativo
    percentile: Optional[float] = None  # En qué percentil está vs otras oportunidades

    # Clasificación
    tier: str = "C"                    # S, A, B, C, D
    recommendation: str = ""

    # Detalles
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    key_factors: List[Tuple[str, float]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return {
            "total_score": round(self.total_score, 1),
            "tier": self.tier,
            "percentile": self.percentile,
            "recommendation": self.recommendation,
            "dimensions": {
                dim.value: {
                    "score": round(ds.score, 1),
                    "weight": ds.weight,
                    "explanation": ds.explanation
                }
                for dim, ds in self.dimensions.items()
            },
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "key_factors": self.key_factors
        }


class OpportunityScorer:
    """
    Motor de scoring multi-dimensional para oportunidades.

    Evalúa contratos en múltiples dimensiones y produce un score
    final ponderado que representa la calidad de la oportunidad
    para un usuario específico.
    """

    # Pesos por dimensión (deben sumar 1.0)
    DEFAULT_WEIGHTS = {
        ScoreDimension.RELEVANCE: 0.25,
        ScoreDimension.OPPORTUNITY: 0.20,
        ScoreDimension.FEASIBILITY: 0.20,
        ScoreDimension.TIMING: 0.15,
        ScoreDimension.VALUE: 0.10,
        ScoreDimension.STRATEGIC: 0.10,
    }

    # Umbrales para tiers
    TIER_THRESHOLDS = {
        "S": 85,   # Oportunidad excepcional
        "A": 70,   # Muy buena oportunidad
        "B": 55,   # Buena oportunidad
        "C": 40,   # Oportunidad promedio
        "D": 0,    # Oportunidad débil
    }

    def __init__(self, weights: Optional[Dict[ScoreDimension, float]] = None):
        """
        Inicializa el scorer.

        Args:
            weights: Pesos personalizados por dimensión (opcional)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

        # Normalizar pesos
        total_weight = sum(self.weights.values())
        self.weights = {k: v / total_weight for k, v in self.weights.items()}

        logger.info("OpportunityScorer inicializado")

    def score(
        self,
        contract: Dict[str, Any],
        user_profile: Dict[str, Any],
        market_context: Optional[Dict[str, Any]] = None
    ) -> OpportunityScore:
        """
        Calcula el score completo de una oportunidad.

        Args:
            contract: Datos del contrato
            user_profile: Perfil del usuario
            market_context: Contexto de mercado (opcional)

        Returns:
            OpportunityScore con evaluación completa
        """
        result = OpportunityScore()

        # Calcular cada dimensión
        result.dimensions[ScoreDimension.RELEVANCE] = self._score_relevance(
            contract, user_profile
        )
        result.dimensions[ScoreDimension.OPPORTUNITY] = self._score_opportunity(
            contract, market_context
        )
        result.dimensions[ScoreDimension.FEASIBILITY] = self._score_feasibility(
            contract, user_profile
        )
        result.dimensions[ScoreDimension.TIMING] = self._score_timing(contract)
        result.dimensions[ScoreDimension.VALUE] = self._score_value(
            contract, user_profile
        )
        result.dimensions[ScoreDimension.STRATEGIC] = self._score_strategic(
            contract, user_profile
        )

        # Calcular score total ponderado
        result.total_score = sum(
            ds.score * self.weights[dim]
            for dim, ds in result.dimensions.items()
        )

        # Determinar tier
        result.tier = self._determine_tier(result.total_score)

        # Extraer fortalezas y debilidades
        result.strengths, result.weaknesses = self._extract_strengths_weaknesses(
            result.dimensions
        )

        # Extraer factores clave
        result.key_factors = self._extract_key_factors(result.dimensions)

        # Generar recomendación
        result.recommendation = self._generate_recommendation(result)

        return result

    def score_batch(
        self,
        contracts: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        market_context: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Dict[str, Any], OpportunityScore]]:
        """
        Calcula scores para múltiples contratos y los rankea.

        Returns:
            Lista de (contrato, score) ordenada por score descendente
        """
        scored = []

        for contract in contracts:
            score = self.score(contract, user_profile, market_context)
            scored.append((contract, score))

        # Ordenar por score total
        scored.sort(key=lambda x: x[1].total_score, reverse=True)

        # Calcular percentiles
        total = len(scored)
        for i, (contract, score) in enumerate(scored):
            score.percentile = (total - i) / total * 100

        return scored

    def _score_relevance(
        self,
        contract: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> DimensionScore:
        """
        Evalúa qué tan relevante es el contrato para el usuario.

        Factores:
        - Match de industria
        - Match de keywords
        - Match de país/región
        - Match de tipo de contrato
        """
        factors = {}
        score = 0.0

        text = self._get_contract_text(contract).lower()

        # 1. Match de industria (30 puntos)
        user_industry = user_profile.get("industry", "")
        if user_industry:
            industry_keywords = self._get_industry_keywords(user_industry)
            matches = sum(1 for kw in industry_keywords if kw in text)
            industry_score = min(30, (matches / max(len(industry_keywords), 1)) * 40)
            factors["industry_match"] = industry_score
            score += industry_score

        # 2. Match de keywords personalizadas (30 puntos)
        user_keywords = user_profile.get("include_keywords", [])
        if user_keywords:
            matches = sum(1 for kw in user_keywords if kw.lower() in text)
            keyword_score = min(30, (matches / len(user_keywords)) * 40)
            factors["keyword_match"] = keyword_score
            score += keyword_score

        # 3. Match de país (20 puntos)
        user_countries = user_profile.get("countries", "all")
        contract_country = contract.get("country", "").lower()

        if user_countries == "all" or contract_country in user_countries.lower():
            factors["country_match"] = 20
            score += 20
        else:
            factors["country_match"] = 0

        # 4. No está en exclusiones (20 puntos)
        exclude_keywords = user_profile.get("exclude_keywords", [])
        excluded = any(kw.lower() in text for kw in exclude_keywords)

        if not excluded:
            factors["not_excluded"] = 20
            score += 20
        else:
            factors["not_excluded"] = 0

        return DimensionScore(
            dimension=ScoreDimension.RELEVANCE,
            score=min(100, score),
            weight=self.weights[ScoreDimension.RELEVANCE],
            factors=factors,
            explanation=self._explain_relevance(factors)
        )

    def _score_opportunity(
        self,
        contract: Dict[str, Any],
        market_context: Optional[Dict[str, Any]]
    ) -> DimensionScore:
        """
        Evalúa qué tan buena es la oportunidad en sí misma.

        Factores:
        - Nivel de competencia esperado
        - Monto atractivo
        - Fuente confiable
        - Información completa
        """
        factors = {}
        score = 50.0  # Base neutral

        # 1. Estimación de competencia (25 puntos)
        competition_score = self._estimate_competition_score(contract, market_context)
        factors["low_competition"] = competition_score
        score += competition_score - 12.5  # Ajuste desde base

        # 2. Información completa (25 puntos)
        completeness = self._calculate_completeness(contract)
        factors["completeness"] = completeness * 25
        score += (completeness - 0.5) * 25

        # 3. Fuente confiable (25 puntos)
        source_score = self._score_source_reliability(contract.get("source", ""))
        factors["source_reliability"] = source_score
        score += (source_score / 25 - 0.5) * 25

        # 4. Deadline razonable (25 puntos)
        deadline_score = self._score_deadline_reasonability(contract)
        factors["deadline_reasonable"] = deadline_score
        score += (deadline_score / 25 - 0.5) * 25

        return DimensionScore(
            dimension=ScoreDimension.OPPORTUNITY,
            score=max(0, min(100, score)),
            weight=self.weights[ScoreDimension.OPPORTUNITY],
            factors=factors,
            explanation=self._explain_opportunity(factors)
        )

    def _score_feasibility(
        self,
        contract: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> DimensionScore:
        """
        Evalúa qué tan factible es para el usuario ganar/ejecutar el contrato.

        Factores:
        - Requisitos de experiencia
        - Requisitos financieros
        - Requisitos de certificaciones
        - Ubicación geográfica
        """
        factors = {}
        score = 70.0  # Optimista por defecto

        text = self._get_contract_text(contract).lower()
        amount = contract.get("amount", 0) or 0

        # 1. Capacidad financiera (30 puntos)
        min_budget = user_profile.get("min_budget", 0) or 0
        max_budget = user_profile.get("max_budget") or float('inf')

        if amount > 0:
            if min_budget <= amount <= max_budget:
                factors["financial_capacity"] = 30
            elif amount < min_budget:
                factors["financial_capacity"] = 20  # Muy pequeño
            else:
                # Muy grande - posible problema de capacidad
                over_ratio = amount / max_budget if max_budget else 1
                factors["financial_capacity"] = max(0, 30 - (over_ratio - 1) * 20)
        else:
            factors["financial_capacity"] = 20  # Sin info

        # 2. Experiencia requerida (25 puntos)
        exp_patterns = r"(\d+)\s*a[ñn]os?\s*(?:de\s+)?experiencia"
        import re
        exp_matches = re.findall(exp_patterns, text)

        if exp_matches:
            max_exp = max(int(e) for e in exp_matches)
            if max_exp <= 2:
                factors["experience_match"] = 25
            elif max_exp <= 5:
                factors["experience_match"] = 20
            elif max_exp <= 10:
                factors["experience_match"] = 12
            else:
                factors["experience_match"] = 5
        else:
            factors["experience_match"] = 22  # Sin requisito explícito

        # 3. Certificaciones (25 puntos)
        cert_patterns = ["iso", "cmmi", "pmp", "itil", "cobit"]
        certs_required = sum(1 for p in cert_patterns if p in text)

        if certs_required == 0:
            factors["certifications"] = 25
        elif certs_required == 1:
            factors["certifications"] = 20
        elif certs_required <= 3:
            factors["certifications"] = 12
        else:
            factors["certifications"] = 5

        # 4. Ubicación/Presencia (20 puntos)
        local_required = any(p in text for p in [
            "presencia local", "oficina en", "sede en la ciudad"
        ])

        if not local_required:
            factors["location"] = 20
        else:
            # Verificar si el usuario tiene presencia
            user_city = user_profile.get("city", "").lower()
            contract_location = contract.get("city", "").lower()

            if user_city and contract_location and user_city in contract_location:
                factors["location"] = 20
            else:
                factors["location"] = 5

        # Calcular score total
        score = sum(factors.values())

        return DimensionScore(
            dimension=ScoreDimension.FEASIBILITY,
            score=min(100, score),
            weight=self.weights[ScoreDimension.FEASIBILITY],
            factors=factors,
            explanation=self._explain_feasibility(factors)
        )

    def _score_timing(self, contract: Dict[str, Any]) -> DimensionScore:
        """
        Evalúa el timing de la oportunidad.

        Factores:
        - Días hasta deadline
        - Recencia de publicación
        - Tiempo de preparación estimado
        """
        factors = {}
        score = 50.0

        now = datetime.now()

        # 1. Días hasta deadline (50 puntos)
        deadline = contract.get("deadline")
        if deadline:
            try:
                if isinstance(deadline, str):
                    deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))

                days_left = (deadline - now).days

                if days_left < 0:
                    factors["deadline"] = 0  # Expirado
                elif days_left <= 2:
                    factors["deadline"] = 10  # Muy urgente
                elif days_left <= 5:
                    factors["deadline"] = 25  # Urgente
                elif days_left <= 14:
                    factors["deadline"] = 40  # Adecuado
                elif days_left <= 30:
                    factors["deadline"] = 50  # Óptimo
                else:
                    factors["deadline"] = 45  # Muy adelantado (puede olvidarse)
            except (ValueError, TypeError):
                factors["deadline"] = 30  # Sin info válida
        else:
            factors["deadline"] = 30

        # 2. Recencia de publicación (30 puntos)
        pub_date = contract.get("publication_date")
        if pub_date:
            try:
                if isinstance(pub_date, str):
                    pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))

                days_old = (now - pub_date).days

                if days_old <= 1:
                    factors["recency"] = 30  # Muy reciente
                elif days_old <= 3:
                    factors["recency"] = 25
                elif days_old <= 7:
                    factors["recency"] = 20
                elif days_old <= 14:
                    factors["recency"] = 10
                else:
                    factors["recency"] = 5  # Antiguo
            except (ValueError, TypeError):
                factors["recency"] = 15
        else:
            factors["recency"] = 15

        # 3. Tiempo de preparación adecuado (20 puntos)
        # Basado en complejidad estimada del contrato
        amount = contract.get("amount", 0) or 0
        days_left = factors.get("deadline", 30) / 50 * 30  # Estimar días

        if amount > 1_000_000_000:  # > 1B - necesita más preparación
            prep_needed = 21
        elif amount > 100_000_000:  # > 100M
            prep_needed = 14
        else:
            prep_needed = 7

        if days_left >= prep_needed:
            factors["prep_time"] = 20
        elif days_left >= prep_needed * 0.5:
            factors["prep_time"] = 10
        else:
            factors["prep_time"] = 0

        score = sum(factors.values())

        return DimensionScore(
            dimension=ScoreDimension.TIMING,
            score=min(100, score),
            weight=self.weights[ScoreDimension.TIMING],
            factors=factors,
            explanation=self._explain_timing(factors, contract)
        )

    def _score_value(
        self,
        contract: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> DimensionScore:
        """
        Evalúa el valor económico de la oportunidad.

        Factores:
        - Monto absoluto
        - Margen estimado
        - Valor relativo al perfil del usuario
        """
        factors = {}
        amount = contract.get("amount", 0) or 0

        # 1. Monto absoluto (40 puntos)
        if amount > 0:
            if amount >= 5_000_000_000:  # > 5B
                factors["absolute_value"] = 40
            elif amount >= 1_000_000_000:  # > 1B
                factors["absolute_value"] = 35
            elif amount >= 500_000_000:  # > 500M
                factors["absolute_value"] = 30
            elif amount >= 100_000_000:  # > 100M
                factors["absolute_value"] = 25
            elif amount >= 50_000_000:  # > 50M
                factors["absolute_value"] = 20
            elif amount >= 10_000_000:  # > 10M
                factors["absolute_value"] = 15
            else:
                factors["absolute_value"] = 10
        else:
            factors["absolute_value"] = 15  # Sin info

        # 2. Valor relativo al usuario (30 puntos)
        min_budget = user_profile.get("min_budget", 0) or 0
        max_budget = user_profile.get("max_budget") or amount * 2

        if amount > 0 and max_budget > 0:
            if min_budget <= amount <= max_budget:
                # En el rango ideal
                factors["relative_value"] = 30
            elif amount < min_budget:
                # Muy pequeño para el usuario
                ratio = amount / min_budget if min_budget > 0 else 1
                factors["relative_value"] = max(5, 20 * ratio)
            else:
                # Muy grande para el usuario (pero podría ser aspiracional)
                ratio = max_budget / amount if amount > 0 else 1
                factors["relative_value"] = max(10, 25 * ratio)
        else:
            factors["relative_value"] = 20

        # 3. Potencial de margen (30 puntos)
        # Servicios y consultoría tienen mejores márgenes que suministro
        text = self._get_contract_text(contract).lower()

        high_margin_keywords = ["consultoría", "asesoría", "desarrollo", "software", "capacitación"]
        low_margin_keywords = ["suministro", "compra de", "adquisición", "dotación"]

        high_match = sum(1 for kw in high_margin_keywords if kw in text)
        low_match = sum(1 for kw in low_margin_keywords if kw in text)

        if high_match > low_match:
            factors["margin_potential"] = 30
        elif low_match > high_match:
            factors["margin_potential"] = 15
        else:
            factors["margin_potential"] = 22

        score = sum(factors.values())

        return DimensionScore(
            dimension=ScoreDimension.VALUE,
            score=min(100, score),
            weight=self.weights[ScoreDimension.VALUE],
            factors=factors,
            explanation=self._explain_value(factors, contract)
        )

    def _score_strategic(
        self,
        contract: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> DimensionScore:
        """
        Evalúa el valor estratégico de la oportunidad.

        Factores:
        - Entidad prestigiosa
        - Sector estratégico
        - Potencial de contratos futuros
        - Diversificación de cartera
        """
        factors = {}
        text = self._get_contract_text(contract).lower()
        entity = contract.get("entity", "").lower()

        # 1. Entidad prestigiosa (35 puntos)
        prestigious_entities = [
            "ministerio", "presidencia", "banco", "ecopetrol", "epm",
            "banco mundial", "bid", "onu", "naciones unidas", "usaid",
            "fondo monetario", "fmi"
        ]

        if any(pe in entity for pe in prestigious_entities):
            factors["prestigious_entity"] = 35
        elif any(pe in entity for pe in ["alcaldía", "gobernación", "universidad"]):
            factors["prestigious_entity"] = 25
        else:
            factors["prestigious_entity"] = 15

        # 2. Sector estratégico (25 puntos)
        strategic_sectors = [
            "transformación digital", "inteligencia artificial", "blockchain",
            "energías renovables", "ciberseguridad", "smart city",
            "salud digital", "fintech", "e-government"
        ]

        if any(ss in text for ss in strategic_sectors):
            factors["strategic_sector"] = 25
        else:
            factors["strategic_sector"] = 10

        # 3. Potencial de continuidad (20 puntos)
        continuity_signals = [
            "marco", "acuerdo marco", "indefinido", "varios años",
            "renovable", "extensible", "fase 1", "etapa inicial"
        ]

        if any(cs in text for cs in continuity_signals):
            factors["continuity_potential"] = 20
        else:
            factors["continuity_potential"] = 10

        # 4. Diversificación (20 puntos)
        # Si es un sector/entidad diferente al historial del usuario
        user_industry = user_profile.get("industry", "")
        contract_type = self._detect_simple_type(text)

        # Asumimos que diversificación es buena para crecimiento
        if contract_type != user_industry:
            factors["diversification"] = 15  # Moderado - es oportunidad pero riesgo
        else:
            factors["diversification"] = 20  # En su zona de confort

        score = sum(factors.values())

        return DimensionScore(
            dimension=ScoreDimension.STRATEGIC,
            score=min(100, score),
            weight=self.weights[ScoreDimension.STRATEGIC],
            factors=factors,
            explanation=self._explain_strategic(factors, contract)
        )

    # =========================================================================
    # Métodos auxiliares
    # =========================================================================

    def _get_contract_text(self, contract: Dict[str, Any]) -> str:
        """Obtiene todo el texto relevante del contrato."""
        parts = [
            contract.get("title", ""),
            contract.get("description", ""),
            contract.get("entity", ""),
        ]
        return " ".join(filter(None, parts))

    def _get_industry_keywords(self, industry: str) -> List[str]:
        """Obtiene keywords de una industria."""
        from config import Config
        industry_config = Config.INDUSTRIES.get(industry, {})
        return industry_config.get("keywords", [])

    def _estimate_competition_score(
        self,
        contract: Dict[str, Any],
        market_context: Optional[Dict[str, Any]]
    ) -> float:
        """Estima score basado en competencia esperada (más alto = menos competencia)."""
        score = 12.5  # Base
        amount = contract.get("amount", 0) or 0
        text = self._get_contract_text(contract).lower()

        # Contratos más grandes = menos competidores
        if amount > 1_000_000_000:
            score += 10
        elif amount > 500_000_000:
            score += 5

        # Requisitos específicos = menos competidores
        specific_requirements = ["certificación", "iso", "experiencia específica", "consorcio"]
        specificity = sum(1 for req in specific_requirements if req in text)
        score += specificity * 3

        return min(25, score)

    def _calculate_completeness(self, contract: Dict[str, Any]) -> float:
        """Calcula qué tan completa está la información del contrato."""
        fields = ["title", "description", "entity", "amount", "deadline", "url"]
        present = sum(1 for f in fields if contract.get(f))
        return present / len(fields)

    def _score_source_reliability(self, source: str) -> float:
        """Evalúa confiabilidad de la fuente."""
        source_lower = source.lower()

        if any(s in source_lower for s in ["secop", "sam.gov", "compranet"]):
            return 25  # Fuentes gubernamentales oficiales
        if any(s in source_lower for s in ["banco mundial", "bid", "onu", "ungm"]):
            return 25  # Multilaterales
        if any(s in source_lower for s in ["ecopetrol", "epm"]):
            return 22  # Grandes empresas
        return 15  # Otras fuentes

    def _score_deadline_reasonability(self, contract: Dict[str, Any]) -> float:
        """Evalúa si el deadline es razonable."""
        deadline = contract.get("deadline")
        if not deadline:
            return 15

        try:
            if isinstance(deadline, str):
                deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))

            days_left = (deadline - datetime.now()).days

            if days_left < 0:
                return 0
            if days_left < 3:
                return 5
            if days_left < 7:
                return 15
            if days_left < 30:
                return 25
            return 20  # Muy lejano podría olvidarse
        except (ValueError, TypeError):
            return 15

    def _detect_simple_type(self, text: str) -> str:
        """Detecta tipo simple de contrato."""
        if any(kw in text for kw in ["software", "desarrollo", "aplicación", "sistema"]):
            return "tecnologia"
        if any(kw in text for kw in ["construcción", "obra", "edificio"]):
            return "construccion"
        if any(kw in text for kw in ["consultoría", "asesoría", "estudio"]):
            return "consultoria"
        return "general"

    def _determine_tier(self, score: float) -> str:
        """Determina el tier basado en el score."""
        for tier, threshold in self.TIER_THRESHOLDS.items():
            if score >= threshold:
                return tier
        return "D"

    def _extract_strengths_weaknesses(
        self,
        dimensions: Dict[ScoreDimension, DimensionScore]
    ) -> Tuple[List[str], List[str]]:
        """Extrae fortalezas y debilidades del análisis."""
        strengths = []
        weaknesses = []

        for dim, ds in dimensions.items():
            for factor, value in ds.factors.items():
                max_value = 30  # Aproximado

                if value >= max_value * 0.8:
                    strengths.append(self._factor_to_text(factor, True))
                elif value <= max_value * 0.3:
                    weaknesses.append(self._factor_to_text(factor, False))

        return strengths[:5], weaknesses[:5]

    def _factor_to_text(self, factor: str, is_strength: bool) -> str:
        """Convierte factor a texto legible."""
        texts = {
            "industry_match": ("Alta coincidencia con tu industria", "Baja coincidencia con tu industria"),
            "keyword_match": ("Coincide con tus palabras clave", "Pocas palabras clave coinciden"),
            "country_match": ("País de interés", "Fuera de tus países de interés"),
            "financial_capacity": ("Dentro de tu capacidad financiera", "Fuera de tu rango de presupuesto"),
            "deadline": ("Deadline con tiempo suficiente", "Deadline muy ajustado"),
            "low_competition": ("Baja competencia esperada", "Alta competencia esperada"),
            "prestigious_entity": ("Entidad prestigiosa", "Entidad poco conocida"),
        }

        default = (factor.replace("_", " ").title(), f"Bajo en {factor.replace('_', ' ')}")
        return texts.get(factor, default)[0 if is_strength else 1]

    def _extract_key_factors(
        self,
        dimensions: Dict[ScoreDimension, DimensionScore]
    ) -> List[Tuple[str, float]]:
        """Extrae los factores más importantes."""
        all_factors = []

        for dim, ds in dimensions.items():
            for factor, value in ds.factors.items():
                weighted_value = value * ds.weight
                all_factors.append((factor, weighted_value))

        # Top 5 factores más influyentes
        all_factors.sort(key=lambda x: abs(x[1]), reverse=True)
        return all_factors[:5]

    def _generate_recommendation(self, result: OpportunityScore) -> str:
        """Genera recomendación basada en el análisis."""
        tier = result.tier
        score = result.total_score

        if tier == "S":
            return "PRIORIDAD MÁXIMA: Oportunidad excepcional. Dedica recursos significativos a esta propuesta."
        if tier == "A":
            return "ALTA PRIORIDAD: Muy buena oportunidad. Vale la pena invertir tiempo en preparar una propuesta sólida."
        if tier == "B":
            return "PRIORIDAD MEDIA: Buena oportunidad. Evalúa si tienes capacidad disponible para participar."
        if tier == "C":
            return "PRIORIDAD BAJA: Oportunidad promedio. Considera solo si no tienes mejores opciones."
        return "NO RECOMENDADO: Esta oportunidad no parece ser un buen fit. Enfoca recursos en otras."

    # =========================================================================
    # Métodos de explicación
    # =========================================================================

    def _explain_relevance(self, factors: Dict[str, float]) -> str:
        """Explica el score de relevancia."""
        parts = []
        if factors.get("industry_match", 0) >= 20:
            parts.append("alta coincidencia con tu industria")
        if factors.get("keyword_match", 0) >= 20:
            parts.append("coincide con tus palabras clave")

        if parts:
            return "Relevante porque: " + ", ".join(parts)
        return "Relevancia moderada basada en tu perfil"

    def _explain_opportunity(self, factors: Dict[str, float]) -> str:
        """Explica el score de oportunidad."""
        if factors.get("low_competition", 0) >= 20:
            return "Buena oportunidad con competencia esperada baja"
        if factors.get("completeness", 0) >= 20:
            return "Información completa disponible para evaluar"
        return "Oportunidad estándar del mercado"

    def _explain_feasibility(self, factors: Dict[str, float]) -> str:
        """Explica el score de factibilidad."""
        if factors.get("financial_capacity", 0) >= 25:
            return "Dentro de tu capacidad financiera"
        if factors.get("experience_match", 0) >= 20:
            return "Requisitos de experiencia accesibles"
        return "Verifica que cumples todos los requisitos"

    def _explain_timing(self, factors: Dict[str, float], contract: Dict[str, Any]) -> str:
        """Explica el score de timing."""
        deadline_score = factors.get("deadline", 0)
        if deadline_score >= 40:
            return "Tiempo suficiente para preparar propuesta"
        if deadline_score >= 20:
            return "Deadline ajustado pero manejable"
        if deadline_score > 0:
            return "Muy poco tiempo - actúa rápido"
        return "Deadline vencido o no especificado"

    def _explain_value(self, factors: Dict[str, float], contract: Dict[str, Any]) -> str:
        """Explica el score de valor."""
        amount = contract.get("amount", 0)
        if amount and amount > 500_000_000:
            return f"Alto valor: ${amount/1_000_000:,.0f}M"
        if factors.get("margin_potential", 0) >= 25:
            return "Potencial de buenos márgenes"
        return "Valor económico estándar"

    def _explain_strategic(self, factors: Dict[str, float], contract: Dict[str, Any]) -> str:
        """Explica el score estratégico."""
        if factors.get("prestigious_entity", 0) >= 30:
            return f"Entidad prestigiosa: {contract.get('entity', 'N/A')}"
        if factors.get("strategic_sector", 0) >= 20:
            return "Sector estratégico con potencial de crecimiento"
        return "Valor estratégico moderado"


# Singleton
_opportunity_scorer = None


def get_opportunity_scorer() -> OpportunityScorer:
    """Obtiene la instancia singleton del scorer."""
    global _opportunity_scorer
    if _opportunity_scorer is None:
        _opportunity_scorer = OpportunityScorer()
    return _opportunity_scorer
