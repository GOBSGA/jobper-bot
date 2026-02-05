"""
Scraper para portal de proveedores de EPM
Obtiene oportunidades de contratación de Empresas Públicas de Medellín
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from scrapers.base import ContractData
from scrapers.private.base_private import PrivatePortalScraper

logger = logging.getLogger(__name__)


class EPMScraper(PrivatePortalScraper):
    """
    Scraper para oportunidades de EPM (Empresas Públicas de Medellín).

    EPM es una de las empresas de servicios públicos más grandes de Colombia.
    Opera en energía, agua, gas y telecomunicaciones.

    URL: https://www.epm.com.co/proveedores
    """

    portal_name = "EPM"
    portal_country = "colombia"
    source_type = "private"
    requires_authentication = False

    # URLs del portal
    BASE_URL = "https://www.epm.com.co"
    PROVIDERS_URL = "https://www.epm.com.co/site/proveedores-y-contratistas"

    def __init__(self):
        super().__init__(api_url=self.BASE_URL)

    def _fetch_contracts_impl(
        self,
        keywords: Optional[List[str]] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        days_back: int = 30
    ) -> List[ContractData]:
        """
        Obtiene oportunidades de contratación de EPM.

        EPM publica sus procesos de contratación en su portal de proveedores.
        """
        contracts = []

        try:
            import requests
            from bs4 import BeautifulSoup

            headers = self._get_headers()
            headers["Accept"] = "text/html,application/xhtml+xml"

            # URLs a intentar
            urls_to_try = [
                "https://www.epm.com.co/site/proveedores-y-contratistas/oportunidades",
                "https://www.epm.com.co/site/proveedores-y-contratistas/contratacion",
                self.PROVIDERS_URL,
                "https://www.epm.com.co/site/proveedores-y-contratistas",
            ]

            soup = None
            for url in urls_to_try:
                try:
                    response = requests.get(url, headers=headers, timeout=30)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "lxml")
                        # Verificar que tiene contenido relevante
                        if soup.select(".proceso, .oportunidad, .contratacion, article"):
                            break
                except Exception:
                    continue

            if not soup:
                logger.warning(f"{self.portal_name}: No se pudo acceder al portal")
                return contracts

            # Buscar elementos de procesos/oportunidades
            opportunity_elements = (
                soup.select(".proceso-contratacion, .oportunidad-item") or
                soup.select("article.contratacion") or
                soup.select(".listado-procesos .item") or
                soup.select(".card-proceso, .card-oportunidad") or
                soup.select('a[href*="proceso"], a[href*="contratacion"]')
            )

            for element in opportunity_elements[:30]:
                try:
                    contract = self._parse_opportunity_element(element, keywords)
                    if contract:
                        if min_amount and contract.amount and contract.amount < min_amount:
                            continue
                        if max_amount and contract.amount and contract.amount > max_amount:
                            continue
                        contracts.append(contract)
                except Exception as e:
                    logger.debug(f"Error parsing EPM element: {e}")
                    continue

            # Fallback si no encontramos elementos estructurados
            if not contracts:
                contracts = self._fallback_extraction(soup, keywords)

            logger.info(f"{self.portal_name}: {len(contracts)} oportunidades encontradas")

        except Exception as e:
            logger.error(f"{self.portal_name}: Error fetching: {e}")

        return contracts

    def _parse_opportunity_element(
        self,
        element,
        keywords: Optional[List[str]] = None
    ) -> Optional[ContractData]:
        """Parsea un elemento HTML de oportunidad de EPM."""
        try:
            # Obtener título
            title_elem = element.select_one("h2, h3, h4, .titulo, .title, a")
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

            # URL
            link = element.select_one("a") or (element if element.name == "a" else None)
            url = self.PROVIDERS_URL

            if link:
                href = link.get("href", "")
                if href:
                    if href.startswith("/"):
                        url = f"{self.BASE_URL}{href}"
                    elif href.startswith("http"):
                        url = href

            # ID único
            external_id = f"EPM-{hash(title) % 1000000}"

            # Descripción
            desc_elem = element.select_one(".descripcion, .resumen, p")
            description = desc_elem.get_text(strip=True) if desc_elem else None

            # Número de proceso (si está disponible)
            num_elem = element.select_one(".numero-proceso, .codigo")
            if num_elem:
                num_proceso = num_elem.get_text(strip=True)
                external_id = f"EPM-{num_proceso}"

            # Fecha límite
            deadline = None
            deadline_elem = element.select_one(".fecha-cierre, .vencimiento, .deadline")
            if deadline_elem:
                deadline = self._parse_date(deadline_elem.get_text(strip=True))

            # Monto (si está disponible)
            amount = None
            amount_elem = element.select_one(".valor, .monto, .presupuesto")
            if amount_elem:
                amount = self._parse_amount(amount_elem.get_text(strip=True))

            return ContractData(
                external_id=external_id,
                title=title[:500],
                description=description[:1000] if description else None,
                entity="Empresas Públicas de Medellín (EPM)",
                amount=amount,
                currency="COP",
                country="colombia",
                source=self.portal_name,
                url=url,
                publication_date=datetime.now(),
                deadline=deadline,
                raw_data={"source": "web_scrape"}
            )

        except Exception as e:
            logger.debug(f"Error parsing EPM opportunity: {e}")
            return None

    def _fallback_extraction(
        self,
        soup,
        keywords: Optional[List[str]] = None
    ) -> List[ContractData]:
        """Extracción de fallback buscando links de contratación."""
        contracts = []

        contract_keywords = [
            "contratacion", "licitacion", "invitacion", "concurso",
            "proceso", "proveedor", "suministro"
        ]

        all_links = soup.select("a[href]")

        for link in all_links[:50]:
            href = link.get("href", "").lower()
            text = link.get_text(strip=True)

            is_contract_link = any(kw in href or kw in text.lower() for kw in contract_keywords)

            if not is_contract_link or len(text) < 15:
                continue

            if keywords and not any(kw.lower() in text.lower() for kw in keywords):
                continue

            url = link.get("href")
            if url.startswith("/"):
                url = f"{self.BASE_URL}{url}"

            contract = ContractData(
                external_id=f"EPM-LINK-{hash(text) % 100000}",
                title=text[:500],
                description=None,
                entity="Empresas Públicas de Medellín (EPM)",
                amount=None,
                currency="COP",
                country="colombia",
                source=self.portal_name,
                url=url,
                publication_date=datetime.now(),
                deadline=None,
                raw_data={"source": "fallback_extraction"}
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
            "%d %b %Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parsea montos de texto a float."""
        if not amount_str:
            return None

        try:
            # Limpiar string
            cleaned = amount_str.replace("$", "").replace("COP", "")
            cleaned = cleaned.replace(".", "").replace(",", ".")
            cleaned = "".join(c for c in cleaned if c.isdigit() or c == ".")

            if cleaned:
                return float(cleaned)
        except ValueError:
            pass

        return None
