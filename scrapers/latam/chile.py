"""
Scraper para ChileCompra - Sistema de Contratación Pública de Chile
API: Mercado Público (api.mercadopublico.cl)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from scrapers.base import BaseScraper, ContractData

logger = logging.getLogger(__name__)

# ChileCompra API
CHILECOMPRA_API_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"


class ChileCompraScraper(BaseScraper):
    """Scraper para la API de ChileCompra (Chile)."""

    def __init__(self, api_ticket: str = None):
        """
        Inicializa el scraper de ChileCompra.

        Args:
            api_ticket: Ticket de API de mercadopublico.cl (opcional para consultas básicas)
        """
        super().__init__(CHILECOMPRA_API_URL)
        self.api_ticket = api_ticket

    def fetch_contracts(
        self,
        keywords: List[str] = None,
        min_amount: float = None,
        max_amount: float = None,
        days_back: int = 7
    ) -> List[ContractData]:
        """
        Obtiene licitaciones de ChileCompra.

        Args:
            keywords: Palabras clave para filtrar
            min_amount: Monto mínimo en CLP
            max_amount: Monto máximo en CLP
            days_back: Días hacia atrás para buscar

        Returns:
            Lista de ContractData normalizados
        """
        params = self._build_query(keywords, min_amount, max_amount, days_back)

        logger.info("🇨🇱 Consultando ChileCompra...")
        logger.debug(f"Query params: {params}")

        data = self._safe_request(self.api_url, params)

        if not data:
            logger.warning("No se obtuvieron datos de ChileCompra")
            return []

        # ChileCompra devuelve {"Listado": [...]}
        results = data.get("Listado", []) if isinstance(data, dict) else data

        contracts = []
        for raw in results:
            try:
                contract = self._normalize_contract(raw)
                if contract:
                    contracts.append(contract)
            except Exception as e:
                logger.error(f"Error normalizando contrato Chile: {e}")
                continue

        logger.info(f"✅ ChileCompra: {len(contracts)} licitaciones obtenidas")
        return contracts

    def _build_query(
        self,
        keywords: List[str] = None,
        min_amount: float = None,
        max_amount: float = None,
        days_back: int = 7
    ) -> dict:
        """Construye los parámetros de consulta para ChileCompra."""

        date_start = (datetime.now() - timedelta(days=days_back)).strftime('%d%m%Y')
        date_end = datetime.now().strftime('%d%m%Y')

        params = {
            "fecha": f"{date_start}-{date_end}",
            "estado": "activas",  # Solo licitaciones activas
        }

        # API ticket si está disponible
        if self.api_ticket:
            params["ticket"] = self.api_ticket

        # Filtro de keywords
        if keywords:
            params["nombre"] = " ".join(keywords)

        return params

    def _normalize_contract(self, raw: dict) -> Optional[ContractData]:
        """Normaliza una licitación de ChileCompra al formato estándar."""

        external_id = raw.get("CodigoExterno") or raw.get("Codigo", "")
        if not external_id:
            return None

        # Parsear fechas
        pub_date = self._parse_date(raw.get("FechaPublicacion"))
        deadline = self._parse_date(raw.get("FechaCierre"))

        # Parsear monto
        amount = None
        monto_str = raw.get("MontoEstimado") or raw.get("Monto")
        if monto_str:
            try:
                # ChileCompra puede enviar montos como string con puntos
                amount = float(str(monto_str).replace(".", "").replace(",", "."))
            except (ValueError, TypeError):
                pass

        # Construir URL
        url = self._build_url(raw)

        return ContractData(
            external_id=str(external_id),
            title=raw.get("Nombre", "Sin título"),
            description=raw.get("Descripcion", ""),
            entity=raw.get("NombreOrganismo") or raw.get("Organismo", ""),
            amount=amount,
            currency="CLP",
            country="chile",
            source="ChileCompra",
            url=url,
            publication_date=pub_date,
            deadline=deadline,
            raw_data=raw,
        )

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parsea fechas de ChileCompra."""
        if not date_str:
            return None

        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y %H:%M",
            "%d-%m-%Y",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(date_str)[:26], fmt)
            except ValueError:
                continue

        return None

    def _build_url(self, raw: dict) -> str:
        """Construye la URL del proceso en ChileCompra."""
        codigo = raw.get("CodigoExterno") or raw.get("Codigo", "")
        if codigo:
            return f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?qs=/{codigo}"

        return "https://www.mercadopublico.cl/"
