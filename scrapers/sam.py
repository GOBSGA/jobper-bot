"""
Scraper para SAM.gov - System for Award Management (EEUU)
API: SAM.gov Opportunities API

Incluye CombinedScraper v3.0 optimizado con:
- Cache con TTL (15 min default)
- Ejecución paralela de scrapers
- Búsqueda de keywords con regex compilado
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from scrapers.base import BaseScraper, ContractData
from scrapers.secop import SecopScraper
from scrapers.optimization import OptimizedScraperWrapper, KeywordMatcher
from config import Config

logger = logging.getLogger(__name__)


class SamGovScraper(BaseScraper):
    """Scraper para la API de SAM.gov (Estados Unidos)."""

    def __init__(self):
        super().__init__(Config.SAM_API_URL)
        self.api_key = Config.SAM_API_KEY

    def is_available(self) -> bool:
        """Verifica si la API de SAM.gov está configurada."""
        return bool(self.api_key)

    def fetch_contracts(
        self,
        keywords: List[str] = None,
        min_amount: float = None,
        max_amount: float = None,
        days_back: int = 7
    ) -> List[ContractData]:
        """
        Obtiene oportunidades de SAM.gov.

        Args:
            keywords: Palabras clave para filtrar
            min_amount: Monto mínimo en USD
            max_amount: Monto máximo en USD
            days_back: Días hacia atrás para buscar

        Returns:
            Lista de ContractData normalizados
        """
        if not self.is_available():
            logger.warning("SAM.gov API key no configurada")
            return []

        params = self._build_query(keywords, min_amount, max_amount, days_back)

        logger.info(f"Consultando SAM.gov...")
        logger.debug(f"Query params: {params}")

        data = self._safe_request(self.api_url, params)

        if not data:
            logger.warning("No se obtuvieron datos de SAM.gov")
            return []

        # La respuesta de SAM.gov tiene estructura {opportunitiesData: [...]}
        opportunities = data.get("opportunitiesData", [])

        contracts = []
        for raw in opportunities:
            try:
                contract = self._normalize_contract(raw)
                contracts.append(contract)
            except Exception as e:
                logger.error(f"Error normalizando contrato SAM: {e}")
                continue

        logger.info(f"SAM.gov: {len(contracts)} oportunidades obtenidas")
        return contracts

    def _build_query(
        self,
        keywords: List[str] = None,
        min_amount: float = None,
        max_amount: float = None,
        days_back: int = 7
    ) -> dict:
        """Construye los parámetros de consulta para SAM.gov API."""

        # Fecha límite
        date_limit = (datetime.now() - timedelta(days=days_back)).strftime('%m/%d/%Y')

        params = {
            "api_key": self.api_key,
            "postedFrom": date_limit,
            "limit": 100,
            "offset": 0,
        }

        # Keywords como query string
        if keywords:
            # SAM.gov usa 'q' para búsqueda por texto
            params["q"] = " OR ".join(keywords[:5])  # Limitar a 5 keywords

        # Nota: SAM.gov no tiene filtro directo de monto en la API pública
        # El filtrado por monto se hace post-procesamiento

        return params

    def _normalize_contract(self, raw: dict) -> ContractData:
        """Normaliza una oportunidad de SAM.gov al formato estándar."""

        external_id = raw.get("noticeId", raw.get("solicitationNumber", ""))

        # Parsear fechas
        pub_date = self._parse_date(raw.get("postedDate"))
        deadline = self._parse_date(raw.get("responseDeadLine"))

        # Construir URL
        url = self._build_url(raw)

        # SAM.gov no siempre incluye monto directamente
        # Puede estar en archivos adjuntos o no disponible
        amount = None
        if raw.get("award"):
            try:
                amount = float(raw["award"].get("amount", 0))
            except (ValueError, TypeError):
                pass

        # Descripción
        description = raw.get("description", "")
        if not description:
            description = raw.get("additionalInfoLink", "")

        return ContractData(
            external_id=str(external_id),
            title=raw.get("title", "Sin título"),
            description=description[:1000] if description else "",
            entity=raw.get("fullParentPathName", raw.get("organizationName", "")),
            amount=amount,
            currency="USD",
            country="usa",
            source="SAM.gov",
            url=url,
            publication_date=pub_date,
            deadline=deadline,
            raw_data=raw,
        )

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parsea una fecha de SAM.gov."""
        if not date_str:
            return None

        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%m/%d/%Y",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                # Remover timezone info si existe
                clean_date = date_str.replace("Z", "+00:00")
                return datetime.strptime(clean_date[:19], fmt[:19].replace("%z", ""))
            except ValueError:
                continue

        return None

    def _build_url(self, raw: dict) -> str:
        """Construye la URL de la oportunidad en SAM.gov."""
        notice_id = raw.get("noticeId", "")
        if notice_id:
            return f"https://sam.gov/opp/{notice_id}/view"

        solicitation = raw.get("solicitationNumber", "")
        if solicitation:
            return f"https://sam.gov/search/?keywords={solicitation}"

        return "https://sam.gov"


