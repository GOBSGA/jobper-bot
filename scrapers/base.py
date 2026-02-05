"""
Clase base para scrapers de licitaciones
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import logging

import requests

logger = logging.getLogger(__name__)


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
        Realiza una petición HTTP de forma segura con manejo de errores.

        Returns:
            Respuesta JSON o None si hay error
        """
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout conectando a {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"Error de conexión a {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return None
