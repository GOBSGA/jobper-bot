"""
Contract Normalizer
Sistema de normalización de contratos de múltiples fuentes.

Transforma datos crudos de diferentes fuentes a un formato
común y enriquecido para procesamiento uniforme.
"""
from __future__ import annotations

import re
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class NormalizationQuality(str, Enum):
    """Calidad de la normalización."""
    HIGH = "high"           # Todos los campos principales
    MEDIUM = "medium"       # Campos básicos
    LOW = "low"             # Solo título y fuente
    INCOMPLETE = "incomplete"


@dataclass
class NormalizedContract:
    """Contrato normalizado con campos enriquecidos."""
    # Identificación
    id: str                          # ID interno único
    external_id: str                 # ID de la fuente original
    source: str                      # Clave de la fuente
    source_name: str                 # Nombre legible de la fuente

    # Información principal
    title: str
    title_normalized: str            # Título limpio y normalizado
    description: Optional[str] = None
    description_normalized: Optional[str] = None

    # Entidad contratante
    entity: Optional[str] = None
    entity_normalized: Optional[str] = None
    entity_type: Optional[str] = None  # "gobierno", "privado", "multilateral"

    # Valor
    amount: Optional[float] = None
    amount_usd: Optional[float] = None  # Convertido a USD
    currency: str = "COP"
    budget_range: Optional[str] = None  # "small", "medium", "large", "enterprise"

    # Geografía
    country: str = "colombia"
    country_name: str = "Colombia"
    region: Optional[str] = None
    city: Optional[str] = None

    # Fechas
    publication_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    estimated_duration_days: Optional[int] = None

    # Clasificación
    contract_type: Optional[str] = None      # "goods", "services", "construction", etc.
    procurement_method: Optional[str] = None  # "open", "restricted", "direct"
    sectors: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)

    # Contenido extraído
    keywords: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    certifications_required: List[str] = field(default_factory=list)

    # URLs
    url: Optional[str] = None
    document_urls: List[str] = field(default_factory=list)

    # Calidad y metadatos
    quality: NormalizationQuality = NormalizationQuality.MEDIUM
    completeness_score: float = 0.0  # 0-100
    raw_data: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    fetched_at: datetime = field(default_factory=datetime.now)
    normalized_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return {
            "id": self.id,
            "external_id": self.external_id,
            "source": self.source,
            "title": self.title,
            "description": self.description,
            "entity": self.entity,
            "amount": self.amount,
            "amount_usd": self.amount_usd,
            "currency": self.currency,
            "country": self.country,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "contract_type": self.contract_type,
            "sectors": self.sectors,
            "keywords": self.keywords,
            "url": self.url,
            "quality": self.quality.value,
            "completeness_score": self.completeness_score
        }

    def to_contract_data(self):
        """Convierte a ContractData para compatibilidad."""
        from scrapers.base import ContractData

        return ContractData(
            external_id=self.external_id,
            title=self.title,
            description=self.description,
            entity=self.entity,
            amount=self.amount,
            currency=self.currency,
            country=self.country,
            source=self.source,
            url=self.url,
            publication_date=self.publication_date,
            deadline=self.deadline,
            raw_data=self.raw_data
        )


