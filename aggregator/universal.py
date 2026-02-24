"""
Universal Aggregator
Agregador central que coordina la extracción de todas las fuentes.

Este es el punto de entrada principal para obtener contratos
de todas las fuentes configuradas de manera unificada.
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from aggregator.normalizer import ContractNormalizer, NormalizedContract, get_normalizer
from aggregator.source_registry import SourceConfig, SourcePriority, SourceRegistry, SourceStatus, get_source_registry

logger = logging.getLogger(__name__)


class AggregationMode(str, Enum):
    """Modos de agregación."""

    FULL = "full"  # Todas las fuentes
    PRIORITY = "priority"  # Solo fuentes de alta prioridad
    COUNTRY = "country"  # Fuentes de un país específico
    SELECTIVE = "selective"  # Fuentes específicas


@dataclass
class AggregationResult:
    """Resultado de una agregación."""

    # Contratos obtenidos
    contracts: List[NormalizedContract] = field(default_factory=list)

    # Estadísticas
    total_contracts: int = 0
    sources_queried: int = 0
    sources_successful: int = 0
    sources_failed: int = 0

    # Detalles por fuente
    source_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Errores
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return {
            "total_contracts": self.total_contracts,
            "sources_queried": self.sources_queried,
            "sources_successful": self.sources_successful,
            "sources_failed": self.sources_failed,
            "duration_seconds": round(self.duration_seconds, 2),
            "source_results": {
                k: {
                    "contracts": v.get("contracts", 0),
                    "status": v.get("status", "unknown"),
                    "duration": round(v.get("duration", 0), 2),
                }
                for k, v in self.source_results.items()
            },
            "errors_count": len(self.errors),
        }


class UniversalAggregator:
    """
    Agregador universal de contratos.

    Coordina la extracción de múltiples fuentes en paralelo,
    normaliza los resultados y proporciona una interfaz unificada.
    """

    def __init__(
        self,
        registry: Optional[SourceRegistry] = None,
        normalizer: Optional[ContractNormalizer] = None,
        max_workers: int = 5,
    ):
        """
        Inicializa el agregador.

        Args:
            registry: Registro de fuentes (usa singleton si no se proporciona)
            normalizer: Normalizador (usa singleton si no se proporciona)
            max_workers: Máximo de workers para ejecución paralela
        """
        self.registry = registry or get_source_registry()
        self.normalizer = normalizer or get_normalizer()
        self.max_workers = max_workers

        # Cache de contratos
        self._cache: Dict[str, List[NormalizedContract]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

        logger.info(f"UniversalAggregator inicializado con {max_workers} workers")

    def aggregate(
        self,
        mode: AggregationMode = AggregationMode.FULL,
        sources: Optional[List[str]] = None,
        country: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        days_back: int = 7,
        use_cache: bool = True,
        cache_ttl_minutes: int = 30,
    ) -> AggregationResult:
        """
        Agrega contratos de múltiples fuentes.

        Args:
            mode: Modo de agregación
            sources: Lista de fuentes específicas (para modo SELECTIVE)
            country: País específico (para modo COUNTRY)
            keywords: Palabras clave para filtrar
            min_amount: Monto mínimo
            max_amount: Monto máximo
            days_back: Días hacia atrás para buscar
            use_cache: Si usar cache
            cache_ttl_minutes: TTL del cache en minutos

        Returns:
            AggregationResult con contratos y estadísticas
        """
        result = AggregationResult(started_at=datetime.now())

        # Determinar fuentes a consultar
        sources_to_query = self._select_sources(mode, sources, country)

        if not sources_to_query:
            logger.warning("No hay fuentes para consultar")
            result.completed_at = datetime.now()
            return result

        result.sources_queried = len(sources_to_query)

        # Ejecutar en paralelo
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}

            for source_key, source_config in sources_to_query.items():
                # Verificar cache
                if use_cache:
                    cached = self._get_from_cache(source_key, cache_ttl_minutes)
                    if cached is not None:
                        result.source_results[source_key] = {
                            "contracts": len(cached),
                            "status": "cached",
                            "duration": 0,
                        }
                        result.contracts.extend(cached)
                        result.sources_successful += 1
                        continue

                # Enviar a ejecución
                future = executor.submit(self._fetch_source, source_config, keywords, min_amount, max_amount, days_back)
                futures[future] = source_key

            # Procesar resultados
            for future in as_completed(futures):
                source_key = futures[future]

                try:
                    contracts, duration, error = future.result(timeout=120)

                    if error:
                        result.source_results[source_key] = {
                            "contracts": 0,
                            "status": "error",
                            "error": str(error),
                            "duration": duration,
                        }
                        result.errors.append({"source": source_key, "error": str(error)})
                        result.sources_failed += 1
                    else:
                        result.source_results[source_key] = {
                            "contracts": len(contracts),
                            "status": "success",
                            "duration": duration,
                        }
                        result.contracts.extend(contracts)
                        result.sources_successful += 1

                        # Guardar en cache
                        if use_cache:
                            self._save_to_cache(source_key, contracts)

                except Exception as e:
                    logger.error(f"Error procesando fuente {source_key}: {e}")
                    result.source_results[source_key] = {
                        "contracts": 0,
                        "status": "error",
                        "error": str(e),
                        "duration": 0,
                    }
                    result.errors.append({"source": source_key, "error": str(e)})
                    result.sources_failed += 1

        # Finalizar
        result.completed_at = datetime.now()
        result.duration_seconds = (result.completed_at - result.started_at).total_seconds()
        result.total_contracts = len(result.contracts)

        # Deduplicar contratos
        result.contracts = self._deduplicate(result.contracts)
        result.total_contracts = len(result.contracts)

        logger.info(
            f"Agregación completada: {result.total_contracts} contratos "
            f"de {result.sources_successful}/{result.sources_queried} fuentes "
            f"en {result.duration_seconds:.1f}s"
        )

        return result

    def aggregate_for_user(
        self, user_profile: Dict[str, Any], limit: int = 50, use_cache: bool = True
    ) -> AggregationResult:
        """
        Agrega contratos relevantes para un usuario específico.

        Args:
            user_profile: Perfil del usuario
            limit: Máximo de contratos a retornar
            use_cache: Si usar cache

        Returns:
            AggregationResult con contratos filtrados y ordenados
        """
        # Determinar parámetros desde perfil
        countries = user_profile.get("countries", "all")
        keywords = user_profile.get("include_keywords", [])
        min_budget = user_profile.get("min_budget")
        max_budget = user_profile.get("max_budget")
        industry = user_profile.get("industry")

        # Agregar keywords de industria
        if industry:
            from config import Config

            industry_config = Config.INDUSTRIES.get(industry, {})
            industry_keywords = industry_config.get("keywords", [])
            keywords = list(set(keywords + industry_keywords))

        # Determinar modo y país
        if countries == "all":
            mode = AggregationMode.FULL
            country = None
        else:
            mode = AggregationMode.COUNTRY
            country = countries

        # Agregar fuentes multilaterales siempre
        result = self.aggregate(
            mode=mode,
            country=country,
            keywords=keywords,
            min_amount=min_budget,
            max_amount=max_budget,
            use_cache=use_cache,
        )

        # Ordenar por relevancia usando scoring
        if result.contracts:
            from intelligence.opportunity_scorer import get_opportunity_scorer

            scorer = get_opportunity_scorer()
            scored = scorer.score_batch([c.to_dict() for c in result.contracts], user_profile)

            # Reconstruir lista ordenada
            contract_map = {c.id: c for c in result.contracts}
            sorted_contracts = []

            for contract_dict, score in scored[:limit]:
                contract_id = contract_dict.get("id")
                if contract_id in contract_map:
                    sorted_contracts.append(contract_map[contract_id])

            result.contracts = sorted_contracts
            result.total_contracts = len(sorted_contracts)

        return result

    def get_new_contracts(self, since: datetime, sources: Optional[List[str]] = None) -> List[NormalizedContract]:
        """
        Obtiene contratos nuevos desde una fecha.

        Args:
            since: Fecha desde la cual buscar
            sources: Fuentes específicas (opcional)

        Returns:
            Lista de contratos nuevos
        """
        result = self.aggregate(
            mode=AggregationMode.SELECTIVE if sources else AggregationMode.FULL, sources=sources, use_cache=False
        )

        # Filtrar por fecha
        new_contracts = [c for c in result.contracts if c.publication_date and c.publication_date >= since]

        return new_contracts

    def get_expiring_soon(self, days: int = 3, sources: Optional[List[str]] = None) -> List[NormalizedContract]:
        """
        Obtiene contratos que expiran pronto.

        Args:
            days: Días hasta expiración
            sources: Fuentes específicas (opcional)

        Returns:
            Lista de contratos que expiran pronto
        """
        result = self.aggregate(
            mode=AggregationMode.SELECTIVE if sources else AggregationMode.FULL, sources=sources, use_cache=True
        )

        now = datetime.now()
        deadline_limit = now + timedelta(days=days)

        # Filtrar por deadline
        expiring = [c for c in result.contracts if c.deadline and now < c.deadline <= deadline_limit]

        # Ordenar por deadline
        expiring.sort(key=lambda x: x.deadline)

        return expiring

    def search(
        self,
        query: str,
        country: Optional[str] = None,
        contract_type: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        limit: int = 50,
    ) -> List[NormalizedContract]:
        """
        Búsqueda de contratos.

        Args:
            query: Texto de búsqueda
            country: País específico
            contract_type: Tipo de contrato
            min_amount: Monto mínimo
            max_amount: Monto máximo
            limit: Máximo de resultados

        Returns:
            Lista de contratos que coinciden
        """
        # Obtener todos los contratos (desde cache preferiblemente)
        result = self.aggregate(
            mode=AggregationMode.COUNTRY if country else AggregationMode.FULL,
            country=country,
            keywords=query.split() if query else None,
            min_amount=min_amount,
            max_amount=max_amount,
            use_cache=True,
        )

        contracts = result.contracts

        # Filtrar por tipo si se especifica
        if contract_type:
            contracts = [c for c in contracts if c.contract_type == contract_type]

        # Ordenar por relevancia (simple: coincidencia de query)
        if query:
            query_lower = query.lower()
            contracts.sort(
                key=lambda c: (query_lower in (c.title or "").lower(), query_lower in (c.description or "").lower()),
                reverse=True,
            )

        return contracts[:limit]

    def refresh_source(self, source_key: str) -> AggregationResult:
        """
        Refresca una fuente específica ignorando cache.

        Args:
            source_key: Clave de la fuente

        Returns:
            AggregationResult de la fuente
        """
        return self.aggregate(mode=AggregationMode.SELECTIVE, sources=[source_key], use_cache=False)

    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del agregador."""
        cache_stats = {
            "sources_cached": len(self._cache),
            "total_contracts_cached": sum(len(c) for c in self._cache.values()),
            "cache_age": {k: (datetime.now() - ts).total_seconds() for k, ts in self._cache_timestamps.items()},
        }

        registry_stats = self.registry.get_statistics()

        return {"cache": cache_stats, "registry": registry_stats}

    # =========================================================================
    # Métodos privados
    # =========================================================================

    def _select_sources(
        self, mode: AggregationMode, sources: Optional[List[str]], country: Optional[str]
    ) -> Dict[str, SourceConfig]:
        """Selecciona fuentes según el modo."""
        if mode == AggregationMode.SELECTIVE and sources:
            return {k: self.registry.get(k) for k in sources if self.registry.get(k) and self.registry.get(k).enabled}

        if mode == AggregationMode.COUNTRY and country:
            return self.registry.get_by_country(country)

        if mode == AggregationMode.PRIORITY:
            high = self.registry.get_by_priority(SourcePriority.CRITICAL)
            high.update(self.registry.get_by_priority(SourcePriority.HIGH))
            return high

        # FULL: todas las fuentes habilitadas
        return self.registry.get_enabled()

    def _fetch_source(
        self,
        config: SourceConfig,
        keywords: Optional[List[str]],
        min_amount: Optional[float],
        max_amount: Optional[float],
        days_back: int,
    ) -> tuple:
        """
        Extrae contratos de una fuente.

        Returns:
            (contracts, duration, error)
        """
        start_time = datetime.now()
        contracts = []
        error = None

        try:
            # Obtener scraper
            scraper = self.registry.get_scraper(config.key)

            if not scraper:
                raise ValueError(f"Scraper no disponible para {config.key}")

            # Ejecutar fetch con timeout para evitar que bloquee el scheduler
            _SCRAPER_TIMEOUT = 60  # segundos
            with ThreadPoolExecutor(max_workers=1) as _ex:
                _fut = _ex.submit(
                    scraper.fetch_contracts,
                    keywords=keywords, min_amount=min_amount, max_amount=max_amount, days_back=days_back,
                )
                try:
                    raw_contracts = _fut.result(timeout=_SCRAPER_TIMEOUT)
                except FuturesTimeoutError:
                    logger.error(f"Scraper {config.key} timeout after {_SCRAPER_TIMEOUT}s — skipping")
                    self.registry.update_status(config.key, SourceStatus.ERROR, f"Timeout >{_SCRAPER_TIMEOUT}s")
                    return [], 0, TimeoutError(f"Scraper {config.key} timeout")

            # Normalizar
            if raw_contracts:
                # Convertir ContractData a dict si es necesario
                raw_dicts = []
                for c in raw_contracts:
                    if hasattr(c, "to_dict"):
                        raw_dicts.append(c.to_dict())
                    elif hasattr(c, "__dict__"):
                        raw_dicts.append(c.__dict__)
                    else:
                        raw_dicts.append(c)

                contracts = self.normalizer.normalize_batch(raw_dicts, config.key, config.name)

            # Actualizar registro
            self.registry.record_fetch(config.key, len(contracts))

        except Exception as e:
            logger.error(f"Error fetching {config.key}: {e}")
            error = e
            self.registry.update_status(config.key, SourceStatus.ERROR, str(e))

        duration = (datetime.now() - start_time).total_seconds()
        return contracts, duration, error

    def _get_from_cache(self, source_key: str, ttl_minutes: int) -> Optional[List[NormalizedContract]]:
        """Obtiene contratos del cache si no ha expirado."""
        if source_key not in self._cache:
            return None

        timestamp = self._cache_timestamps.get(source_key)
        if not timestamp:
            return None

        age = datetime.now() - timestamp
        if age > timedelta(minutes=ttl_minutes):
            return None

        return self._cache[source_key]

    def _save_to_cache(self, source_key: str, contracts: List[NormalizedContract]):
        """Guarda contratos en cache."""
        self._cache[source_key] = contracts
        self._cache_timestamps[source_key] = datetime.now()

    def _deduplicate(self, contracts: List[NormalizedContract]) -> List[NormalizedContract]:
        """Elimina contratos duplicados."""
        seen_ids = set()
        unique = []

        for contract in contracts:
            # Usar external_id + source como clave única
            key = f"{contract.source}:{contract.external_id}"

            if key not in seen_ids:
                seen_ids.add(key)
                unique.append(contract)

        return unique

    def clear_cache(self, source_key: Optional[str] = None):
        """Limpia el cache."""
        if source_key:
            self._cache.pop(source_key, None)
            self._cache_timestamps.pop(source_key, None)
        else:
            self._cache.clear()
            self._cache_timestamps.clear()


# Singleton
_aggregator = None


def get_aggregator() -> UniversalAggregator:
    """Obtiene la instancia singleton del agregador."""
    global _aggregator
    if _aggregator is None:
        _aggregator = UniversalAggregator()
    return _aggregator
