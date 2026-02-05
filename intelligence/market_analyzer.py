"""
Market Analyzer
Análisis de mercado y tendencias para contratación pública y privada.

Proporciona inteligencia de mercado que permite a los usuarios
tomar decisiones informadas sobre dónde enfocar sus esfuerzos.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class TrendDirection(str, Enum):
    """Dirección de tendencia."""
    RISING = "rising"
    STABLE = "stable"
    FALLING = "falling"


class MarketSegment(str, Enum):
    """Segmentos de mercado."""
    GOVERNMENT_NATIONAL = "gov_national"
    GOVERNMENT_LOCAL = "gov_local"
    PRIVATE_LARGE = "private_large"
    PRIVATE_SME = "private_sme"
    MULTILATERAL = "multilateral"
    INTERNATIONAL = "international"


@dataclass
class MarketTrend:
    """Tendencia de mercado identificada."""
    name: str
    direction: TrendDirection
    strength: float             # 0-100
    description: str
    evidence: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)


@dataclass
class SectorAnalysis:
    """Análisis de un sector específico."""
    sector: str
    total_contracts: int
    total_value: float
    average_value: float
    growth_rate: float          # vs período anterior
    top_entities: List[Tuple[str, int]]
    top_keywords: List[Tuple[str, int]]
    competition_level: str
    opportunity_rating: float   # 0-100


@dataclass
class CompetitorInsight:
    """Insight sobre competencia en el mercado."""
    segment: str
    estimated_competitors: int
    barrier_to_entry: str       # "low", "medium", "high"
    typical_requirements: List[str]
    success_factors: List[str]


@dataclass
class MarketReport:
    """Reporte completo de análisis de mercado."""
    generated_at: datetime
    period_start: datetime
    period_end: datetime

    # Métricas generales
    total_contracts: int
    total_value: float
    contracts_by_source: Dict[str, int]
    contracts_by_country: Dict[str, int]

    # Análisis por sector
    sector_analyses: Dict[str, SectorAnalysis] = field(default_factory=dict)

    # Tendencias identificadas
    trends: List[MarketTrend] = field(default_factory=list)

    # Insights de competencia
    competitor_insights: Dict[str, CompetitorInsight] = field(default_factory=dict)

    # Oportunidades destacadas
    hot_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    emerging_sectors: List[str] = field(default_factory=list)

    # Alertas
    market_alerts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat()
            },
            "overview": {
                "total_contracts": self.total_contracts,
                "total_value": self.total_value,
                "by_source": self.contracts_by_source,
                "by_country": self.contracts_by_country
            },
            "sectors": {
                k: {
                    "total_contracts": v.total_contracts,
                    "total_value": v.total_value,
                    "growth_rate": v.growth_rate,
                    "opportunity_rating": v.opportunity_rating
                }
                for k, v in self.sector_analyses.items()
            },
            "trends": [
                {
                    "name": t.name,
                    "direction": t.direction.value,
                    "strength": t.strength,
                    "description": t.description
                }
                for t in self.trends
            ],
            "hot_opportunities": len(self.hot_opportunities),
            "emerging_sectors": self.emerging_sectors,
            "alerts": self.market_alerts
        }


class MarketAnalyzer:
    """
    Analizador de mercado para contratación.

    Procesa datos de contratos para identificar tendencias,
    oportunidades y generar inteligencia de mercado.
    """

    # Mapeo de keywords a sectores
    SECTOR_KEYWORDS = {
        "tecnologia": [
            "software", "desarrollo", "sistema", "aplicación", "plataforma",
            "digital", "tecnología", "informática", "ti", "tic", "datos"
        ],
        "construccion": [
            "construcción", "obra", "edificio", "infraestructura", "vía",
            "carretera", "puente", "vivienda", "urbanismo"
        ],
        "salud": [
            "salud", "médico", "hospital", "medicamento", "farmacéutico",
            "clínico", "eps", "ips", "vacuna"
        ],
        "educacion": [
            "educación", "capacitación", "formación", "universidad", "escuela",
            "docente", "académico", "curso"
        ],
        "consultoria": [
            "consultoría", "asesoría", "estudio", "diagnóstico", "evaluación",
            "interventoría", "auditoría"
        ],
        "logistica": [
            "transporte", "logística", "distribución", "almacenamiento",
            "cadena de suministro", "envío"
        ],
        "energia": [
            "energía", "eléctrico", "renovable", "solar", "petróleo",
            "gas", "ambiental"
        ],
        "alimentos": [
            "alimentos", "alimentación", "catering", "restaurante",
            "suministro de alimentos", "refrigerio"
        ]
    }

    def __init__(self):
        """Inicializa el analizador."""
        self._cache = {}
        logger.info("MarketAnalyzer inicializado")

    def analyze_market(
        self,
        contracts: List[Dict[str, Any]],
        period_days: int = 30,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> MarketReport:
        """
        Genera un reporte completo de análisis de mercado.

        Args:
            contracts: Lista de contratos a analizar
            period_days: Período de análisis en días
            user_profile: Perfil del usuario para personalizar

        Returns:
            MarketReport con análisis completo
        """
        now = datetime.now()
        period_start = now - timedelta(days=period_days)

        # Filtrar contratos del período
        period_contracts = self._filter_by_period(contracts, period_start, now)

        # Crear reporte base
        report = MarketReport(
            generated_at=now,
            period_start=period_start,
            period_end=now,
            total_contracts=len(period_contracts),
            total_value=sum(c.get("amount", 0) or 0 for c in period_contracts),
            contracts_by_source=self._count_by_field(period_contracts, "source"),
            contracts_by_country=self._count_by_field(period_contracts, "country")
        )

        # Análisis por sector
        report.sector_analyses = self._analyze_sectors(period_contracts)

        # Identificar tendencias
        report.trends = self._identify_trends(period_contracts, contracts)

        # Insights de competencia
        report.competitor_insights = self._analyze_competition(period_contracts)

        # Oportunidades calientes
        if user_profile:
            report.hot_opportunities = self._find_hot_opportunities(
                period_contracts, user_profile
            )

        # Sectores emergentes
        report.emerging_sectors = self._identify_emerging_sectors(
            period_contracts, contracts
        )

        # Alertas de mercado
        report.market_alerts = self._generate_alerts(report)

        return report

    def get_sector_insights(
        self,
        contracts: List[Dict[str, Any]],
        sector: str
    ) -> SectorAnalysis:
        """
        Obtiene análisis detallado de un sector específico.

        Args:
            contracts: Contratos a analizar
            sector: Sector a analizar

        Returns:
            SectorAnalysis con métricas detalladas
        """
        # Filtrar contratos del sector
        sector_contracts = self._filter_by_sector(contracts, sector)

        if not sector_contracts:
            return SectorAnalysis(
                sector=sector,
                total_contracts=0,
                total_value=0,
                average_value=0,
                growth_rate=0,
                top_entities=[],
                top_keywords=[],
                competition_level="unknown",
                opportunity_rating=0
            )

        total_value = sum(c.get("amount", 0) or 0 for c in sector_contracts)
        avg_value = total_value / len(sector_contracts) if sector_contracts else 0

        return SectorAnalysis(
            sector=sector,
            total_contracts=len(sector_contracts),
            total_value=total_value,
            average_value=avg_value,
            growth_rate=self._calculate_growth_rate(contracts, sector),
            top_entities=self._get_top_entities(sector_contracts),
            top_keywords=self._get_top_keywords(sector_contracts),
            competition_level=self._estimate_competition(sector_contracts),
            opportunity_rating=self._rate_sector_opportunity(sector_contracts)
        )

    def compare_periods(
        self,
        contracts: List[Dict[str, Any]],
        current_days: int = 30,
        previous_days: int = 30
    ) -> Dict[str, Any]:
        """
        Compara métricas entre dos períodos.

        Returns:
            Diccionario con comparaciones
        """
        now = datetime.now()

        # Período actual
        current_start = now - timedelta(days=current_days)
        current_contracts = self._filter_by_period(contracts, current_start, now)

        # Período anterior
        previous_end = current_start
        previous_start = previous_end - timedelta(days=previous_days)
        previous_contracts = self._filter_by_period(contracts, previous_start, previous_end)

        # Calcular métricas
        current_count = len(current_contracts)
        previous_count = len(previous_contracts)

        current_value = sum(c.get("amount", 0) or 0 for c in current_contracts)
        previous_value = sum(c.get("amount", 0) or 0 for c in previous_contracts)

        return {
            "current_period": {
                "contracts": current_count,
                "total_value": current_value,
                "avg_value": current_value / current_count if current_count else 0
            },
            "previous_period": {
                "contracts": previous_count,
                "total_value": previous_value,
                "avg_value": previous_value / previous_count if previous_count else 0
            },
            "changes": {
                "contracts_change": self._calculate_change(previous_count, current_count),
                "value_change": self._calculate_change(previous_value, current_value)
            }
        }

    def get_entity_profile(
        self,
        contracts: List[Dict[str, Any]],
        entity_name: str
    ) -> Dict[str, Any]:
        """
        Genera perfil de una entidad contratante.

        Args:
            contracts: Contratos a analizar
            entity_name: Nombre de la entidad

        Returns:
            Perfil con historial y patrones
        """
        # Filtrar contratos de la entidad
        entity_contracts = [
            c for c in contracts
            if entity_name.lower() in (c.get("entity", "") or "").lower()
        ]

        if not entity_contracts:
            return {"error": "Entidad no encontrada", "entity": entity_name}

        # Analizar patrones
        total_value = sum(c.get("amount", 0) or 0 for c in entity_contracts)
        avg_value = total_value / len(entity_contracts)

        # Sectores que contrata
        sectors = defaultdict(int)
        for contract in entity_contracts:
            sector = self._detect_sector(contract)
            sectors[sector] += 1

        # Frecuencia de contratación
        dates = [
            c.get("publication_date") for c in entity_contracts
            if c.get("publication_date")
        ]

        return {
            "entity": entity_name,
            "total_contracts": len(entity_contracts),
            "total_value": total_value,
            "average_value": avg_value,
            "sectors": dict(sectors),
            "top_sector": max(sectors, key=sectors.get) if sectors else None,
            "contracting_frequency": self._estimate_frequency(dates),
            "recent_contracts": entity_contracts[:5]
        }

    # =========================================================================
    # Métodos privados de análisis
    # =========================================================================

    def _filter_by_period(
        self,
        contracts: List[Dict[str, Any]],
        start: datetime,
        end: datetime
    ) -> List[Dict[str, Any]]:
        """Filtra contratos por período."""
        result = []

        for contract in contracts:
            pub_date = contract.get("publication_date")
            if pub_date:
                try:
                    if isinstance(pub_date, str):
                        pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))

                    if start <= pub_date <= end:
                        result.append(contract)
                except (ValueError, TypeError):
                    pass

        return result

    def _filter_by_sector(
        self,
        contracts: List[Dict[str, Any]],
        sector: str
    ) -> List[Dict[str, Any]]:
        """Filtra contratos por sector."""
        keywords = self.SECTOR_KEYWORDS.get(sector, [])
        if not keywords:
            return []

        result = []
        for contract in contracts:
            text = self._get_contract_text(contract).lower()
            if any(kw in text for kw in keywords):
                result.append(contract)

        return result

    def _detect_sector(self, contract: Dict[str, Any]) -> str:
        """Detecta el sector de un contrato."""
        text = self._get_contract_text(contract).lower()

        scores = {}
        for sector, keywords in self.SECTOR_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[sector] = score

        if scores:
            return max(scores, key=scores.get)
        return "otros"

    def _count_by_field(
        self,
        contracts: List[Dict[str, Any]],
        field: str
    ) -> Dict[str, int]:
        """Cuenta contratos por campo."""
        counts = defaultdict(int)
        for contract in contracts:
            value = contract.get(field, "unknown") or "unknown"
            counts[value] += 1
        return dict(counts)

    def _get_contract_text(self, contract: Dict[str, Any]) -> str:
        """Obtiene texto completo del contrato."""
        parts = [
            contract.get("title", ""),
            contract.get("description", ""),
            contract.get("entity", "")
        ]
        return " ".join(filter(None, parts))

    def _analyze_sectors(
        self,
        contracts: List[Dict[str, Any]]
    ) -> Dict[str, SectorAnalysis]:
        """Analiza todos los sectores presentes."""
        sectors = {}

        for sector in self.SECTOR_KEYWORDS.keys():
            analysis = self.get_sector_insights(contracts, sector)
            if analysis.total_contracts > 0:
                sectors[sector] = analysis

        return sectors

    def _identify_trends(
        self,
        current_contracts: List[Dict[str, Any]],
        all_contracts: List[Dict[str, Any]]
    ) -> List[MarketTrend]:
        """Identifica tendencias del mercado."""
        trends = []

        # Tendencia 1: Digitalización
        tech_current = len(self._filter_by_sector(current_contracts, "tecnologia"))
        tech_ratio = tech_current / len(current_contracts) if current_contracts else 0

        if tech_ratio > 0.2:
            trends.append(MarketTrend(
                name="Transformación Digital",
                direction=TrendDirection.RISING,
                strength=min(100, tech_ratio * 300),
                description="Alto volumen de contratación en tecnología e innovación digital",
                evidence=[
                    f"{tech_current} contratos de tecnología en el período",
                    f"{tech_ratio*100:.1f}% del total de contratos"
                ],
                recommended_actions=[
                    "Fortalecer capacidades digitales",
                    "Considerar alianzas con empresas tech",
                    "Obtener certificaciones cloud (AWS, Azure)"
                ]
            ))

        # Tendencia 2: Sostenibilidad
        sustainability_keywords = ["sostenible", "ambiental", "renovable", "verde", "carbono"]
        sustainability_contracts = [
            c for c in current_contracts
            if any(kw in self._get_contract_text(c).lower() for kw in sustainability_keywords)
        ]

        if len(sustainability_contracts) > 5:
            trends.append(MarketTrend(
                name="Contratación Sostenible",
                direction=TrendDirection.RISING,
                strength=min(100, len(sustainability_contracts) * 10),
                description="Creciente énfasis en criterios ambientales y sostenibilidad",
                evidence=[
                    f"{len(sustainability_contracts)} contratos con criterios de sostenibilidad"
                ],
                recommended_actions=[
                    "Implementar políticas de sostenibilidad",
                    "Obtener certificación ISO 14001",
                    "Documentar huella de carbono"
                ]
            ))

        # Tendencia 3: Contratación de servicios vs bienes
        services_count = sum(
            1 for c in current_contracts
            if any(kw in self._get_contract_text(c).lower()
                   for kw in ["servicio", "consultoría", "asesoría"])
        )
        goods_count = sum(
            1 for c in current_contracts
            if any(kw in self._get_contract_text(c).lower()
                   for kw in ["suministro", "compra de", "adquisición de bienes"])
        )

        if services_count > goods_count * 1.5:
            trends.append(MarketTrend(
                name="Servicios sobre Bienes",
                direction=TrendDirection.STABLE,
                strength=70,
                description="Las entidades prefieren contratar servicios integrales sobre adquisición de bienes",
                evidence=[
                    f"{services_count} contratos de servicios vs {goods_count} de bienes"
                ],
                recommended_actions=[
                    "Desarrollar portafolio de servicios",
                    "Ofrecer soluciones integrales",
                    "Incluir componentes de servicio en ofertas de bienes"
                ]
            ))

        return trends

    def _analyze_competition(
        self,
        contracts: List[Dict[str, Any]]
    ) -> Dict[str, CompetitorInsight]:
        """Analiza la competencia por segmento."""
        insights = {}

        # Por fuente/tipo de contratación
        segments = {
            "secop_small": {
                "filter": lambda c: "secop" in (c.get("source", "") or "").lower()
                         and (c.get("amount", 0) or 0) < 100_000_000,
                "barrier": "low",
                "requirements": ["RUT", "Cámara de Comercio", "Antecedentes"],
                "factors": ["Precio competitivo", "Experiencia básica", "Disponibilidad"]
            },
            "secop_large": {
                "filter": lambda c: "secop" in (c.get("source", "") or "").lower()
                         and (c.get("amount", 0) or 0) >= 500_000_000,
                "barrier": "high",
                "requirements": ["Experiencia específica 5+ años", "Capacidad financiera",
                               "Certificaciones", "Equipo especializado"],
                "factors": ["Track record", "Capacidad técnica", "Solidez financiera"]
            },
            "multilateral": {
                "filter": lambda c: c.get("country") == "multilateral",
                "barrier": "high",
                "requirements": ["Registro en portales", "Experiencia internacional",
                               "Inglés", "Certificaciones internacionales"],
                "factors": ["Reputación", "Experiencia similar", "Propuesta técnica sólida"]
            }
        }

        for segment_name, config in segments.items():
            segment_contracts = [c for c in contracts if config["filter"](c)]

            if segment_contracts:
                # Estimar competidores basado en monto promedio
                avg_amount = sum(c.get("amount", 0) or 0 for c in segment_contracts) / len(segment_contracts)

                if avg_amount < 50_000_000:
                    estimated_competitors = 20
                elif avg_amount < 200_000_000:
                    estimated_competitors = 10
                elif avg_amount < 1_000_000_000:
                    estimated_competitors = 5
                else:
                    estimated_competitors = 3

                insights[segment_name] = CompetitorInsight(
                    segment=segment_name,
                    estimated_competitors=estimated_competitors,
                    barrier_to_entry=config["barrier"],
                    typical_requirements=config["requirements"],
                    success_factors=config["factors"]
                )

        return insights

    def _find_hot_opportunities(
        self,
        contracts: List[Dict[str, Any]],
        user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identifica oportunidades calientes para el usuario."""
        from intelligence.opportunity_scorer import get_opportunity_scorer

        scorer = get_opportunity_scorer()
        scored = scorer.score_batch(contracts, user_profile)

        # Top 10 oportunidades
        hot = []
        for contract, score in scored[:10]:
            if score.total_score >= 60:
                hot.append({
                    "contract": contract,
                    "score": score.total_score,
                    "tier": score.tier,
                    "recommendation": score.recommendation
                })

        return hot

    def _identify_emerging_sectors(
        self,
        current_contracts: List[Dict[str, Any]],
        all_contracts: List[Dict[str, Any]]
    ) -> List[str]:
        """Identifica sectores emergentes (crecimiento acelerado)."""
        emerging = []

        for sector in self.SECTOR_KEYWORDS.keys():
            growth = self._calculate_growth_rate(all_contracts, sector)
            if growth > 20:  # Crecimiento > 20%
                emerging.append(sector)

        return emerging

    def _calculate_growth_rate(
        self,
        contracts: List[Dict[str, Any]],
        sector: str
    ) -> float:
        """Calcula tasa de crecimiento de un sector."""
        now = datetime.now()

        # Período actual (30 días)
        current_start = now - timedelta(days=30)
        current = self._filter_by_period(
            self._filter_by_sector(contracts, sector),
            current_start, now
        )

        # Período anterior (30-60 días)
        previous_end = current_start
        previous_start = previous_end - timedelta(days=30)
        previous = self._filter_by_period(
            self._filter_by_sector(contracts, sector),
            previous_start, previous_end
        )

        if len(previous) == 0:
            return 100 if len(current) > 0 else 0

        return ((len(current) - len(previous)) / len(previous)) * 100

    def _calculate_change(self, previous: float, current: float) -> float:
        """Calcula cambio porcentual."""
        if previous == 0:
            return 100 if current > 0 else 0
        return ((current - previous) / previous) * 100

    def _get_top_entities(
        self,
        contracts: List[Dict[str, Any]],
        limit: int = 5
    ) -> List[Tuple[str, int]]:
        """Obtiene las entidades con más contratos."""
        entities = defaultdict(int)

        for contract in contracts:
            entity = contract.get("entity", "Unknown") or "Unknown"
            entities[entity] += 1

        sorted_entities = sorted(entities.items(), key=lambda x: x[1], reverse=True)
        return sorted_entities[:limit]

    def _get_top_keywords(
        self,
        contracts: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Tuple[str, int]]:
        """Extrae las palabras clave más frecuentes."""
        # Palabras a ignorar
        stopwords = {
            "de", "la", "el", "en", "y", "a", "los", "las", "del", "para",
            "con", "por", "se", "al", "que", "un", "una", "su", "como"
        }

        word_counts = defaultdict(int)

        for contract in contracts:
            text = self._get_contract_text(contract).lower()
            words = text.split()

            for word in words:
                # Limpiar palabra
                word = ''.join(c for c in word if c.isalnum())
                if len(word) > 3 and word not in stopwords:
                    word_counts[word] += 1

        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_words[:limit]

    def _estimate_competition(self, contracts: List[Dict[str, Any]]) -> str:
        """Estima nivel de competencia basado en contratos."""
        if not contracts:
            return "unknown"

        avg_amount = sum(c.get("amount", 0) or 0 for c in contracts) / len(contracts)

        if avg_amount < 50_000_000:
            return "very_high"
        elif avg_amount < 200_000_000:
            return "high"
        elif avg_amount < 1_000_000_000:
            return "moderate"
        else:
            return "low"

    def _rate_sector_opportunity(self, contracts: List[Dict[str, Any]]) -> float:
        """Califica oportunidad del sector (0-100)."""
        if not contracts:
            return 0

        score = 50.0  # Base

        # Más contratos = más oportunidades
        if len(contracts) > 50:
            score += 15
        elif len(contracts) > 20:
            score += 10
        elif len(contracts) > 10:
            score += 5

        # Valor total alto = sector activo
        total_value = sum(c.get("amount", 0) or 0 for c in contracts)
        if total_value > 10_000_000_000:
            score += 15
        elif total_value > 1_000_000_000:
            score += 10

        # Diversidad de entidades = no monopolizado
        entities = set(c.get("entity", "") for c in contracts)
        if len(entities) > 10:
            score += 10
        elif len(entities) > 5:
            score += 5

        return min(100, score)

    def _estimate_frequency(self, dates: List) -> str:
        """Estima frecuencia de contratación."""
        if len(dates) < 2:
            return "insufficient_data"

        # Ordenar fechas
        sorted_dates = sorted([
            d if isinstance(d, datetime) else datetime.fromisoformat(str(d))
            for d in dates if d
        ])

        if len(sorted_dates) < 2:
            return "insufficient_data"

        # Calcular intervalo promedio
        intervals = [
            (sorted_dates[i+1] - sorted_dates[i]).days
            for i in range(len(sorted_dates) - 1)
        ]

        avg_interval = sum(intervals) / len(intervals)

        if avg_interval <= 7:
            return "weekly"
        elif avg_interval <= 30:
            return "monthly"
        elif avg_interval <= 90:
            return "quarterly"
        else:
            return "sporadic"

    def _generate_alerts(self, report: MarketReport) -> List[str]:
        """Genera alertas basadas en el análisis."""
        alerts = []

        # Alerta de sector caliente
        for sector, analysis in report.sector_analyses.items():
            if analysis.growth_rate > 30:
                alerts.append(
                    f"🔥 Sector {sector} creciendo {analysis.growth_rate:.0f}% - "
                    f"Oportunidad de expansión"
                )

        # Alerta de tendencias
        for trend in report.trends:
            if trend.direction == TrendDirection.RISING and trend.strength > 70:
                alerts.append(f"📈 Tendencia fuerte: {trend.name}")

        # Alerta de competencia baja
        for segment, insight in report.competitor_insights.items():
            if insight.estimated_competitors < 5:
                alerts.append(
                    f"🎯 Baja competencia en {segment} - "
                    f"Estimados {insight.estimated_competitors} competidores"
                )

        return alerts


# Singleton
_market_analyzer = None


def get_market_analyzer() -> MarketAnalyzer:
    """Obtiene la instancia singleton del analizador."""
    global _market_analyzer
    if _market_analyzer is None:
        _market_analyzer = MarketAnalyzer()
    return _market_analyzer
