"""
Source Registry
Registro central de fuentes de datos para el agregador.

Permite registrar, configurar y gestionar múltiples fuentes
de contratos de manera dinámica.
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class SourceType(str, Enum):
    """Tipos de fuentes de datos."""

    API = "api"  # API REST/GraphQL
    SCRAPER = "scraper"  # Web scraping
    RSS = "rss"  # Feed RSS/Atom
    DATABASE = "database"  # Conexión directa a BD
    WEBHOOK = "webhook"  # Push desde terceros
    FILE = "file"  # Archivos (CSV, JSON, XML)
    CUSTOM = "custom"  # Implementación custom


class SourceStatus(str, Enum):
    """Estados de una fuente."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    MAINTENANCE = "maintenance"


class SourcePriority(str, Enum):
    """Prioridad de actualización."""

    CRITICAL = "critical"  # Cada 5 min
    HIGH = "high"  # Cada 15 min
    NORMAL = "normal"  # Cada hora
    LOW = "low"  # Cada 6 horas
    DAILY = "daily"  # Una vez al día


@dataclass
class SourceConfig:
    """Configuración de una fuente de datos."""

    # Identificación
    key: str  # Identificador único
    name: str  # Nombre legible
    description: str = ""

    # Tipo y conexión
    source_type: SourceType = SourceType.API
    url: str = ""
    api_key: str = ""
    credentials: Dict[str, str] = field(default_factory=dict)

    # Geografía
    country: str = "colombia"
    region: str = ""
    currency: str = "COP"

    # Categorización
    categories: List[str] = field(default_factory=list)
    sectors: List[str] = field(default_factory=list)
    contract_types: List[str] = field(default_factory=list)

    # Scheduling
    priority: SourcePriority = SourcePriority.NORMAL
    update_interval_minutes: int = 60
    last_fetch: Optional[datetime] = None

    # Comportamiento
    enabled: bool = True
    max_results_per_fetch: int = 100
    days_back: int = 7
    rate_limit_requests: int = 100
    rate_limit_period_seconds: int = 3600

    # Estado
    status: SourceStatus = SourceStatus.ACTIVE
    error_count: int = 0
    last_error: Optional[str] = None
    total_contracts_fetched: int = 0

    # Implementación
    scraper_class: Optional[str] = None  # Path to scraper class
    normalizer_config: Dict[str, Any] = field(default_factory=dict)

    # Metadatos
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return {
            "key": self.key,
            "name": self.name,
            "source_type": self.source_type.value,
            "country": self.country,
            "priority": self.priority.value,
            "enabled": self.enabled,
            "status": self.status.value,
            "error_count": self.error_count,
            "total_contracts_fetched": self.total_contracts_fetched,
            "last_fetch": self.last_fetch.isoformat() if self.last_fetch else None,
        }


