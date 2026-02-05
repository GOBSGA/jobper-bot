"""
Scraper para SEACE - Sistema Electrónico de Contrataciones del Estado (Perú)
API: SEACE API (seace.gob.pe)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from scrapers.base import BaseScraper, ContractData

logger = logging.getLogger(__name__)

# SEACE API - Perú
# Nota: SEACE tiene una API de datos abiertos limitada, usamos el endpoint público
SEACE_API_URL = "https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml"
SEACE_DATA_URL = "https://datosabiertos.gob.pe/api/v1/datastore_search"


class SeaceScraper(BaseScraper):
    """Scraper para SEACE (Perú)."""

    def __init__(self):
        super().__init__(SEACE_DATA_URL)

    def fetch_contracts(
        self,
        keywords: List[str] = None,
        min_amount: float = None,
        max_amount: float = None,
        days_back: int = 7
    ) -> List[ContractData]:
        """
        Obtiene procesos de SEACE.

        Args:
            keywords: Palabras clave para filtrar
            min_amount: Monto mínimo en PEN (soles)
            max_amount: Monto máximo en PEN
            days_back: Días hacia atrás para buscar

        Returns:
            Lista de ContractData normalizados
        """
        params = self._build_query(keywords, min_amount, max_amount, days_back)

        logger.info("🇵🇪 Consultando SEACE Perú...")
        logger.debug(f"Query params: {params}")

        data = self._safe_request(self.api_url, params)

        if not data:
            logger.warning("No se obtuvieron datos de SEACE")
            return []

        # Datos Abiertos Perú devuelve {"result": {"records": [...]}}
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
                logger.error(f"Error normalizando contrato Perú: {e}")
                continue

        logger.info(f"✅ SEACE: {len(contracts)} procesos obtenidos")
        return contracts

    def _build_query(
        self,
        keywords: List[str] = None,
        min_amount: float = None,
        max_amount: float = None,
        days_back: int = 7
    ) -> dict:
        """Construye los parámetros de consulta para SEACE."""

        # Resource ID para el dataset de contrataciones públicas
        params = {
            "resource_id": "contrataciones-publicas",  # ID del dataset
            "limit": 200,
        }

        # Construir filtros
        filters = {}

        # Filtro de fecha (si está disponible en el dataset)
        date_limit = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        filters["fecha_publicacion"] = {"gte": date_limit}

        # Filtro de keywords
        if keywords:
            params["q"] = " ".join(keywords)

        if filters:
            import json
            params["filters"] = json.dumps(filters)

        return params

    def _normalize_contract(self, raw: dict) -> Optional[ContractData]:
        """Normaliza un proceso de SEACE al formato estándar."""

        external_id = (raw.get("numero_proceso") or
                       raw.get("codigo_convocatoria") or
                       raw.get("_id", ""))
        if not external_id:
            return None

        # Parsear fechas
        pub_date = self._parse_date(raw.get("fecha_publicacion") or
                                     raw.get("fecha_convocatoria"))
        deadline = self._parse_date(raw.get("fecha_presentacion_propuestas") or
                                     raw.get("fecha_cierre"))

        # Parsear monto
        amount = None
        for field in ["valor_referencial", "monto_total", "valor_estimado"]:
            if raw.get(field):
                try:
                    amount = float(str(raw[field]).replace(",", ""))
                    if amount > 0:
                        break
                except (ValueError, TypeError):
                    continue

        # Construir URL
        url = self._build_url(raw)

        return ContractData(
            external_id=str(external_id),
            title=raw.get("objeto_convocatoria") or raw.get("descripcion", "Sin título"),
            description=raw.get("descripcion") or raw.get("objeto_convocatoria", ""),
            entity=raw.get("entidad") or raw.get("nombre_entidad", ""),
            amount=amount,
            currency="PEN",
            country="peru",
            source="SEACE",
            url=url,
            publication_date=pub_date,
            deadline=deadline,
            raw_data=raw,
        )

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parsea fechas de SEACE."""
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
        """Construye la URL del proceso en SEACE."""
        numero = raw.get("numero_proceso") or raw.get("codigo_convocatoria", "")
        if numero:
            return f"https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml?nroProc={numero}"

        return "https://prod2.seace.gob.pe/seacebus-uiwd-pub/"
