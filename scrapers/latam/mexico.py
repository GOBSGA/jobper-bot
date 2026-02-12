"""
Scraper para CompraNet - Sistema de Contratación Pública de México
API: Datos Abiertos México (datos.gob.mx)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from scrapers.base import BaseScraper, ContractData

logger = logging.getLogger(__name__)

# CompraNet API - Datos Abiertos México
COMPRANET_API_URL = "https://api.datos.gob.mx/v1/compranet"


class CompraNetScraper(BaseScraper):
    """Scraper para la API de CompraNet (México)."""

    def __init__(self):
        super().__init__(COMPRANET_API_URL)

    def fetch_contracts(
        self, keywords: List[str] = None, min_amount: float = None, max_amount: float = None, days_back: int = 7
    ) -> List[ContractData]:
        """
        Obtiene contratos de CompraNet.

        Args:
            keywords: Palabras clave para filtrar
            min_amount: Monto mínimo en MXN
            max_amount: Monto máximo en MXN
            days_back: Días hacia atrás para buscar

        Returns:
            Lista de ContractData normalizados
        """
        params = self._build_query(keywords, min_amount, max_amount, days_back)

        logger.info("🇲🇽 Consultando CompraNet México...")
        logger.debug(f"Query params: {params}")

        data = self._safe_request(self.api_url, params)

        if not data:
            logger.warning("No se obtuvieron datos de CompraNet")
            return []

        # La API de datos.gob.mx devuelve {"results": [...]}
        results = data.get("results", data) if isinstance(data, dict) else data

        contracts = []
        for raw in results:
            try:
                contract = self._normalize_contract(raw)
                if contract:
                    contracts.append(contract)
            except Exception as e:
                logger.error(f"Error normalizando contrato México: {e}")
                continue

        logger.info(f"✅ CompraNet: {len(contracts)} contratos obtenidos")
        return contracts

    def _build_query(
        self, keywords: List[str] = None, min_amount: float = None, max_amount: float = None, days_back: int = 7
    ) -> dict:
        """Construye los parámetros de consulta para CompraNet."""

        date_limit = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        params = {
            "pageSize": 200,
            "fecha_inicio": date_limit,
        }

        # Filtro de keywords
        if keywords:
            # Buscar en descripción
            params["descripcion_anuncio"] = keywords[0] if keywords else ""

        # Filtros de monto (MXN)
        if min_amount:
            params["monto_minimo"] = min_amount
        if max_amount:
            params["monto_maximo"] = max_amount

        return params

    def _normalize_contract(self, raw: dict) -> Optional[ContractData]:
        """Normaliza un contrato de CompraNet al formato estándar."""

        external_id = raw.get("codigo_expediente") or raw.get("numero_procedimiento", "")
        if not external_id:
            return None

        # Parsear fechas
        pub_date = self._parse_date(raw.get("fecha_inicio_recepcion_propuestas") or raw.get("fecha_publicacion"))
        deadline = self._parse_date(raw.get("fecha_apertura_proposiciones") or raw.get("fecha_limite"))

        # Parsear monto
        amount = None
        for field in ["monto_total", "importe_contrato", "monto_maximo"]:
            if raw.get(field):
                try:
                    amount = float(raw[field])
                    if amount > 0:
                        break
                except (ValueError, TypeError):
                    continue

        # Construir URL
        url = self._build_url(raw)

        return ContractData(
            external_id=str(external_id),
            title=raw.get("titulo_expediente") or raw.get("descripcion_anuncio", "Sin título"),
            description=raw.get("descripcion_anuncio", ""),
            entity=raw.get("nombre_de_la_uc") or raw.get("unidad_compradora", ""),
            amount=amount,
            currency="MXN",
            country="mexico",
            source="CompraNet",
            url=url,
            publication_date=pub_date,
            deadline=deadline,
            raw_data=raw,
        )

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parsea fechas de CompraNet."""
        if not date_str:
            return None

        formats = [
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(date_str)[:26], fmt)
            except ValueError:
                continue

        return None

    def _build_url(self, raw: dict) -> str:
        """Construye la URL del proceso en CompraNet."""
        # URL directa si existe
        if raw.get("url_expediente"):
            return raw["url_expediente"]

        # Construir URL basada en código
        codigo = raw.get("codigo_expediente", "")
        if codigo:
            return f"https://compranet.hacienda.gob.mx/esop/toolkit/opportunity/opportunityDetail.do?oppId={codigo}"

        return "https://compranet.hacienda.gob.mx/"