class SourceRegistry:
    """
    Registro central de fuentes de datos.

    Gestiona la configuración y estado de todas las fuentes
    de contratos disponibles en el sistema.
    """

    # Fuentes predefinidas
    BUILTIN_SOURCES = {
        # Colombia - Gobierno
        "secop": SourceConfig(
            key="secop",
            name="SECOP II",
            description="Sistema Electrónico de Contratación Pública de Colombia",
            source_type=SourceType.API,
            url="https://www.datos.gov.co/resource/p6dx-8zbt.json",
            country="colombia",
            currency="COP",
            categories=["gobierno"],
            priority=SourcePriority.HIGH,
            update_interval_minutes=30,
            scraper_class="scrapers.secop.SecopScraper",
        ),
        # USA - Gobierno
        "sam_gov": SourceConfig(
            key="sam_gov",
            name="SAM.gov",
            description="System for Award Management - US Federal Contracts",
            source_type=SourceType.API,
            url="https://api.sam.gov/opportunities/v2/search",
            country="usa",
            currency="USD",
            categories=["gobierno"],
            priority=SourcePriority.NORMAL,
            update_interval_minutes=60,
            scraper_class="scrapers.sam.SamGovScraper",
        ),
        # Multilaterales
        "worldbank": SourceConfig(
            key="worldbank",
            name="Banco Mundial",
            description="World Bank Procurement Opportunities",
            source_type=SourceType.SCRAPER,
            url="https://projects.worldbank.org/en/projects-operations/procurement",
            country="multilateral",
            currency="USD",
            categories=["multilateral"],
            priority=SourcePriority.NORMAL,
            update_interval_minutes=120,
            scraper_class="scrapers.private.multilateral.worldbank.WorldBankScraper",
        ),
        "idb": SourceConfig(
            key="idb",
            name="BID - Banco Interamericano de Desarrollo",
            description="Inter-American Development Bank Procurement",
            source_type=SourceType.SCRAPER,
            url="https://www.iadb.org/en/projects-search",
            country="multilateral",
            currency="USD",
            categories=["multilateral"],
            priority=SourcePriority.NORMAL,
            update_interval_minutes=120,
            scraper_class="scrapers.private.multilateral.idb.IDBScraper",
        ),
        "ungm": SourceConfig(
            key="ungm",
            name="UNGM - UN Global Marketplace",
            description="United Nations Global Marketplace",
            source_type=SourceType.SCRAPER,
            url="https://www.ungm.org/Public/Notice",
            country="multilateral",
            currency="USD",
            categories=["multilateral"],
            priority=SourcePriority.NORMAL,
            update_interval_minutes=120,
            scraper_class="scrapers.private.multilateral.ungm.UNGMScraper",
        ),
        # Colombia - Privados
        "ecopetrol": SourceConfig(
            key="ecopetrol",
            name="Ecopetrol",
            description="Portal de Proveedores de Ecopetrol",
            source_type=SourceType.SCRAPER,
            url="https://csp.ecopetrol.com.co",
            country="colombia",
            currency="COP",
            categories=["privado", "energia"],
            sectors=["energia", "construccion", "tecnologia"],
            priority=SourcePriority.NORMAL,
            update_interval_minutes=120,
            scraper_class="scrapers.private.ecopetrol.EcopetrolScraper",
        ),
        "epm": SourceConfig(
            key="epm",
            name="EPM",
            description="Empresas Públicas de Medellín - Portal de Proveedores",
            source_type=SourceType.SCRAPER,
            url="https://www.epm.com.co/proveedores",
            country="colombia",
            currency="COP",
            categories=["privado", "energia", "servicios_publicos"],
            priority=SourcePriority.NORMAL,
            update_interval_minutes=120,
            scraper_class="scrapers.private.epm.EPMScraper",
        ),
        # LATAM
        "compranet_mexico": SourceConfig(
            key="compranet_mexico",
            name="CompraNet México",
            description="Sistema de Compras Gubernamentales de México",
            source_type=SourceType.API,
            url="https://compranet.hacienda.gob.mx",
            country="mexico",
            currency="MXN",
            categories=["gobierno"],
            priority=SourcePriority.NORMAL,
            update_interval_minutes=120,
            scraper_class="scrapers.latam.mexico.CompraNetScraper",
        ),
        "mercado_publico_chile": SourceConfig(
            key="mercado_publico_chile",
            name="Mercado Público Chile",
            description="Portal de Compras Públicas de Chile",
            source_type=SourceType.API,
            url="https://api.mercadopublico.cl",
            country="chile",
            currency="CLP",
            categories=["gobierno"],
            priority=SourcePriority.NORMAL,
            update_interval_minutes=120,
            scraper_class="scrapers.latam.chile.ChileCompraScraper",
        ),
        "osce_peru": SourceConfig(
            key="osce_peru",
            name="OSCE Perú",
            description="Organismo Supervisor de las Contrataciones del Estado",
            source_type=SourceType.SCRAPER,
            url="https://prodapp2.seace.gob.pe",
            country="peru",
            currency="PEN",
            categories=["gobierno"],
            priority=SourcePriority.NORMAL,
            update_interval_minutes=120,
            scraper_class="scrapers.latam.peru.SeaceScraper",
        ),
        "comprar_argentina": SourceConfig(
            key="comprar_argentina",
            name="Comprar Argentina",
            description="Sistema de Contrataciones del Estado Argentino",
            source_type=SourceType.API,
            url="https://comprar.gob.ar",
            country="argentina",
            currency="ARS",
            categories=["gobierno"],
            priority=SourcePriority.LOW,
            update_interval_minutes=360,
            scraper_class="scrapers.latam.argentina.ComprarScraper",
        ),
        "comprasnet_brasil": SourceConfig(
            key="comprasnet_brasil",
            name="ComprasNet Brasil",
            description="Portal de Compras del Gobierno Federal de Brasil",
            source_type=SourceType.API,
            url="https://compras.dados.gov.br",
            country="brasil",
            currency="BRL",
            categories=["gobierno"],
            priority=SourcePriority.LOW,
            update_interval_minutes=360,
            scraper_class="scrapers.latam.brasil.ComprasNetScraper",
        ),
        # Europa (para expansión)
        "ted_europa": SourceConfig(
            key="ted_europa",
            name="TED - Tenders Electronic Daily",
            description="Suplemento al Diario Oficial de la UE para licitaciones",
            source_type=SourceType.API,
            url="https://ted.europa.eu/api",
            country="europa",
            currency="EUR",
            categories=["gobierno", "multilateral"],
            priority=SourcePriority.LOW,
            update_interval_minutes=360,
            enabled=False,  # Deshabilitado por defecto
            scraper_class="scrapers.international.ted.TEDScraper",
        ),
    }

    def __init__(self):
        """Inicializa el registro."""
        self._sources: Dict[str, SourceConfig] = {}
        self._scrapers: Dict[str, Any] = {}  # Cache de instancias

        # Cargar fuentes predefinidas
        for key, config in self.BUILTIN_SOURCES.items():
            self._sources[key] = config

        logger.info(f"SourceRegistry inicializado con {len(self._sources)} fuentes")

    def register(self, config: SourceConfig) -> bool:
        """
        Registra una nueva fuente de datos.

        Args:
            config: Configuración de la fuente

        Returns:
            True si se registró correctamente
        """
        if config.key in self._sources:
            logger.warning(f"Fuente {config.key} ya existe, actualizando...")

        self._sources[config.key] = config
        logger.info(f"Fuente registrada: {config.key} ({config.name})")
        return True

    def unregister(self, key: str) -> bool:
        """Elimina una fuente del registro."""
        if key in self._sources:
            del self._sources[key]
            if key in self._scrapers:
                del self._scrapers[key]
            logger.info(f"Fuente eliminada: {key}")
            return True
        return False

    def get(self, key: str) -> Optional[SourceConfig]:
        """Obtiene configuración de una fuente."""
        return self._sources.get(key)

    def get_all(self) -> Dict[str, SourceConfig]:
        """Obtiene todas las fuentes registradas."""
        return self._sources.copy()

    def get_enabled(self) -> Dict[str, SourceConfig]:
        """Obtiene solo las fuentes habilitadas."""
        return {k: v for k, v in self._sources.items() if v.enabled}

    def get_by_country(self, country: str) -> Dict[str, SourceConfig]:
        """Obtiene fuentes por país."""
        return {k: v for k, v in self._sources.items() if v.country == country and v.enabled}

    def get_by_priority(self, priority: SourcePriority) -> Dict[str, SourceConfig]:
        """Obtiene fuentes por prioridad."""
        return {k: v for k, v in self._sources.items() if v.priority == priority and v.enabled}

    def get_due_for_update(self) -> List[SourceConfig]:
        """
        Obtiene fuentes que necesitan actualización.

        Returns:
            Lista de fuentes ordenadas por prioridad
        """
        due = []
        now = datetime.now()

        for config in self._sources.values():
            if not config.enabled:
                continue

            if config.status in [SourceStatus.ERROR, SourceStatus.RATE_LIMITED]:
                # Verificar si pasó suficiente tiempo para reintentar
                if config.last_fetch:
                    retry_after = timedelta(minutes=max(30, config.error_count * 10))
                    if now - config.last_fetch < retry_after:
                        continue

            if config.last_fetch is None:
                due.append(config)
            else:
                interval = timedelta(minutes=config.update_interval_minutes)
                if now - config.last_fetch >= interval:
                    due.append(config)

        # Ordenar por prioridad
        priority_order = {
            SourcePriority.CRITICAL: 0,
            SourcePriority.HIGH: 1,
            SourcePriority.NORMAL: 2,
            SourcePriority.LOW: 3,
            SourcePriority.DAILY: 4,
        }

        due.sort(key=lambda x: priority_order.get(x.priority, 5))

        return due

    def get_scraper(self, key: str) -> Optional[Any]:
        """
        Obtiene instancia del scraper para una fuente.

        Args:
            key: Clave de la fuente

        Returns:
            Instancia del scraper o None
        """
        if key in self._scrapers:
            return self._scrapers[key]

        config = self._sources.get(key)
        if not config or not config.scraper_class:
            return None

        try:
            # Importar dinámicamente la clase
            module_path, class_name = config.scraper_class.rsplit(".", 1)
            module = importlib.import_module(module_path)
            scraper_class = getattr(module, class_name)

            # Crear instancia — each scraper handles its own URL internally,
            # so we instantiate without arguments (scrapers define their own
            # API URLs in __init__).
            scraper = scraper_class()
            self._scrapers[key] = scraper

            logger.info(f"Scraper cargado: {key} -> {config.scraper_class}")
            return scraper

        except Exception as e:
            logger.error(f"Error cargando scraper {key}: {e}")
            return None

    def update_status(self, key: str, status: SourceStatus, error_message: Optional[str] = None):
        """Actualiza el estado de una fuente."""
        if key not in self._sources:
            return

        config = self._sources[key]
        config.status = status
        config.updated_at = datetime.now()

        if status == SourceStatus.ERROR:
            config.error_count += 1
            config.last_error = error_message
        elif status == SourceStatus.ACTIVE:
            config.error_count = 0
            config.last_error = None

    def record_fetch(self, key: str, contracts_count: int):
        """Registra una extracción exitosa."""
        if key not in self._sources:
            return

        config = self._sources[key]
        config.last_fetch = datetime.now()
        config.total_contracts_fetched += contracts_count
        config.status = SourceStatus.ACTIVE
        config.error_count = 0

    def enable(self, key: str) -> bool:
        """Habilita una fuente."""
        if key in self._sources:
            self._sources[key].enabled = True
            self._sources[key].status = SourceStatus.ACTIVE
            return True
        return False

    def disable(self, key: str) -> bool:
        """Deshabilita una fuente."""
        if key in self._sources:
            self._sources[key].enabled = False
            self._sources[key].status = SourceStatus.INACTIVE
            return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del registro."""
        enabled = [s for s in self._sources.values() if s.enabled]
        active = [s for s in enabled if s.status == SourceStatus.ACTIVE]
        errored = [s for s in self._sources.values() if s.status == SourceStatus.ERROR]

        return {
            "total_sources": len(self._sources),
            "enabled": len(enabled),
            "active": len(active),
            "errored": len(errored),
            "by_country": self._count_by_field("country"),
            "by_type": self._count_by_field("source_type"),
            "by_priority": self._count_by_field("priority"),
            "total_contracts_fetched": sum(s.total_contracts_fetched for s in self._sources.values()),
        }

    def _count_by_field(self, field: str) -> Dict[str, int]:
        """Cuenta fuentes por campo."""
        counts = {}
        for source in self._sources.values():
            value = getattr(source, field, "unknown")
            if hasattr(value, "value"):  # Es un Enum
                value = value.value
            counts[value] = counts.get(value, 0) + 1
        return counts


# Singleton
_source_registry = None


def get_source_registry() -> SourceRegistry:
    """Obtiene la instancia singleton del registro."""
    global _source_registry
    if _source_registry is None:
        _source_registry = SourceRegistry()
    return _source_registry
