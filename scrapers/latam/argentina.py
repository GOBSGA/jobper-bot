"""
Scraper para COMPR.AR - Sistema de Contrataciones de Argentina
API: COMPR.AR API (comprar.gob.ar)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from scrapers.base import BaseScraper, ContractData

logger = logging.getLogger(__name__)

# COMPR.AR API - Argentina
COMPRAR_API_URL = "https://comprar.gob.ar/PLIEG/buscadorProcesos.aspx"
COMPRAR_DATA_URL = "https://datos.gob.ar/api/3/action/datastore_search"


class ComprarScraper(BaseScraper):
    """Scraper para COMPR.AR (Argentina)."""

    def __init__(self):
        super().__init__(COMPRAR_DATA_URL)

    def fetch_contracts(
        self, keywords: List[str] = None, min_amount: float = None, max_amount: float = None, days_back: int = 7
    ) -> List[ContractData]:
        """
        Obtiene contrataciones de COMPR.AR.

        Args:
            keywords: Palabras clave para filtrar
            min_amount: Monto mínimo en ARS (pesos argentinos)
            max_amount: Monto máximo en ARS
            days_back: Días hacia atrás para buscar

        Returns:
            Lista de ContractData normalizados
        """
        params = self._build_query(keywords, min_amount, max_amount, days_back)

        logger.info("🇦🇷 Consultando COMPR.AR Argentina...")
        logger.debug(f"Query params: {params}")

        data = self._safe_request(self.api_url, params)

        if not data:
            logger.warning("No se obtuvieron datos de COMPR.AR")
            return []

        # Datos.gob.ar devuelve {"result": {"records": [...]}}
        results = []
        if isinstance(data, dict):
            result = data.get("result", {})
            results = result.get("records", []) if isinstance(result, dict) else []
        elif isinstance(data, list):
            results = data

        contracts = []
        for raw in results:
            try:
                contract = self._normalize_contract(raw)
                if contract:
                    contracts.append(contract)
            except Exception as e:
                logger.error(f"Error normalizando contrato Argentina: {e}")
                continue

        logger.info(f"✅ COMPR.AR: {len(contracts)} contrataciones obtenidas")
        return contracts

    def _build_query(
        self, keywords: List[str] = None, min_amount: float = None, max_amount: float = None, days_back: int = 7
    ) -> dict:
        """Construye los parámetros de consulta para COMPR.AR."""

        # Resource ID para contrataciones públicas de Argentina
        params = {
            "resource_id": "contrataciones-publicas",
            "limit": 200,
        }

        # Filtro de búsqueda por keywords
        if keywords:
            params["q"] = " ".join(keywords)

        # Filtros adicionales
        filters = {}
        date_limit = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        # Intentar filtrar por fecha
        filters["fecha_publicacion"] = {"gte": date_limit}

        if filters:
            import json

            params["filters"] = json.dumps(filters)

        return params

    def _normalize_contract(self, raw: dict) -> Optional[ContractData]:
        """Normaliza una contratación de COMPR.AR al formato estándar."""

        external_id = raw.get("numero_proceso") or raw.get("numero_expediente") or raw.get("id", "")
        if not external_id:
            return None

        # Parsear fechas
        pub_date = self._parse_date(raw.get("fecha_publicacion") or raw.get("fecha_apertura"))
        deadline = self._parse_date(raw.get("fecha_limite_oferta") or raw.get("fecha_cierre"))

        # Parsear monto
        amount = None
        for field in ["monto_estimado", "presupuesto_oficial", "monto_total"]:
            if raw.get(field):
                try:
                    # Limpiar formato argentino (puntos como separador de miles)
                    monto_str = str(raw[field]).replace(".", "").replace(",", ".")
                    amount = float(monto_str)
                    if amount > 0:
                        break
                except (ValueError, TypeError):
                    continue

        # Construir URL
        url = self._build_url(raw)

        return ContractData(
            external_id=str(external_id),
            title=raw.get("objeto") or raw.get("descripcion", "Sin título"),
            description=raw.get("descripcion") or raw.get("objeto", ""),
            entity=raw.get("organismo") or raw.get("unidad_contratante", ""),
            amount=amount,
            currency="ARS",
            country="argentina",
            source="COMPR.AR",
            url=url,
            publication_date=pub_date,
            deadline=deadline,
            raw_data=raw,
        )

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parsea fechas de COMPR.AR."""
        if not date_str:
            return None

        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(date_str)[:26], fmt)
            except ValueError:
                continue

        return None

    def _build_url(self, raw: dict) -> str:
        """Construye la URL del proceso en COMPR.AR."""
        numero = raw.get("numero_proceso") or raw.get("numero_expediente", "")
        if numero:
            return f"https://comprar.gob.ar/PLIEG/buscadorProcesos.aspx?nro={numero}"

        return "https://comprar.gob.ar/"
