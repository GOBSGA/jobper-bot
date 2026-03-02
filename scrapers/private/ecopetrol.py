"""
Scraper para portal de proveedores de Ecopetrol
Obtiene oportunidades de contratación de la petrolera colombiana
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from scrapers.base import ContractData
from scrapers.private.base_private import PrivatePortalScraper

logger = logging.getLogger(__name__)


class EcopetrolScraper(PrivatePortalScraper):
    """
    Scraper para oportunidades de Ecopetrol.

    Ecopetrol es la empresa petrolera más grande de Colombia.
    Publica oportunidades de contratación en su portal de proveedores.

    URL: https://csp.ecopetrol.com.co
    """

    portal_name = "Ecopetrol"
    portal_country = "colombia"
    source_type = "private"
    requires_authentication = False

    # URLs del portal
    BASE_URL = "https://csp.ecopetrol.com.co"
    OPPORTUNITIES_URL = "https://www.ecopetrol.com.co/wps/portal/Home/es/Proveedores"

    def __init__(self):
        super().__init__(api_url=self.BASE_URL)

    def _fetch_contracts_impl(
        self,
        keywords: Optional[List[str]] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        days_back: int = 30,
    ) -> List[ContractData]:
        """
        El portal CSP de Ecopetrol (csp.ecopetrol.com.co) requiere autenticación
        de proveedor registrado y renderiza contenido con JavaScript.
        BeautifulSoup no puede parsear el contenido dinámico.

        TODO: Implementar con API oficial de Ecopetrol cuando esté disponible,
        o con Playwright + credenciales de proveedor registrado.
        """
        logger.info(
            f"{self.portal_name}: Deshabilitado — el portal CSP requiere "
            "autenticación y JavaScript. Retornando vacío."
        )
        return []

        # --- CÓDIGO ORIGINAL (requiere JS + auth) ---
        contracts = []

        try:
            import requests
            from bs4 import BeautifulSoup

            # Obtener página de oportunidades
            headers = self._get_headers()
            headers["Accept"] = "text/html,application/xhtml+xml"

            # Intentar diferentes URLs del portal
            urls_to_try = [
                "https://www.ecopetrol.com.co/wps/portal/Home/es/Proveedores/Contratacion",
                "https://www.ecopetrol.com.co/wps/portal/Home/es/Proveedores",
                self.BASE_URL,
            ]

            soup = None
            for url in urls_to_try:
                try:
                    response = requests.get(url, headers=headers, timeout=30)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "lxml")
                        break
                except Exception:
                    continue

            if not soup:
                logger.warning(f"{self.portal_name}: No se pudo acceder al portal")
                return contracts

            # Buscar elementos de oportunidades/licitaciones
            # La estructura exacta depende del portal
            opportunity_elements = (
                soup.select(".oportunidad, .licitacion, .contratacion-item")
                or soup.select("article.opportunity")
                or soup.select(".listado-procesos li")
                or soup.select('a[href*="contratacion"], a[href*="licitacion"]')
            )

            for element in opportunity_elements[:30]:
                try:
                    contract = self._parse_opportunity_element(element, keywords)
                    if contract:
                        # Filtrar por monto si se especifica
                        if min_amount and contract.amount and contract.amount < min_amount:
                            continue
                        if max_amount and contract.amount and contract.amount > max_amount:
                            continue
                        contracts.append(contract)
                except Exception as e:
                    logger.debug(f"Error parsing Ecopetrol element: {e}")
                    continue

            # Si no encontramos nada estructurado, buscar links genéricos
            if not contracts:
                contracts = self._fallback_link_extraction(soup, keywords)

            logger.info(f"{self.portal_name}: {len(contracts)} oportunidades encontradas")

        except Exception as e:
            logger.error(f"{self.portal_name}: Error fetching: {e}")

        return contracts

    def _parse_opportunity_element(self, element, keywords: Optional[List[str]] = None) -> Optional[ContractData]:
        """Parsea un elemento HTML de oportunidad."""
        try:
            # Obtener título
            title_elem = element.select_one("h2, h3, h4, .title, a")
            if title_elem:
                title = title_elem.get_text(strip=True)
            elif element.name == "a":
                title = element.get_text(strip=True)
            else:
                return None

            if not title or len(title) < 10:
                return None

            # Filtrar por keywords
            if keywords:
                text_lower = title.lower()
                if not any(kw.lower() in text_lower for kw in keywords):
                    return None

            # Obtener URL
            link = element.select_one("a") or (element if element.name == "a" else None)
            url = None
            if link:
                href = link.get("href", "")
                if href:
                    if href.startswith("/"):
                        url = f"https://www.ecopetrol.com.co{href}"
                    elif href.startswith("http"):
                        url = href
                    else:
                        url = f"https://www.ecopetrol.com.co/{href}"

            # ID único basado en título
            external_id = f"ECO-{hash(title) % 1000000}"

            # Buscar descripción
            desc_elem = element.select_one(".descripcion, .description, p")
            description = desc_elem.get_text(strip=True) if desc_elem else None

            # Buscar fecha límite
            deadline = None
            deadline_elem = element.select_one(".fecha-cierre, .deadline, .fecha")
            if deadline_elem:
                deadline = self._parse_date(deadline_elem.get_text(strip=True))

            return ContractData(
                external_id=external_id,
                title=title[:500],
                description=description[:1000] if description else None,
                entity="Ecopetrol S.A.",
                amount=None,  # Usualmente no está en el listado
                currency="COP",
                country="colombia",
                source=self.portal_name,
                url=url or self.OPPORTUNITIES_URL,
                publication_date=datetime.now(),
                deadline=deadline,
                raw_data={"source": "web_scrape"},
            )

        except Exception as e:
            logger.debug(f"Error parsing Ecopetrol opportunity: {e}")
            return None

    def _fallback_link_extraction(self, soup, keywords: Optional[List[str]] = None) -> List[ContractData]:
        """Extrae links relacionados con contratación como fallback."""
        contracts = []

        # Buscar links que contengan palabras clave de contratación
        contract_keywords = ["contratacion", "licitacion", "invitacion", "concurso", "proceso"]

        all_links = soup.select("a[href]")

        for link in all_links[:50]:
            href = link.get("href", "").lower()
            text = link.get_text(strip=True)

            # Verificar si es un link de contratación
            is_contract_link = any(kw in href or kw in text.lower() for kw in contract_keywords)

            if not is_contract_link or len(text) < 15:
                continue

            # Filtrar por keywords del usuario
            if keywords and not any(kw.lower() in text.lower() for kw in keywords):
                continue

            url = link.get("href")
            if url.startswith("/"):
                url = f"https://www.ecopetrol.com.co{url}"

            contract = ContractData(
                external_id=f"ECO-LINK-{hash(text) % 100000}",
                title=text[:500],
                description=None,
                entity="Ecopetrol S.A.",
                amount=None,
                currency="COP",
                country="colombia",
                source=self.portal_name,
                url=url,
                publication_date=datetime.now(),
                deadline=None,
                raw_data={"source": "fallback_extraction"},
            )
            contracts.append(contract)

        return contracts

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parsea fechas en varios formatos."""
        if not date_str:
            return None

        date_str = date_str.strip()

        formats = [
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d de %B de %Y",
            "%B %d, %Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None
