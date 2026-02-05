"""
Clase base para scrapers de licitaciones.
Incluye retry con exponential backoff y rate limiting.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import logging

import requests

logger = logging.getLogger(__name__)

# Default retry config
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, doubles each retry
RATE_LIMIT_DELAY = 0.5  # seconds between requests


@dataclass
class ContractData:
    """Estructura de datos normalizada para contratos de cualquier fuente."""

    external_id: str
    title: str
    description: Optional[str]
    entity: Optional[str]
    amount: Optional[float]
    currency: str
    country: str
    source: str
    url: Optional[str]
    publication_date: Optional[datetime]
    deadline: Optional[datetime]
    raw_data: dict

    def to_dict(self) -> dict:
        """Convierte a diccionario para almacenamiento."""
        return {
            "external_id": self.external_id,
            "title": self.title,
            "description": self.description,
            "entity": self.entity,
            "amount": self.amount,
            "currency": self.currency,
            "country": self.country,
            "source": self.source,
            "url": self.url,
            "publication_date": self.publication_date,
            "deadline": self.deadline,
            "raw_data": self.raw_data,
        }


class BaseScraper(ABC):
    """Clase base abstracta para scrapers de APIs de licitaciones."""

    def __init__(self, api_url: str, timeout: int = 30):
        self.api_url = api_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "Jobper-Bot/2.0"
        })

    @abstractmethod
    def fetch_contracts(
        self,
        keywords: List[str] = None,
        min_amount: float = None,
        max_amount: float = None,
        days_back: int = 7
    ) -> List[ContractData]:
        """
        Obtiene contratos de la API según los filtros.

        Args:
            keywords: Lista de palabras clave para filtrar
            min_amount: Monto mínimo del contrato
            max_amount: Monto máximo del contrato
            days_back: Días hacia atrás para buscar

        Returns:
            Lista de ContractData normalizados
        """
        pass

    @abstractmethod
    def _normalize_contract(self, raw_contract: dict) -> ContractData:
        """
        Normaliza un contrato crudo de la API al formato estándar.

        Args:
            raw_contract: Datos crudos de la API

        Returns:
            ContractData normalizado
        """
        pass

    def _safe_request(self, url: str, params: dict = None) -> Optional[dict]:
        """
        HTTP request with retry (exponential backoff) and rate limiting.

        Retries up to MAX_RETRIES on timeout/connection errors.
        Waits RATE_LIMIT_DELAY between requests to avoid API throttling.
        """
        # Rate limiting between requests
        time.sleep(RATE_LIMIT_DELAY)

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                last_error = f"Timeout conectando a {url}"
                logger.warning(f"{last_error} (intento {attempt + 1}/{MAX_RETRIES})")
            except requests.exceptions.ConnectionError:
                last_error = f"Error de conexión a {url}"
                logger.warning(f"{last_error} (intento {attempt + 1}/{MAX_RETRIES})")
            except requests.exceptions.HTTPError as e:
                status = getattr(e.response, "status_code", None)
                # Don't retry on 4xx client errors (except 429 rate limit)
                if status and 400 <= status < 500 and status != 429:
                    logger.error(f"HTTP {status}: {e}")
                    return None
                last_error = f"HTTP error: {e}"
                logger.warning(f"{last_error} (intento {attempt + 1}/{MAX_RETRIES})")
            except Exception as e:
                logger.error(f"Error inesperado: {e}")
                return None

            # Exponential backoff before retry
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF * (2 ** attempt)
                logger.info(f"Reintentando en {wait}s...")
                time.sleep(wait)

        logger.error(f"Todos los reintentos fallaron: {last_error}")
        return None
