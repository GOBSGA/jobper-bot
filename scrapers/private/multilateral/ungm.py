"""
Scraper para UNGM (United Nations Global Marketplace)
Obtiene oportunidades de procurement de Naciones Unidas
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from scrapers.base import ContractData
from scrapers.private.base_private import PrivatePortalScraper

logger = logging.getLogger(__name__)


class UNGMScraper(PrivatePortalScraper):
    """
    Scraper para oportunidades de Naciones Unidas via UNGM.

    UNGM (United Nations Global Marketplace) es el portal central
    de procurement para todas las agencias de la ONU.

    URL: https://www.ungm.org/Public/Notice
    Nota: UNGM no tiene API pública, requiere web scraping.
    """

    portal_name = "ONU (UNGM)"
    portal_country = "multilateral"
    source_type = "multilateral"
    requires_authentication = False

    # URL base de UNGM
    BASE_URL = "https://www.ungm.org"
    NOTICES_URL = "https://www.ungm.org/Public/Notice"

    def __init__(self):
        super().__init__(api_url=self.NOTICES_URL)

    def _fetch_contracts_impl(
        self,
        keywords: Optional[List[str]] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        days_back: int = 30,
    ) -> List[ContractData]:
        """
        Obtiene oportunidades de procurement de UNGM.

        UNGM no tiene API pública, así que usamos web scraping
        de su página de notices públicos.
        """
        contracts = []

        try:
            import requests
            from bs4 import BeautifulSoup

            # Obtener página de notices
            headers = self._get_headers()
            headers["Accept"] = "text/html,application/xhtml+xml"

            # UNGM usa un sistema de búsqueda con POST
            # Primero obtenemos la página principal
            response = requests.get(self.NOTICES_URL, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # Buscar notices en la tabla/lista
            # La estructura de UNGM puede variar, intentamos varios selectores
            notice_elements = (
                soup.select(".notice-item")
                or soup.select("table.notices tbody tr")
                or soup.select(".tenderList .tender-item")
                or soup.select("[data-notice-id]")
            )

            if not notice_elements:
                # Intentar buscar links a notices
                notice_links = soup.select('a[href*="/Public/Notice/"]')
                for link in notice_links[:50]:
                    href = link.get("href", "")
                    if "/Public/Notice/" in href:
                        notice_id = href.split("/")[-1]
                        if notice_id.isdigit():
                            contract = self._fetch_notice_detail(notice_id, keywords)
                            if contract:
                                contracts.append(contract)

            else:
                for element in notice_elements[:50]:
                    try:
                        contract = self._parse_notice_element(element, keywords)
                        if contract:
                            contracts.append(contract)
                    except Exception as e:
                        logger.debug(f"Error parsing UNGM element: {e}")
                        continue

            logger.info(f"{self.portal_name}: {len(contracts)} oportunidades encontradas")

        except Exception as e:
            logger.error(f"{self.portal_name}: Error fetching: {e}")

        return contracts

    def _parse_notice_element(self, element, keywords: Optional[List[str]] = None) -> Optional[ContractData]:
        """Parsea un elemento HTML de notice."""
        try:
            # Intentar extraer ID del notice
            notice_id = element.get("data-notice-id")
            if not notice_id:
                link = element.select_one('a[href*="/Notice/"]')
                if link:
                    href = link.get("href", "")
                    parts = href.split("/")
                    notice_id = parts[-1] if parts else None

            if not notice_id:
                return None

            # Título
            title_elem = element.select_one(".title, h3, h4, td:first-child a")
            title = title_elem.get_text(strip=True) if title_elem else ""

            if not title:
                return None

            # Filtrar por keywords si existen
            if keywords:
                text_lower = title.lower()
                if not any(kw.lower() in text_lower for kw in keywords):
                    return None

            # Agencia/Entidad
            agency_elem = element.select_one(".agency, .organization, td:nth-child(2)")
            agency = agency_elem.get_text(strip=True) if agency_elem else "Naciones Unidas"

            # Fecha de deadline
            deadline_elem = element.select_one(".deadline, .closing-date, td:nth-child(3)")
            deadline = None
            if deadline_elem:
                deadline = self._parse_ungm_date(deadline_elem.get_text(strip=True))

            # URL
            url = f"{self.BASE_URL}/Public/Notice/{notice_id}"

            return ContractData(
                external_id=f"UNGM-{notice_id}",
                title=title[:500],
                description=None,
                entity=agency,
                amount=None,  # UNGM generalmente no muestra montos en listado
                currency="USD",
                country="multilateral",
                source=self.portal_name,
                url=url,
                publication_date=datetime.now(),
                deadline=deadline,
                raw_data={"notice_id": notice_id},
            )

        except Exception as e:
            logger.debug(f"Error parsing UNGM notice: {e}")
            return None

    def _fetch_notice_detail(self, notice_id: str, keywords: Optional[List[str]] = None) -> Optional[ContractData]:
        """
        Obtiene detalles de un notice específico.
        """
        try:
            import requests
            from bs4 import BeautifulSoup

            url = f"{self.BASE_URL}/Public/Notice/{notice_id}"

            response = requests.get(url, headers=self._get_headers(), timeout=20)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, "lxml")

            # Extraer título
            title_elem = soup.select_one("h1, .notice-title, .title")
            title = title_elem.get_text(strip=True) if title_elem else ""

            if not title:
                return None

            # Filtrar por keywords
            if keywords:
                text_lower = title.lower()
                desc_elem = soup.select_one(".description, .notice-description")
                if desc_elem:
                    text_lower += " " + desc_elem.get_text(strip=True).lower()

                if not any(kw.lower() in text_lower for kw in keywords):
                    return None

            # Descripción
            desc_elem = soup.select_one(".description, .notice-description, .content")
            description = desc_elem.get_text(strip=True)[:2000] if desc_elem else None

            # Agencia
            agency_elem = soup.select_one(".agency, .organization, .un-agency")
            agency = agency_elem.get_text(strip=True) if agency_elem else "Naciones Unidas"

            # Deadline
            deadline = None
            deadline_elem = soup.select_one(".deadline, .closing-date")
            if deadline_elem:
                deadline = self._parse_ungm_date(deadline_elem.get_text(strip=True))

            return ContractData(
                external_id=f"UNGM-{notice_id}",
                title=title[:500],
                description=description,
                entity=agency,
                amount=None,
                currency="USD",
                country="multilateral",
                source=self.portal_name,
                url=url,
                publication_date=datetime.now(),
                deadline=deadline,
                raw_data={"notice_id": notice_id, "url": url},
            )

        except Exception as e:
            logger.debug(f"Error fetching UNGM detail {notice_id}: {e}")
            return None

    def _parse_ungm_date(self, date_str: str) -> Optional[datetime]:
        """Parsea fechas de UNGM en varios formatos."""
        if not date_str:
            return None

        # Limpiar string
        date_str = date_str.strip()

        formats = [
            "%d-%b-%Y",  # 15-Jan-2024
            "%d %b %Y",  # 15 Jan 2024
            "%Y-%m-%d",  # 2024-01-15
            "%d/%m/%Y",  # 15/01/2024
            "%m/%d/%Y",  # 01/15/2024
            "%B %d, %Y",  # January 15, 2024
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None