class ContractNormalizer:
    """
    Normalizador de contratos de múltiples fuentes.

    Procesa datos crudos y los convierte a un formato común
    enriquecido con información extraída y calculada.
    """

    # Tasas de cambio aproximadas (actualizar periódicamente)
    EXCHANGE_RATES = {
        "COP": 4000,    # COP a USD
        "MXN": 17,      # MXN a USD
        "CLP": 900,     # CLP a USD
        "PEN": 3.7,     # PEN a USD
        "ARS": 850,     # ARS a USD
        "BRL": 5,       # BRL a USD
        "EUR": 0.92,    # EUR a USD
        "USD": 1        # USD a USD
    }

    # Patrones para extracción
    TYPE_PATTERNS = {
        "goods": [
            r"suministro", r"compra\s+de", r"adquisición", r"dotación",
            r"equipos", r"materiales", r"insumos", r"supply", r"goods"
        ],
        "services": [
            r"prestación\s+de\s+servicios", r"servicio\s+de", r"services",
            r"soporte", r"mantenimiento", r"outsourcing"
        ],
        "construction": [
            r"construcción", r"obra", r"edificación", r"infrastructure",
            r"civil\s+works", r"building"
        ],
        "consulting": [
            r"consultoría", r"asesoría", r"consulting", r"advisory",
            r"estudio", r"diagnóstico"
        ],
        "it": [
            r"software", r"sistema\s+de\s+información", r"desarrollo",
            r"aplicación", r"plataforma", r"technology", r"it\s+services"
        ]
    }

    SECTOR_PATTERNS = {
        "tecnologia": ["software", "sistema", "digital", "tecnología", "ti", "tic"],
        "salud": ["salud", "médico", "hospital", "farmacéutico", "health"],
        "educacion": ["educación", "capacitación", "formación", "education"],
        "construccion": ["construcción", "obra", "infraestructura", "civil"],
        "energia": ["energía", "eléctrico", "petróleo", "gas", "energy"],
        "transporte": ["transporte", "vial", "carretera", "transport"],
        "agricultura": ["agrícola", "agropecuario", "rural", "agriculture"],
        "ambiente": ["ambiental", "sostenible", "environment", "green"]
    }

    # Rangos de presupuesto (en USD)
    BUDGET_RANGES = {
        "micro": (0, 10_000),
        "small": (10_000, 100_000),
        "medium": (100_000, 1_000_000),
        "large": (1_000_000, 10_000_000),
        "enterprise": (10_000_000, float('inf'))
    }

    # Nombres de países
    COUNTRY_NAMES = {
        "colombia": "Colombia",
        "usa": "Estados Unidos",
        "mexico": "México",
        "chile": "Chile",
        "peru": "Perú",
        "argentina": "Argentina",
        "brasil": "Brasil",
        "europa": "Europa",
        "multilateral": "Internacional"
    }

    def __init__(self):
        """Inicializa el normalizador."""
        # Compilar patrones
        self._type_patterns = {
            t: [re.compile(p, re.IGNORECASE) for p in patterns]
            for t, patterns in self.TYPE_PATTERNS.items()
        }
        self._sector_patterns = {
            s: [re.compile(p, re.IGNORECASE) for p in patterns]
            for s, patterns in self.SECTOR_PATTERNS.items()
        }

        logger.info("ContractNormalizer inicializado")

    def normalize(
        self,
        raw_data: Dict[str, Any],
        source_key: str,
        source_name: str,
        field_mapping: Optional[Dict[str, str]] = None
    ) -> NormalizedContract:
        """
        Normaliza un contrato crudo.

        Args:
            raw_data: Datos crudos del contrato
            source_key: Clave de la fuente
            source_name: Nombre de la fuente
            field_mapping: Mapeo de campos (opcional)

        Returns:
            NormalizedContract normalizado
        """
        # Aplicar mapeo de campos si existe
        if field_mapping:
            raw_data = self._apply_mapping(raw_data, field_mapping)

        # Extraer campos básicos
        external_id = self._extract_id(raw_data, source_key)
        title = self._extract_string(raw_data, ["title", "titulo", "nombre", "objeto"])
        description = self._extract_string(raw_data, ["description", "descripcion", "detalle"])
        entity = self._extract_string(raw_data, ["entity", "entidad", "organismo", "buyer"])

        # Extraer valores numéricos
        amount, currency = self._extract_amount(raw_data)

        # Extraer país
        country = self._extract_string(raw_data, ["country", "pais"]) or self._infer_country(source_key)

        # Extraer fechas
        publication_date = self._extract_date(raw_data, ["publication_date", "fecha_publicacion", "published"])
        deadline = self._extract_date(raw_data, ["deadline", "fecha_cierre", "closing_date", "fecha_limite"])

        # Extraer URL
        url = self._extract_string(raw_data, ["url", "link", "enlace"])

        # Generar ID único
        unique_id = self._generate_id(source_key, external_id, title)

        # Crear contrato base
        contract = NormalizedContract(
            id=unique_id,
            external_id=external_id,
            source=source_key,
            source_name=source_name,
            title=title or "Sin título",
            title_normalized=self._normalize_text(title),
            description=description,
            description_normalized=self._normalize_text(description) if description else None,
            entity=entity,
            entity_normalized=self._normalize_entity(entity) if entity else None,
            amount=amount,
            currency=currency,
            country=country,
            country_name=self.COUNTRY_NAMES.get(country, country),
            publication_date=publication_date,
            deadline=deadline,
            url=url,
            raw_data=raw_data
        )

        # Enriquecer contrato
        self._enrich_contract(contract)

        # Calcular calidad
        contract.quality, contract.completeness_score = self._assess_quality(contract)

        return contract

    def normalize_batch(
        self,
        raw_contracts: List[Dict[str, Any]],
        source_key: str,
        source_name: str,
        field_mapping: Optional[Dict[str, str]] = None
    ) -> List[NormalizedContract]:
        """
        Normaliza múltiples contratos.

        Returns:
            Lista de contratos normalizados
        """
        normalized = []

        for raw in raw_contracts:
            try:
                contract = self.normalize(raw, source_key, source_name, field_mapping)
                normalized.append(contract)
            except Exception as e:
                logger.warning(f"Error normalizando contrato: {e}")
                continue

        logger.info(f"Normalizados {len(normalized)}/{len(raw_contracts)} contratos de {source_key}")
        return normalized

    def _apply_mapping(
        self,
        data: Dict[str, Any],
        mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """Aplica mapeo de campos."""
        result = data.copy()

        for target, source in mapping.items():
            if source in data:
                result[target] = data[source]

        return result

    def _extract_id(self, data: Dict[str, Any], source_key: str) -> str:
        """Extrae ID externo del contrato."""
        id_fields = ["id", "external_id", "numero", "code", "reference", "uid"]

        for field in id_fields:
            if field in data and data[field]:
                return str(data[field])

        # Generar ID desde otros campos
        return f"{source_key}_{hashlib.md5(str(data).encode()).hexdigest()[:12]}"

    def _extract_string(
        self,
        data: Dict[str, Any],
        fields: List[str]
    ) -> Optional[str]:
        """Extrae string de múltiples campos posibles."""
        for field in fields:
            if field in data and data[field]:
                value = str(data[field]).strip()
                if value and value.lower() not in ["null", "none", "n/a", ""]:
                    return value
        return None

    def _extract_amount(
        self,
        data: Dict[str, Any]
    ) -> Tuple[Optional[float], str]:
        """Extrae monto y moneda."""
        amount_fields = ["amount", "monto", "valor", "budget", "presupuesto", "value"]
        currency_fields = ["currency", "moneda", "divisa"]

        amount = None
        currency = "COP"  # Default

        # Buscar monto
        for field in amount_fields:
            if field in data and data[field]:
                try:
                    value = data[field]
                    if isinstance(value, str):
                        # Limpiar string
                        value = re.sub(r"[^\d.,]", "", value)
                        value = value.replace(",", "")
                    amount = float(value)
                    if amount > 0:
                        break
                except (ValueError, TypeError):
                    continue

        # Buscar moneda
        for field in currency_fields:
            if field in data and data[field]:
                currency = str(data[field]).upper()
                break

        return amount, currency

    def _extract_date(
        self,
        data: Dict[str, Any],
        fields: List[str]
    ) -> Optional[datetime]:
        """Extrae fecha de múltiples campos posibles."""
        for field in fields:
            if field in data and data[field]:
                date = self._parse_date(data[field])
                if date:
                    return date
        return None

    def _parse_date(self, value: Any) -> Optional[datetime]:
        """Parsea una fecha de varios formatos."""
        if isinstance(value, datetime):
            return value

        if not value or not isinstance(value, str):
            return None

        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d %b %Y",
            "%B %d, %Y"
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value[:26], fmt)
            except (ValueError, TypeError):
                continue

        # Intentar ISO format
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            pass

        return None

    def _infer_country(self, source_key: str) -> str:
        """Infiere país de la fuente."""
        country_map = {
            "secop": "colombia",
            "sam_gov": "usa",
            "compranet": "mexico",
            "mercado_publico": "chile",
            "osce": "peru",
            "comprar": "argentina",
            "comprasnet": "brasil",
            "worldbank": "multilateral",
            "idb": "multilateral",
            "ungm": "multilateral",
            "ted": "europa",
            "ecopetrol": "colombia",
            "epm": "colombia"
        }

        for key, country in country_map.items():
            if key in source_key.lower():
                return country

        return "unknown"

    def _generate_id(self, source: str, external_id: str, title: str) -> str:
        """Genera ID único para el contrato."""
        content = f"{source}:{external_id}:{title}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _normalize_text(self, text: Optional[str]) -> Optional[str]:
        """Normaliza texto para búsqueda y comparación."""
        if not text:
            return None

        # Convertir a minúsculas
        text = text.lower()

        # Remover caracteres especiales excepto espacios
        text = re.sub(r"[^\w\s]", " ", text)

        # Normalizar espacios
        text = " ".join(text.split())

        return text

    def _normalize_entity(self, entity: str) -> str:
        """Normaliza nombre de entidad."""
        # Remover prefijos comunes
        prefixes = [
            "ministerio de", "secretaría de", "departamento de",
            "alcaldía de", "gobernación de", "empresa de"
        ]

        normalized = entity.lower()
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):].strip()
                break

        return normalized

    def _enrich_contract(self, contract: NormalizedContract):
        """Enriquece contrato con información calculada."""
        text = f"{contract.title} {contract.description or ''}".lower()

        # Detectar tipo de contrato
        contract.contract_type = self._detect_type(text)

        # Detectar sectores
        contract.sectors = self._detect_sectors(text)

        # Extraer keywords
        contract.keywords = self._extract_keywords(text)

        # Extraer tecnologías
        contract.technologies = self._extract_technologies(text)

        # Extraer certificaciones requeridas
        contract.certifications_required = self._extract_certifications(text)

        # Detectar tipo de entidad
        contract.entity_type = self._detect_entity_type(contract.entity, contract.source)

        # Convertir a USD
        if contract.amount:
            contract.amount_usd = self._convert_to_usd(contract.amount, contract.currency)
            contract.budget_range = self._determine_budget_range(contract.amount_usd)

        # Estimar duración
        contract.estimated_duration_days = self._estimate_duration(
            contract.publication_date, contract.deadline, text
        )

    def _detect_type(self, text: str) -> Optional[str]:
        """Detecta tipo de contrato."""
        scores = {}

        for contract_type, patterns in self._type_patterns.items():
            score = sum(1 for p in patterns if p.search(text))
            if score > 0:
                scores[contract_type] = score

        if scores:
            return max(scores, key=scores.get)
        return None

    def _detect_sectors(self, text: str) -> List[str]:
        """Detecta sectores del contrato."""
        sectors = []

        for sector, patterns in self._sector_patterns.items():
            if any(p.search(text) for p in patterns):
                sectors.append(sector)

        return sectors

    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extrae palabras clave relevantes."""
        # Palabras a ignorar
        stopwords = {
            "de", "la", "el", "en", "y", "a", "los", "las", "del", "para",
            "con", "por", "se", "al", "que", "un", "una", "su", "como",
            "the", "of", "and", "to", "in", "for", "on", "with"
        }

        # Extraer palabras
        words = re.findall(r"\b[a-záéíóúñ]+\b", text.lower())

        # Filtrar y contar
        word_counts = {}
        for word in words:
            if len(word) > 3 and word not in stopwords:
                word_counts[word] = word_counts.get(word, 0) + 1

        # Top keywords por frecuencia
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:max_keywords]]

    def _extract_technologies(self, text: str) -> List[str]:
        """Extrae tecnologías mencionadas."""
        tech_patterns = [
            r"python", r"java(?:script)?", r"\.net", r"node\.?js",
            r"react", r"angular", r"vue", r"aws", r"azure",
            r"google\s+cloud", r"kubernetes", r"docker",
            r"postgresql", r"mysql", r"oracle", r"mongodb",
            r"power\s*bi", r"tableau", r"sap"
        ]

        technologies = set()
        for pattern in tech_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                technologies.add(pattern.replace(r"\s+", " ").replace("\\", "").upper())

        return list(technologies)

    def _extract_certifications(self, text: str) -> List[str]:
        """Extrae certificaciones requeridas."""
        cert_patterns = [
            (r"iso\s*(\d+)", "ISO {}"),
            (r"cmmi\s*(?:nivel\s*)?(\d+)?", "CMMI{}"),
            (r"(pmp|itil|cobit|scrum)", "{}"),
        ]

        certifications = set()
        for pattern, template in cert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match:
                    cert = template.format(match).upper()
                else:
                    cert = template.format("").upper()
                certifications.add(cert)

        return list(certifications)

    def _detect_entity_type(self, entity: Optional[str], source: str) -> Optional[str]:
        """Detecta tipo de entidad contratante."""
        if not entity:
            if "multilateral" in source or source in ["worldbank", "idb", "ungm"]:
                return "multilateral"
            return None

        entity_lower = entity.lower()

        # Gobierno
        gov_indicators = [
            "ministerio", "secretaría", "alcaldía", "gobernación",
            "departamento", "agencia", "instituto", "superintendencia",
            "ministry", "department", "agency"
        ]
        if any(ind in entity_lower for ind in gov_indicators):
            return "gobierno"

        # Multilateral
        multilateral_indicators = [
            "world bank", "banco mundial", "bid", "idb",
            "naciones unidas", "united nations", "onu", "un"
        ]
        if any(ind in entity_lower for ind in multilateral_indicators):
            return "multilateral"

        # Privado
        private_indicators = [
            "s.a.", "s.a.s", "ltda", "inc", "corp", "llc"
        ]
        if any(ind in entity_lower for ind in private_indicators):
            return "privado"

        return "gobierno"  # Default para SECOP y similares

    def _convert_to_usd(self, amount: float, currency: str) -> float:
        """Convierte monto a USD."""
        rate = self.EXCHANGE_RATES.get(currency, 1)
        return amount / rate

    def _determine_budget_range(self, amount_usd: float) -> str:
        """Determina rango de presupuesto."""
        for range_name, (min_val, max_val) in self.BUDGET_RANGES.items():
            if min_val <= amount_usd < max_val:
                return range_name
        return "enterprise"

    def _estimate_duration(
        self,
        pub_date: Optional[datetime],
        deadline: Optional[datetime],
        text: str
    ) -> Optional[int]:
        """Estima duración del contrato en días."""
        # Si tenemos ambas fechas
        if pub_date and deadline:
            return (deadline - pub_date).days

        # Buscar en texto
        patterns = [
            (r"(\d+)\s*meses?", 30),
            (r"(\d+)\s*semanas?", 7),
            (r"(\d+)\s*d[ií]as?", 1),
            (r"(\d+)\s*a[ñn]os?", 365)
        ]

        for pattern, multiplier in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1)) * multiplier

        return None

    def _assess_quality(
        self,
        contract: NormalizedContract
    ) -> Tuple[NormalizationQuality, float]:
        """Evalúa calidad de la normalización."""
        score = 0
        max_score = 100

        # Campos principales (60 puntos)
        if contract.title and len(contract.title) > 10:
            score += 15
        if contract.description and len(contract.description) > 50:
            score += 15
        if contract.entity:
            score += 10
        if contract.amount and contract.amount > 0:
            score += 10
        if contract.deadline:
            score += 10

        # Campos secundarios (30 puntos)
        if contract.url:
            score += 5
        if contract.publication_date:
            score += 5
        if contract.contract_type:
            score += 5
        if contract.sectors:
            score += 5
        if contract.keywords:
            score += 5
        if contract.technologies:
            score += 5

        # Campos de enriquecimiento (10 puntos)
        if contract.amount_usd:
            score += 5
        if contract.entity_type:
            score += 5

        # Determinar calidad
        if score >= 80:
            quality = NormalizationQuality.HIGH
        elif score >= 50:
            quality = NormalizationQuality.MEDIUM
        elif score >= 25:
            quality = NormalizationQuality.LOW
        else:
            quality = NormalizationQuality.INCOMPLETE

        return quality, score


# Singleton
_normalizer = None


def get_normalizer() -> ContractNormalizer:
    """Obtiene la instancia singleton del normalizador."""
    global _normalizer
    if _normalizer is None:
        _normalizer = ContractNormalizer()
    return _normalizer
