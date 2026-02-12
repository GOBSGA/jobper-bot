"""
Base scraper para portales privados y multilaterales
Extiende BaseScraper con soporte para autenticación
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import Any, Dict, List, Optional

from scrapers.base import BaseScraper, ContractData

logger = logging.getLogger(__name__)


class PrivatePortalScraper(BaseScraper):
    """
    Scraper base para portales privados que pueden requerir autenticación.

    Extiende BaseScraper agregando:
    - Soporte para autenticación (login/session)
    - Manejo de cookies y tokens
    - Verificación de sesión válida
    """

    # Metadatos del portal (override en subclases)
    portal_name: str = "Portal Privado"
    portal_country: str = "multilateral"
    source_type: str = "private"
    requires_authentication: bool = False

    def __init__(self, api_url: str, credentials: Optional[Dict[str, str]] = None, timeout: int = 30):
        """
        Inicializa el scraper de portal privado.

        Args:
            api_url: URL base del API o portal
            credentials: Diccionario con credenciales (usuario, password, api_key, etc.)
            timeout: Timeout para requests en segundos
        """
        super().__init__(api_url, timeout)
        self.credentials = credentials or {}
        self._authenticated = False
        self._session_token: Optional[str] = None
        self._cookies: Dict[str, str] = {}

    @property
    def is_authenticated(self) -> bool:
        """Verifica si hay una sesión autenticada activa."""
        return self._authenticated

    def authenticate(self) -> bool:
        """
        Realiza autenticación contra el portal.

        Override este método en subclases que requieren auth.

        Returns:
            bool: True si la autenticación fue exitosa
        """
        if not self.requires_authentication:
            self._authenticated = True
            return True

        # Implementar en subclases
        logger.warning(f"{self.portal_name}: authenticate() no implementado")
        return False

    def is_session_valid(self) -> bool:
        """
        Verifica si la sesión actual sigue siendo válida.

        Override en subclases para verificación específica.

        Returns:
            bool: True si la sesión es válida
        """
        return self._authenticated

    def ensure_authenticated(self) -> bool:
        """
        Asegura que hay una sesión autenticada válida.

        Returns:
            bool: True si hay sesión válida (existente o nueva)
        """
        if self.is_session_valid():
            return True

        logger.info(f"{self.portal_name}: Iniciando autenticación...")
        return self.authenticate()

    def fetch_contracts(
        self,
        keywords: Optional[List[str]] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        days_back: int = 30,
    ) -> List[ContractData]:
        """
        Obtiene contratos del portal.

        Args:
            keywords: Lista de palabras clave para filtrar
            min_amount: Monto mínimo del contrato
            max_amount: Monto máximo del contrato
            days_back: Días hacia atrás para buscar

        Returns:
            Lista de ContractData normalizados
        """
        # Verificar autenticación si es necesaria
        if self.requires_authentication:
            if not self.ensure_authenticated():
                logger.error(f"{self.portal_name}: No se pudo autenticar")
                return []

        try:
            return self._fetch_contracts_impl(
                keywords=keywords, min_amount=min_amount, max_amount=max_amount, days_back=days_back
            )
        except Exception as e:
            logger.error(f"{self.portal_name}: Error fetching contracts: {e}")
            return []

    @abstractmethod
    def _fetch_contracts_impl(
        self,
        keywords: Optional[List[str]] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        days_back: int = 30,
    ) -> List[ContractData]:
        """
        Implementación del fetch de contratos.

        Override en subclases con la lógica específica del portal.
        """
        pass

    def _get_headers(self) -> Dict[str, str]:
        """
        Obtiene headers para requests, incluyendo token de sesión si existe.

        Returns:
            Dict con headers HTTP
        """
        headers = {
            "User-Agent": "Jobper-Bot/3.0 (Contract Monitor)",
            "Accept": "application/json",
            "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
        }

        if self._session_token:
            headers["Authorization"] = f"Bearer {self._session_token}"

        return headers

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Realiza una request al portal con manejo de errores.

        Args:
            endpoint: Endpoint relativo o URL completa
            method: Método HTTP (GET, POST, etc.)
            params: Query parameters
            data: Form data
            json_data: JSON body

        Returns:
            Respuesta parseada como dict o None si hay error
        """
        import requests

        url = endpoint if endpoint.startswith("http") else f"{self.api_url}/{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                headers=self._get_headers(),
                cookies=self._cookies,
                timeout=self.timeout,
            )

            response.raise_for_status()

            # Actualizar cookies si las hay
            if response.cookies:
                self._cookies.update(dict(response.cookies))

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"{self.portal_name}: Request error: {e}")
            return None

    def logout(self) -> None:
        """Cierra la sesión actual."""
        self._authenticated = False
        self._session_token = None
        self._cookies = {}
        logger.info(f"{self.portal_name}: Sesión cerrada")
