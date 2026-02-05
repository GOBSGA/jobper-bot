"""
Contract Intelligence Engine
Análisis profundo de contratos usando NLP avanzado y heurísticas de negocio.

Este módulo es el cerebro de Jobper - extrae información estructurada,
detecta oportunidades ocultas, y genera insights accionables.
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ContractType(str, Enum):
    """Tipos de contrato detectados."""
    GOODS = "goods"                      # Compra de bienes
    SERVICES = "services"                # Servicios profesionales
    CONSTRUCTION = "construction"        # Obra civil
    CONSULTING = "consulting"            # Consultoría
    IT_DEVELOPMENT = "it_development"    # Desarrollo de software
    IT_INFRASTRUCTURE = "it_infra"       # Infraestructura TI
    MAINTENANCE = "maintenance"          # Mantenimiento
    TRAINING = "training"                # Capacitación
    RESEARCH = "research"                # Investigación
    MIXED = "mixed"                      # Múltiples tipos
    UNKNOWN = "unknown"


class ContractComplexity(str, Enum):
    """Nivel de complejidad del contrato."""
    SIMPLE = "simple"           # < 5 requisitos, 1 entregable
    MODERATE = "moderate"       # 5-15 requisitos
    COMPLEX = "complex"         # 15+ requisitos, múltiples fases
    HIGHLY_COMPLEX = "highly_complex"  # Multidisciplinario, consorcio requerido


class CompetitionLevel(str, Enum):
    """Nivel de competencia esperado."""
    LOW = "low"           # Pocos competidores esperados
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class ContractRequirement:
    """Requisito extraído de un contrato."""
    type: str                    # "experience", "certification", "financial", "technical", "legal"
    description: str
    is_mandatory: bool = True
    years_required: Optional[int] = None
    amount_required: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContractInsight:
    """Insight generado sobre un contrato."""
    type: str                    # "opportunity", "risk", "recommendation", "market"
    title: str
    description: str
    importance: int              # 1-5, donde 5 es crítico
    action_items: List[str] = field(default_factory=list)


@dataclass
class ContractAnalysis:
    """Análisis completo de un contrato."""
    # Identificación
    contract_id: str
    analyzed_at: datetime

    # Clasificación
    contract_type: ContractType
    complexity: ContractComplexity
    competition_level: CompetitionLevel

    # Información extraída
    estimated_duration_days: Optional[int] = None
    requires_consortium: bool = False
    allows_foreign_companies: bool = True
    requires_local_presence: bool = False

    # Requisitos estructurados
    requirements: List[ContractRequirement] = field(default_factory=list)
    min_experience_years: Optional[int] = None
    min_financial_capacity: Optional[float] = None
    certifications_required: List[str] = field(default_factory=list)

    # Keywords y entidades extraídas
    key_technologies: List[str] = field(default_factory=list)
    key_deliverables: List[str] = field(default_factory=list)
    mentioned_standards: List[str] = field(default_factory=list)

    # Scoring
    opportunity_score: float = 0.0      # 0-100
    fit_score: float = 0.0              # 0-100 (vs perfil usuario)
    win_probability: float = 0.0        # 0-100

    # Insights
    insights: List[ContractInsight] = field(default_factory=list)

    # Resumen ejecutivo
    executive_summary: str = ""
    recommended_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return {
            "contract_id": self.contract_id,
            "analyzed_at": self.analyzed_at.isoformat(),
            "contract_type": self.contract_type.value,
            "complexity": self.complexity.value,
            "competition_level": self.competition_level.value,
            "estimated_duration_days": self.estimated_duration_days,
            "requires_consortium": self.requires_consortium,
            "requirements_count": len(self.requirements),
            "min_experience_years": self.min_experience_years,
            "min_financial_capacity": self.min_financial_capacity,
            "certifications_required": self.certifications_required,
            "key_technologies": self.key_technologies,
            "opportunity_score": self.opportunity_score,
            "fit_score": self.fit_score,
            "win_probability": self.win_probability,
            "insights_count": len(self.insights),
            "executive_summary": self.executive_summary,
            "recommended_action": self.recommended_action
        }


class ContractIntelligence:
    """
    Motor de inteligencia para análisis profundo de contratos.

    Extrae información estructurada de texto no estructurado,
    clasifica contratos, detecta requisitos, y genera insights.
    """

    # Patrones para detección de tipos de contrato
    TYPE_PATTERNS = {
        ContractType.IT_DEVELOPMENT: [
            r"desarrollo\s+de\s+software", r"aplicaci[oó]n\s+m[oó]vil", r"sistema\s+de\s+informaci[oó]n",
            r"plataforma\s+digital", r"software\s+a\s+la\s+medida", r"desarrollo\s+web",
            r"app\s+m[oó]vil", r"api\s+rest", r"microservicios", r"software\s+development"
        ],
        ContractType.IT_INFRASTRUCTURE: [
            r"infraestructura\s+tecnol[oó]gica", r"data\s*center", r"servidores",
            r"redes\s+y\s+comunicaciones", r"ciberseguridad", r"cloud", r"nube",
            r"hosting", r"backup", r"disaster\s+recovery"
        ],
        ContractType.CONSTRUCTION: [
            r"construcci[oó]n", r"obra\s+civil", r"edificaci[oó]n", r"infraestructura\s+f[ií]sica",
            r"remodelaci[oó]n", r"adecuaci[oó]n", r"mantenimiento\s+locativo",
            r"v[ií]as", r"acueducto", r"alcantarillado"
        ],
        ContractType.CONSULTING: [
            r"consultor[ií]a", r"asesor[ií]a", r"estudio\s+de", r"diagn[oó]stico",
            r"evaluaci[oó]n", r"interventor[ií]a", r"auditor[ií]a", r"an[aá]lisis"
        ],
        ContractType.GOODS: [
            r"suministro", r"compra\s+de", r"adquisici[oó]n", r"provisi[oó]n",
            r"dotaci[oó]n", r"equipos", r"materiales", r"insumos"
        ],
        ContractType.SERVICES: [
            r"prestaci[oó]n\s+de\s+servicios", r"servicio\s+de", r"operaci[oó]n",
            r"soporte", r"mesa\s+de\s+ayuda", r"outsourcing"
        ],
        ContractType.TRAINING: [
            r"capacitaci[oó]n", r"formaci[oó]n", r"entrenamiento", r"taller",
            r"diplomado", r"curso", r"seminario"
        ],
        ContractType.MAINTENANCE: [
            r"mantenimiento\s+preventivo", r"mantenimiento\s+correctivo",
            r"soporte\s+t[eé]cnico", r"garant[ií]a\s+extendida"
        ],
        ContractType.RESEARCH: [
            r"investigaci[oó]n", r"estudio\s+cient[ií]fico", r"i\+d",
            r"innovaci[oó]n", r"desarrollo\s+experimental"
        ]
    }

    # Patrones para requisitos
    REQUIREMENT_PATTERNS = {
        "experience": [
            r"experiencia\s+(?:m[ií]nima\s+)?(?:de\s+)?(\d+)\s+a[ñn]os?",
            r"(\d+)\s+a[ñn]os?\s+de\s+experiencia",
            r"experiencia\s+espec[ií]fica\s+en",
            r"haber\s+ejecutado\s+(?:al\s+menos\s+)?(\d+)\s+contratos?"
        ],
        "financial": [
            r"capacidad\s+financiera",
            r"patrimonio\s+(?:l[ií]quido\s+)?(?:m[ií]nimo\s+)?(?:de\s+)?\$?\s*([\d.,]+)",
            r"capital\s+de\s+trabajo",
            r"facturaci[oó]n\s+(?:anual\s+)?(?:m[ií]nima\s+)?(?:de\s+)?\$?\s*([\d.,]+)"
        ],
        "certification": [
            r"certificaci[oó]n\s+(?:en\s+)?iso\s*(\d+)",
            r"certificado\s+(?:en\s+)?(pmp|scrum|itil|cobit)",
            r"registro\s+(?:nacional\s+)?de\s+consultores",
            r"tarjeta\s+profesional"
        ],
        "legal": [
            r"rut\s+actualizado",
            r"c[aá]mara\s+de\s+comercio",
            r"antecedentes\s+(?:disciplinarios|fiscales|judiciales)",
            r"paz\s+y\s+salvo"
        ],
        "consortium": [
            r"consorcio", r"uni[oó]n\s+temporal", r"asociaci[oó]n",
            r"se\s+permite\s+(?:la\s+)?participaci[oó]n\s+conjunta"
        ]
    }

    # Patrones para tecnologías
    TECHNOLOGY_PATTERNS = [
        r"python", r"java(?:script)?", r"\.net", r"node\.?js", r"react", r"angular", r"vue",
        r"aws", r"azure", r"google\s+cloud", r"gcp", r"kubernetes", r"docker",
        r"postgresql", r"mysql", r"oracle", r"sql\s+server", r"mongodb",
        r"power\s*bi", r"tableau", r"sap", r"oracle\s+erp", r"dynamics",
        r"cisco", r"fortinet", r"palo\s+alto", r"vmware",
        r"agile", r"scrum", r"devops", r"ci/cd"
    ]

    # Estándares y certificaciones comunes
    STANDARDS_PATTERNS = [
        r"iso\s*\d+", r"cmmi", r"itil", r"cobit", r"pmi", r"pmbok",
        r"owasp", r"gdpr", r"habeas\s+data", r"ley\s+\d+",
        r"nist", r"soc\s*[12]", r"hipaa"
    ]

    def __init__(self):
        """Inicializa el motor de inteligencia."""
        # Compilar patrones para eficiencia
        self._type_patterns = {
            t: [re.compile(p, re.IGNORECASE) for p in patterns]
            for t, patterns in self.TYPE_PATTERNS.items()
        }
        self._req_patterns = {
            t: [re.compile(p, re.IGNORECASE) for p in patterns]
            for t, patterns in self.REQUIREMENT_PATTERNS.items()
        }
        self._tech_patterns = [re.compile(p, re.IGNORECASE) for p in self.TECHNOLOGY_PATTERNS]
        self._std_patterns = [re.compile(p, re.IGNORECASE) for p in self.STANDARDS_PATTERNS]

        logger.info("ContractIntelligence inicializado")

    def analyze(
        self,
        contract: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None
    ) -> ContractAnalysis:
        """
        Realiza análisis completo de un contrato.

        Args:
            contract: Datos del contrato
            user_profile: Perfil del usuario para calcular fit_score

        Returns:
            ContractAnalysis con toda la información extraída
        """
        text = self._get_full_text(contract)
        contract_id = contract.get("external_id", contract.get("id", "unknown"))

        # Crear análisis base
        analysis = ContractAnalysis(
            contract_id=str(contract_id),
            analyzed_at=datetime.now(),
            contract_type=self._detect_contract_type(text),
            complexity=ContractComplexity.MODERATE,  # Se actualiza después
            competition_level=CompetitionLevel.MODERATE  # Se actualiza después
        )

        # Extraer requisitos
        analysis.requirements = self._extract_requirements(text)
        analysis.min_experience_years = self._extract_min_experience(text)
        analysis.min_financial_capacity = self._extract_min_financial(contract, text)
        analysis.certifications_required = self._extract_certifications(text)

        # Extraer información técnica
        analysis.key_technologies = self._extract_technologies(text)
        analysis.mentioned_standards = self._extract_standards(text)
        analysis.key_deliverables = self._extract_deliverables(text)

        # Detectar características especiales
        analysis.requires_consortium = self._detect_consortium_requirement(text, contract)
        analysis.allows_foreign_companies = self._detect_foreign_allowed(text)
        analysis.requires_local_presence = self._detect_local_presence(text)
        analysis.estimated_duration_days = self._estimate_duration(contract, text)

        # Calcular complejidad y competencia
        analysis.complexity = self._calculate_complexity(analysis, contract)
        analysis.competition_level = self._calculate_competition(analysis, contract)

        # Calcular scores
        analysis.opportunity_score = self._calculate_opportunity_score(analysis, contract)

        if user_profile:
            analysis.fit_score = self._calculate_fit_score(analysis, contract, user_profile)
            analysis.win_probability = self._calculate_win_probability(analysis, user_profile)

        # Generar insights
        analysis.insights = self._generate_insights(analysis, contract, user_profile)

        # Generar resumen ejecutivo
        analysis.executive_summary = self._generate_executive_summary(analysis, contract)
        analysis.recommended_action = self._generate_recommendation(analysis, user_profile)

        return analysis

    def _get_full_text(self, contract: Dict[str, Any]) -> str:
        """Combina todo el texto relevante del contrato."""
        parts = [
            contract.get("title", ""),
            contract.get("description", ""),
            contract.get("entity", ""),
            str(contract.get("raw_data", {}).get("objeto", "")),
            str(contract.get("raw_data", {}).get("requirements", "")),
        ]
        return " ".join(filter(None, parts)).lower()

    def _detect_contract_type(self, text: str) -> ContractType:
        """Detecta el tipo de contrato basado en patrones."""
        scores = {}

        for contract_type, patterns in self._type_patterns.items():
            score = sum(1 for p in patterns if p.search(text))
            if score > 0:
                scores[contract_type] = score

        if not scores:
            return ContractType.UNKNOWN

        # Si hay múltiples tipos con score alto, es mixto
        max_score = max(scores.values())
        high_scores = [t for t, s in scores.items() if s >= max_score * 0.8]

        if len(high_scores) > 1:
            return ContractType.MIXED

        return max(scores, key=scores.get)

    def _extract_requirements(self, text: str) -> List[ContractRequirement]:
        """Extrae requisitos estructurados del texto."""
        requirements = []

        for req_type, patterns in self._req_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(text)
                for match in matches:
                    req = ContractRequirement(
                        type=req_type,
                        description=match.group(0),
                        is_mandatory=True
                    )

                    # Extraer valores numéricos si aplica
                    groups = match.groups()
                    if groups:
                        try:
                            value = groups[0].replace(",", "").replace(".", "")
                            if req_type == "experience":
                                req.years_required = int(value)
                            elif req_type == "financial":
                                req.amount_required = float(value)
                        except (ValueError, TypeError):
                            pass

                    requirements.append(req)

        return requirements

    def _extract_min_experience(self, text: str) -> Optional[int]:
        """Extrae años mínimos de experiencia requeridos."""
        patterns = [
            r"experiencia\s+(?:m[ií]nima\s+)?(?:de\s+)?(\d+)\s+a[ñn]os?",
            r"(\d+)\s+a[ñn]os?\s+de\s+experiencia",
            r"m[ií]nimo\s+(\d+)\s+a[ñn]os?"
        ]

        max_years = 0
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    years = int(match)
                    max_years = max(max_years, years)
                except ValueError:
                    pass

        return max_years if max_years > 0 else None

    def _extract_min_financial(self, contract: Dict[str, Any], text: str) -> Optional[float]:
        """Extrae capacidad financiera mínima requerida."""
        # Primero intentar del monto del contrato (regla general: 10-30% como capacidad)
        amount = contract.get("amount")
        if amount and amount > 0:
            return amount * 0.2  # 20% del valor como estimado

        # Buscar en el texto
        patterns = [
            r"patrimonio\s+(?:l[ií]quido\s+)?(?:m[ií]nimo\s+)?(?:de\s+)?\$?\s*([\d.,]+)",
            r"capital\s+(?:de\s+trabajo\s+)?(?:m[ií]nimo\s+)?(?:de\s+)?\$?\s*([\d.,]+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = match.group(1).replace(",", "").replace(".", "")
                    return float(value)
                except ValueError:
                    pass

        return None

    def _extract_certifications(self, text: str) -> List[str]:
        """Extrae certificaciones requeridas."""
        certs = set()

        cert_patterns = [
            (r"iso\s*(\d+)", "ISO {}"),
            (r"certificaci[oó]n\s+(?:en\s+)?(pmp|scrum|itil|cobit|aws|azure)", "{}"),
            (r"(cmmi)\s*nivel\s*(\d+)", "CMMI Nivel {}"),
        ]

        for pattern, template in cert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    cert = template.format(*match).upper()
                else:
                    cert = template.format(match).upper()
                certs.add(cert)

        return list(certs)

    def _extract_technologies(self, text: str) -> List[str]:
        """Extrae tecnologías mencionadas."""
        techs = set()

        for pattern in self._tech_patterns:
            matches = pattern.findall(text)
            for match in matches:
                techs.add(match.upper())

        return list(techs)

    def _extract_standards(self, text: str) -> List[str]:
        """Extrae estándares mencionados."""
        standards = set()

        for pattern in self._std_patterns:
            matches = pattern.findall(text)
            for match in matches:
                standards.add(match.upper())

        return list(standards)

    def _extract_deliverables(self, text: str) -> List[str]:
        """Extrae entregables principales."""
        deliverables = []

        patterns = [
            r"entrega(?:r|ble)?\s+(?:de\s+)?([^.,;]+)",
            r"producto\s+(?:final\s+)?([^.,;]+)",
            r"resultado\s+(?:esperado\s+)?([^.,;]+)"
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) > 10 and len(match) < 100:
                    deliverables.append(match.strip())

        return deliverables[:5]  # Máximo 5 entregables principales

    def _detect_consortium_requirement(self, text: str, contract: Dict[str, Any]) -> bool:
        """Detecta si se requiere o permite consorcio."""
        amount = contract.get("amount", 0) or 0

        # Contratos muy grandes típicamente requieren consorcio
        if amount > 5_000_000_000:  # > 5 mil millones COP
            return True

        patterns = [
            r"consorcio", r"uni[oó]n\s+temporal",
            r"se\s+permite\s+(?:la\s+)?participaci[oó]n\s+conjunta",
            r"propuestas?\s+conjuntas?"
        ]

        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    def _detect_foreign_allowed(self, text: str) -> bool:
        """Detecta si se permiten empresas extranjeras."""
        # Por defecto se permiten, buscar restricciones
        restriction_patterns = [
            r"solo\s+empresas?\s+colombianas?",
            r"exclusivamente\s+nacional",
            r"personas?\s+jur[ií]dicas?\s+colombianas?"
        ]

        return not any(re.search(p, text, re.IGNORECASE) for p in restriction_patterns)

    def _detect_local_presence(self, text: str) -> bool:
        """Detecta si se requiere presencia local."""
        patterns = [
            r"domicilio\s+en\s+la\s+ciudad",
            r"presencia\s+(?:f[ií]sica\s+)?en",
            r"oficina\s+(?:en\s+)?(?:la\s+)?ciudad",
            r"sede\s+(?:principal\s+)?en"
        ]

        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    def _estimate_duration(self, contract: Dict[str, Any], text: str) -> Optional[int]:
        """Estima la duración del contrato en días."""
        # Buscar duración explícita
        patterns = [
            (r"(\d+)\s*meses?", 30),
            (r"(\d+)\s*d[ií]as?", 1),
            (r"(\d+)\s*semanas?", 7),
            (r"(\d+)\s*a[ñn]os?", 365)
        ]

        for pattern, multiplier in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1)) * multiplier
                except ValueError:
                    pass

        # Estimar basado en deadline
        deadline = contract.get("deadline")
        pub_date = contract.get("publication_date")

        if deadline and pub_date:
            try:
                if isinstance(deadline, str):
                    deadline = datetime.fromisoformat(deadline)
                if isinstance(pub_date, str):
                    pub_date = datetime.fromisoformat(pub_date)

                return (deadline - pub_date).days
            except (ValueError, TypeError):
                pass

        return None

    def _calculate_complexity(
        self,
        analysis: ContractAnalysis,
        contract: Dict[str, Any]
    ) -> ContractComplexity:
        """Calcula el nivel de complejidad del contrato."""
        score = 0

        # Por cantidad de requisitos
        req_count = len(analysis.requirements)
        if req_count > 20:
            score += 3
        elif req_count > 10:
            score += 2
        elif req_count > 5:
            score += 1

        # Por monto
        amount = contract.get("amount", 0) or 0
        if amount > 10_000_000_000:  # > 10 mil millones
            score += 3
        elif amount > 1_000_000_000:  # > 1 mil millones
            score += 2
        elif amount > 100_000_000:  # > 100 millones
            score += 1

        # Por certificaciones requeridas
        if len(analysis.certifications_required) > 3:
            score += 2
        elif len(analysis.certifications_required) > 0:
            score += 1

        # Por duración
        if analysis.estimated_duration_days:
            if analysis.estimated_duration_days > 365:
                score += 2
            elif analysis.estimated_duration_days > 180:
                score += 1

        # Por tecnologías
        if len(analysis.key_technologies) > 5:
            score += 1

        # Determinar nivel
        if score >= 8:
            return ContractComplexity.HIGHLY_COMPLEX
        elif score >= 5:
            return ContractComplexity.COMPLEX
        elif score >= 2:
            return ContractComplexity.MODERATE
        return ContractComplexity.SIMPLE

    def _calculate_competition(
        self,
        analysis: ContractAnalysis,
        contract: Dict[str, Any]
    ) -> CompetitionLevel:
        """Estima el nivel de competencia esperado."""
        score = 0
        amount = contract.get("amount", 0) or 0

        # Contratos pequeños = más competencia
        if amount < 50_000_000:  # < 50 millones
            score += 2
        elif amount < 500_000_000:  # < 500 millones
            score += 1

        # Requisitos bajos = más competencia
        if analysis.min_experience_years is None or analysis.min_experience_years < 3:
            score += 2
        elif analysis.min_experience_years < 5:
            score += 1

        # Sin certificaciones = más competencia
        if not analysis.certifications_required:
            score += 1

        # Tipo común = más competencia
        common_types = [ContractType.SERVICES, ContractType.GOODS, ContractType.MAINTENANCE]
        if analysis.contract_type in common_types:
            score += 1

        # Fuente popular = más competencia
        source = contract.get("source", "").lower()
        if "secop" in source:
            score += 1

        if score >= 5:
            return CompetitionLevel.VERY_HIGH
        elif score >= 3:
            return CompetitionLevel.HIGH
        elif score >= 2:
            return CompetitionLevel.MODERATE
        return CompetitionLevel.LOW

    def _calculate_opportunity_score(
        self,
        analysis: ContractAnalysis,
        contract: Dict[str, Any]
    ) -> float:
        """Calcula score de oportunidad (qué tan buena es la oportunidad)."""
        score = 50.0  # Base

        amount = contract.get("amount", 0) or 0

        # Ajustar por monto (más es mejor, hasta un punto)
        if amount > 0:
            if amount > 1_000_000_000:
                score += 15
            elif amount > 500_000_000:
                score += 10
            elif amount > 100_000_000:
                score += 5

        # Ajustar por competencia (menos es mejor)
        if analysis.competition_level == CompetitionLevel.LOW:
            score += 15
        elif analysis.competition_level == CompetitionLevel.MODERATE:
            score += 5
        elif analysis.competition_level == CompetitionLevel.VERY_HIGH:
            score -= 10

        # Ajustar por deadline (más tiempo es mejor)
        deadline = contract.get("deadline")
        if deadline:
            try:
                if isinstance(deadline, str):
                    deadline = datetime.fromisoformat(deadline)
                days_left = (deadline - datetime.now()).days

                if days_left > 30:
                    score += 10
                elif days_left > 14:
                    score += 5
                elif days_left < 3:
                    score -= 15
            except (ValueError, TypeError):
                pass

        # Ajustar por complejidad (simple es más accesible)
        if analysis.complexity == ContractComplexity.SIMPLE:
            score += 5
        elif analysis.complexity == ContractComplexity.HIGHLY_COMPLEX:
            score -= 5

        return max(0, min(100, score))

    def _calculate_fit_score(
        self,
        analysis: ContractAnalysis,
        contract: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> float:
        """Calcula qué tan bien encaja el usuario con el contrato."""
        score = 0.0
        factors = 0

        # Match de industria
        user_industry = user_profile.get("industry", "")
        if user_industry:
            factors += 1
            industry_types = {
                "tecnologia": [ContractType.IT_DEVELOPMENT, ContractType.IT_INFRASTRUCTURE],
                "construccion": [ContractType.CONSTRUCTION, ContractType.MAINTENANCE],
                "consultoria": [ContractType.CONSULTING, ContractType.RESEARCH],
                "logistica": [ContractType.GOODS, ContractType.SERVICES],
            }

            matching_types = industry_types.get(user_industry, [])
            if analysis.contract_type in matching_types:
                score += 30
            elif analysis.contract_type == ContractType.MIXED:
                score += 15

        # Match de keywords
        user_keywords = set(kw.lower() for kw in user_profile.get("include_keywords", []))
        if user_keywords:
            factors += 1
            text = self._get_full_text(contract)
            matches = sum(1 for kw in user_keywords if kw in text)
            if matches > 0:
                match_ratio = matches / len(user_keywords)
                score += 30 * match_ratio

        # Match de presupuesto
        min_budget = user_profile.get("min_budget")
        max_budget = user_profile.get("max_budget")
        amount = contract.get("amount", 0) or 0

        if amount > 0 and (min_budget or max_budget):
            factors += 1
            in_range = True
            if min_budget and amount < min_budget:
                in_range = False
            if max_budget and amount > max_budget:
                in_range = False

            if in_range:
                score += 20

        # Match de país
        user_countries = user_profile.get("countries", "all")
        contract_country = contract.get("country", "")

        if user_countries != "all":
            factors += 1
            if contract_country == user_countries:
                score += 20
            elif user_countries == "both" and contract_country in ["colombia", "usa"]:
                score += 20

        if factors == 0:
            return 50.0  # Sin información, score neutral

        return max(0, min(100, score * (4 / factors)))  # Normalizar a 100

    def _calculate_win_probability(
        self,
        analysis: ContractAnalysis,
        user_profile: Dict[str, Any]
    ) -> float:
        """
        Estima la probabilidad de ganar el contrato.

        Esta es una estimación heurística basada en factores conocidos.
        """
        base_probability = 20.0  # Probabilidad base en licitación pública

        # Ajustar por competencia
        if analysis.competition_level == CompetitionLevel.LOW:
            base_probability += 25
        elif analysis.competition_level == CompetitionLevel.MODERATE:
            base_probability += 10
        elif analysis.competition_level == CompetitionLevel.VERY_HIGH:
            base_probability -= 10

        # Ajustar por fit_score
        if analysis.fit_score >= 80:
            base_probability += 15
        elif analysis.fit_score >= 60:
            base_probability += 5

        # Ajustar por complejidad (nichos tienen menos competencia)
        if analysis.complexity == ContractComplexity.HIGHLY_COMPLEX:
            base_probability += 10
        elif analysis.complexity == ContractComplexity.COMPLEX:
            base_probability += 5

        # Penalizar si requiere consorcio y el usuario es pequeño
        # (asumiendo que usuarios pequeños no tienen para consorcio)
        if analysis.requires_consortium:
            base_probability -= 10

        return max(5, min(80, base_probability))  # Entre 5% y 80%

    def _generate_insights(
        self,
        analysis: ContractAnalysis,
        contract: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]]
    ) -> List[ContractInsight]:
        """Genera insights accionables sobre el contrato."""
        insights = []

        # Insight de deadline urgente
        deadline = contract.get("deadline")
        if deadline:
            try:
                if isinstance(deadline, str):
                    deadline = datetime.fromisoformat(deadline)
                days_left = (deadline - datetime.now()).days

                if days_left <= 3:
                    insights.append(ContractInsight(
                        type="risk",
                        title="Deadline Crítico",
                        description=f"Solo quedan {days_left} días para presentar propuesta",
                        importance=5,
                        action_items=[
                            "Verificar si tienes toda la documentación lista",
                            "Considerar si es viable participar con tan poco tiempo"
                        ]
                    ))
                elif days_left <= 7:
                    insights.append(ContractInsight(
                        type="recommendation",
                        title="Actuar Pronto",
                        description=f"Quedan {days_left} días - tiempo justo para preparar propuesta",
                        importance=4,
                        action_items=[
                            "Iniciar preparación de documentos hoy",
                            "Revisar requisitos en detalle"
                        ]
                    ))
            except (ValueError, TypeError):
                pass

        # Insight de oportunidad de nicho
        if analysis.competition_level == CompetitionLevel.LOW:
            insights.append(ContractInsight(
                type="opportunity",
                title="Baja Competencia Esperada",
                description="Este contrato tiene requisitos específicos que reducen la competencia",
                importance=4,
                action_items=[
                    "Asegurarte de cumplir todos los requisitos específicos",
                    "Destacar tu experiencia diferenciadora"
                ]
            ))

        # Insight de consorcio
        if analysis.requires_consortium:
            insights.append(ContractInsight(
                type="recommendation",
                title="Considerar Consorcio",
                description="Por el tamaño o complejidad, un consorcio podría ser necesario",
                importance=3,
                action_items=[
                    "Identificar posibles socios complementarios",
                    "Evaluar división de responsabilidades"
                ]
            ))

        # Insight de certificaciones
        if analysis.certifications_required:
            certs = ", ".join(analysis.certifications_required[:3])
            insights.append(ContractInsight(
                type="risk" if len(analysis.certifications_required) > 2 else "recommendation",
                title="Certificaciones Requeridas",
                description=f"Se requieren: {certs}",
                importance=4,
                action_items=[
                    "Verificar que tienes las certificaciones vigentes",
                    "Adjuntar copias actualizadas en la propuesta"
                ]
            ))

        # Insight de tecnologías
        if analysis.key_technologies:
            techs = ", ".join(analysis.key_technologies[:5])
            insights.append(ContractInsight(
                type="market",
                title="Stack Tecnológico",
                description=f"Tecnologías mencionadas: {techs}",
                importance=2,
                action_items=[
                    "Destacar experiencia con estas tecnologías",
                    "Incluir casos de éxito relevantes"
                ]
            ))

        # Insight de monto alto
        amount = contract.get("amount", 0) or 0
        if amount > 1_000_000_000:
            insights.append(ContractInsight(
                type="opportunity",
                title="Contrato de Alto Valor",
                description=f"Monto superior a $1.000M - alta rentabilidad potencial",
                importance=4,
                action_items=[
                    "Evaluar capacidad financiera requerida",
                    "Considerar garantías necesarias"
                ]
            ))

        return sorted(insights, key=lambda x: x.importance, reverse=True)

    def _generate_executive_summary(
        self,
        analysis: ContractAnalysis,
        contract: Dict[str, Any]
    ) -> str:
        """Genera un resumen ejecutivo del análisis."""
        parts = []

        # Tipo y complejidad
        type_names = {
            ContractType.IT_DEVELOPMENT: "Desarrollo de Software",
            ContractType.IT_INFRASTRUCTURE: "Infraestructura TI",
            ContractType.CONSTRUCTION: "Construcción",
            ContractType.CONSULTING: "Consultoría",
            ContractType.GOODS: "Suministro de Bienes",
            ContractType.SERVICES: "Servicios",
            ContractType.TRAINING: "Capacitación",
            ContractType.MAINTENANCE: "Mantenimiento",
            ContractType.RESEARCH: "Investigación",
            ContractType.MIXED: "Mixto",
            ContractType.UNKNOWN: "No clasificado"
        }

        parts.append(f"Contrato de {type_names.get(analysis.contract_type, 'tipo desconocido')}")
        parts.append(f"con complejidad {analysis.complexity.value}")

        # Monto
        amount = contract.get("amount")
        if amount:
            if amount >= 1_000_000_000:
                amount_str = f"${amount/1_000_000_000:.1f} mil millones"
            elif amount >= 1_000_000:
                amount_str = f"${amount/1_000_000:.0f} millones"
            else:
                amount_str = f"${amount:,.0f}"
            parts.append(f"por {amount_str} {contract.get('currency', 'COP')}")

        # Competencia
        comp_text = {
            CompetitionLevel.LOW: "Se espera baja competencia",
            CompetitionLevel.MODERATE: "Competencia moderada esperada",
            CompetitionLevel.HIGH: "Alta competencia esperada",
            CompetitionLevel.VERY_HIGH: "Muy alta competencia esperada"
        }
        parts.append(comp_text.get(analysis.competition_level, ""))

        return ". ".join(parts) + "."

    def _generate_recommendation(
        self,
        analysis: ContractAnalysis,
        user_profile: Optional[Dict[str, Any]]
    ) -> str:
        """Genera recomendación de acción."""
        if analysis.win_probability >= 40 and analysis.fit_score >= 70:
            return "ALTA PRIORIDAD: Este contrato tiene buen fit con tu perfil y probabilidad razonable de ganar. Recomendamos participar."

        if analysis.win_probability >= 30 and analysis.fit_score >= 50:
            return "EVALUAR: El contrato tiene potencial pero revisa los requisitos específicos antes de decidir."

        if analysis.opportunity_score >= 70 and analysis.fit_score < 50:
            return "OPORTUNIDAD DE EXPANSIÓN: Buen contrato pero fuera de tu perfil actual. Considera si quieres expandir a este sector."

        if analysis.competition_level == CompetitionLevel.VERY_HIGH:
            return "ALTA COMPETENCIA: Participa solo si tienes un diferenciador claro o precios muy competitivos."

        return "REVISAR: Evalúa los requisitos detalladamente antes de decidir si participar."


# Singleton
_intelligence_engine = None


def get_contract_intelligence() -> ContractIntelligence:
    """Obtiene la instancia singleton del motor de inteligencia."""
    global _intelligence_engine
    if _intelligence_engine is None:
        _intelligence_engine = ContractIntelligence()
    return _intelligence_engine