# =============================================================================
# SCRAPER COMBINADO v3.0
# =============================================================================

class CombinedScraper:
    """
    Scraper que combina resultados de múltiples fuentes.

    v3.0 Optimizado:
    - Cache con TTL de 15 minutos (configurable)
    - Ejecución paralela de scrapers (5-10x más rápido)
    - Búsqueda de keywords con regex compilado O(L) vs O(K×L)

    Complejidades:
    - fetch_all sin cache: O(max_latency) paralelo + O(S×N) procesamiento
    - fetch_all con cache hit: O(1)
    - Filtro keywords: O(L) por contrato
    """

    def __init__(
        self,
        include_multilateral: bool = True,
        include_private: bool = True,
        include_latam: bool = True,
        cache_ttl_minutes: int = 15,
        max_parallel_workers: int = 10,
        use_cache: bool = True
    ):
        """
        Inicializa el scraper combinado con optimizaciones.

        Args:
            include_multilateral: Si True, incluye BID, Banco Mundial, ONU
            include_private: Si True, incluye portales privados (Ecopetrol, EPM)
            include_latam: Si True, incluye portales LATAM
            cache_ttl_minutes: Tiempo de vida del cache en minutos
            max_parallel_workers: Número máximo de workers paralelos
            use_cache: Si True, usa cache para evitar requests repetidos
        """
        # Fuentes gubernamentales (siempre incluidas)
        self.secop = SecopScraper()
        self.sam = SamGovScraper()

        # Fuentes multilaterales
        self.include_multilateral = include_multilateral
        self._multilateral_scrapers = None

        # Fuentes privadas
        self.include_private = include_private
        self._private_scrapers = None

        # Fuentes LATAM
        self.include_latam = include_latam
        self._latam_scrapers = None

        # Optimizaciones
        self._optimizer = OptimizedScraperWrapper(
            cache_ttl=cache_ttl_minutes,
            max_workers=max_parallel_workers
        )
        self._use_cache = use_cache
        self._keyword_matcher = KeywordMatcher()

    @property
    def multilateral_scrapers(self):
        """Lazy loading de scrapers multilaterales."""
        if self._multilateral_scrapers is None and self.include_multilateral:
            try:
                from scrapers.private.multilateral import IDBScraper, WorldBankScraper, UNGMScraper
                self._multilateral_scrapers = {
                    "idb": IDBScraper(),
                    "worldbank": WorldBankScraper(),
                    "ungm": UNGMScraper(),
                }
                logger.info("Scrapers multilaterales cargados")
            except ImportError as e:
                logger.warning(f"No se pudieron cargar scrapers multilaterales: {e}")
                self._multilateral_scrapers = {}
        return self._multilateral_scrapers or {}

    @property
    def private_scrapers(self):
        """Lazy loading de scrapers privados."""
        if self._private_scrapers is None and self.include_private:
            try:
                from scrapers.private.ecopetrol import EcopetrolScraper
                from scrapers.private.epm import EPMScraper
                self._private_scrapers = {
                    "ecopetrol": EcopetrolScraper(),
                    "epm": EPMScraper(),
                }
                logger.info("Scrapers privados cargados")
            except ImportError as e:
                logger.debug(f"Scrapers privados no disponibles: {e}")
                self._private_scrapers = {}
        return self._private_scrapers or {}

    @property
    def latam_scrapers(self):
        """Lazy loading de scrapers LATAM."""
        if self._latam_scrapers is None and self.include_latam:
            try:
                from scrapers.latam import (
                    CompraNetScraper,
                    ChileCompraScraper,
                    SeaceScraper,
                    ComprarScraper,
                    BrasilComprasNetScraper,
                    PetrobrasScraper,
                )
                self._latam_scrapers = {
                    "mexico": CompraNetScraper(),
                    "chile": ChileCompraScraper(),
                    "peru": SeaceScraper(),
                    "argentina": ComprarScraper(),
                    "brasil": BrasilComprasNetScraper(),
                    "petrobras": PetrobrasScraper(),
                }
                logger.info("🌎 Scrapers LATAM cargados: México, Chile, Perú, Argentina, Brasil + Petrobras")
            except ImportError as e:
                logger.warning(f"No se pudieron cargar scrapers LATAM: {e}")
                self._latam_scrapers = {}
        return self._latam_scrapers or {}

    def fetch_all(
        self,
        keywords: List[str] = None,
        min_amount_cop: float = None,
        max_amount_cop: float = None,
        countries: List[str] = None,
        days_back: int = 7,
        include_sources: List[str] = None,
        parallel: bool = True
    ) -> List[ContractData]:
        """
        Obtiene contratos de todas las fuentes configuradas.

        OPTIMIZADO v3.0:
        - Ejecución paralela: O(max_latency) vs O(sum_latencies)
        - Cache con TTL: O(1) para búsquedas repetidas
        - Keywords regex: O(L) vs O(K×L)

        Args:
            keywords: Palabras clave para filtrar
            min_amount_cop: Monto mínimo en COP (se convierte para otras monedas)
            max_amount_cop: Monto máximo en COP
            countries: Lista de países ["colombia", "usa", "multilateral", "all"]
            days_back: Días hacia atrás
            include_sources: Lista específica de fuentes
            parallel: Si True, ejecuta scrapers en paralelo (default: True)

        Returns:
            Lista combinada de contratos de todas las fuentes
        """
        import time
        start_time = time.time()

        # Normalizar países
        if countries is None or "all" in countries:
            countries = ["colombia", "usa", "multilateral", "mexico", "chile", "peru", "argentina", "brasil"]

        # Configurar keyword matcher para filtrado optimizado
        if keywords:
            self._keyword_matcher.set_keywords(include=keywords)

        # Conversión de moneda (aproximaciones)
        exchange_rates = Config.EXCHANGE_RATES if hasattr(Config, 'EXCHANGE_RATES') else {}
        usd_to_cop = exchange_rates.get("USD_TO_COP", 4000)

        # Tasas de cambio aproximadas (COP base)
        currency_rates = {
            "USD": 1 / usd_to_cop,
            "MXN": 0.0045,
            "CLP": 0.22,
            "PEN": 0.00092,
            "ARS": 0.22,
            "BRL": 0.0012,
            "COP": 1.0,
        }

        # Construir lista de tareas para ejecución paralela
        tasks = self._build_fetch_tasks(
            keywords=keywords,
            min_amount_cop=min_amount_cop,
            max_amount_cop=max_amount_cop,
            countries=countries,
            days_back=days_back,
            include_sources=include_sources,
            currency_rates=currency_rates
        )

        # Ejecutar en paralelo o secuencial
        if parallel and len(tasks) > 1:
            results = self._optimizer.fetch_parallel(tasks, use_cache=self._use_cache)
            all_contracts = []
            for source_name, contracts in results.items():
                if contracts:
                    all_contracts.extend(contracts)
                    logger.info(f"✅ {source_name}: {len(contracts)} contratos")
        else:
            # Ejecución secuencial (fallback)
            all_contracts = self._fetch_sequential(tasks)

        elapsed = time.time() - start_time
        logger.info(f"⚡ Total: {len(all_contracts)} contratos en {elapsed:.2f}s")

        return all_contracts

    def _build_fetch_tasks(
        self,
        keywords: List[str],
        min_amount_cop: float,
        max_amount_cop: float,
        countries: List[str],
        days_back: int,
        include_sources: List[str],
        currency_rates: dict
    ) -> List[tuple]:
        """
        Construye la lista de tareas para ejecución paralela.

        Returns:
            Lista de tuplas (nombre, función, kwargs)
        """
        tasks = []

        def should_include(source: str, country: str) -> bool:
            """Verifica si una fuente debe incluirse."""
            if include_sources and source not in include_sources:
                return False
            if country not in countries and country != "multilateral":
                return False
            return True

        def convert_amount(amount: float, currency: str) -> float:
            """Convierte monto de COP a otra moneda."""
            if amount is None:
                return None
            return amount * currency_rates.get(currency, 1.0)

        # SECOP (Colombia)
        if should_include("secop", "colombia"):
            tasks.append((
                "secop",
                self.secop.fetch_contracts,
                {
                    "keywords": keywords,
                    "min_amount": min_amount_cop,
                    "max_amount": max_amount_cop,
                    "days_back": days_back
                }
            ))

        # SAM.gov (USA)
        if should_include("sam", "usa"):
            tasks.append((
                "sam",
                self.sam.fetch_contracts,
                {
                    "keywords": keywords,
                    "min_amount": convert_amount(min_amount_cop, "USD"),
                    "max_amount": convert_amount(max_amount_cop, "USD"),
                    "days_back": days_back
                }
            ))

        # Multilaterales
        if "multilateral" in countries and self.include_multilateral:
            for key, scraper in self.multilateral_scrapers.items():
                if include_sources and key not in include_sources:
                    continue
                tasks.append((
                    key,
                    scraper.fetch_contracts,
                    {
                        "keywords": keywords,
                        "min_amount": convert_amount(min_amount_cop, "USD"),
                        "max_amount": convert_amount(max_amount_cop, "USD"),
                        "days_back": days_back
                    }
                ))

        # Privados (Colombia)
        if "colombia" in countries and self.include_private:
            for key, scraper in self.private_scrapers.items():
                if include_sources and key not in include_sources:
                    continue
                tasks.append((
                    key,
                    scraper.fetch_contracts,
                    {
                        "keywords": keywords,
                        "min_amount": min_amount_cop,
                        "max_amount": max_amount_cop,
                        "days_back": days_back
                    }
                ))

        # LATAM
        if self.include_latam:
            latam_config = {
                "mexico": ("MXN", "mexico"),
                "chile": ("CLP", "chile"),
                "peru": ("PEN", "peru"),
                "argentina": ("ARS", "argentina"),
                "brasil": ("BRL", "brasil"),
                "petrobras": ("BRL", "brasil"),
            }

            for key, (currency, country) in latam_config.items():
                if not should_include(key, country):
                    continue

                scraper = self.latam_scrapers.get(key)
                if not scraper:
                    continue

                tasks.append((
                    key,
                    scraper.fetch_contracts,
                    {
                        "keywords": keywords,
                        "min_amount": convert_amount(min_amount_cop, currency),
                        "max_amount": convert_amount(max_amount_cop, currency),
                        "days_back": days_back
                    }
                ))

        return tasks

    def _fetch_sequential(self, tasks: List[tuple]) -> List[ContractData]:
        """Ejecuta tareas secuencialmente (fallback)."""
        all_contracts = []
        for name, func, kwargs in tasks:
            try:
                contracts = func(**kwargs)
                all_contracts.extend(contracts)
                logger.info(f"✅ {name}: {len(contracts)} contratos")
            except Exception as e:
                logger.error(f"❌ {name}: {e}")
        return all_contracts

    def get_cache_stats(self) -> dict:
        """Retorna estadísticas del cache."""
        return self._optimizer.get_cache_stats()

    def clear_cache(self) -> None:
        """Limpia el cache."""
        self._optimizer.cache.clear()
        logger.info("🗑️ Cache limpiado")

    def get_available_sources(self) -> dict:
        """Retorna información sobre las fuentes disponibles."""
        sources = {
            "government": {
                "secop": {"name": "SECOP II", "country": "colombia", "available": True},
                "sam": {"name": "SAM.gov", "country": "usa", "available": self.sam.is_available()},
            },
            "multilateral": {},
            "private": {},
            "latam": {}
        }

        for key, scraper in self.multilateral_scrapers.items():
            sources["multilateral"][key] = {
                "name": scraper.portal_name,
                "country": scraper.portal_country,
                "available": True
            }

        for key, scraper in self.private_scrapers.items():
            sources["private"][key] = {
                "name": scraper.portal_name,
                "country": scraper.portal_country,
                "available": True
            }

        # LATAM sources
        latam_info = {
            "mexico": {"name": "CompraNet", "country": "mexico"},
            "chile": {"name": "ChileCompra", "country": "chile"},
            "peru": {"name": "SEACE", "country": "peru"},
            "argentina": {"name": "COMPR.AR", "country": "argentina"},
            "brasil": {"name": "ComprasNet", "country": "brasil"},
            "petrobras": {"name": "Petrobras", "country": "brasil"},
        }
        for key, info in latam_info.items():
            if key in self.latam_scrapers:
                sources["latam"][key] = {
                    "name": info["name"],
                    "country": info["country"],
                    "available": True
                }

        return sources
