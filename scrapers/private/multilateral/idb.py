"""
Scraper para el Banco Interamericano de Desarrollo (BID/IDB)
Obtiene oportunidades de procurement del BID
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from scrapers.base import ContractData
from scrapers.private.base_private import PrivatePortalScraper

logger = logging.getLogger(__name__)


class IDBScraper(PrivatePortalScraper):
    """
    Scraper para oportunidades del Banco Interamericano de Desarrollo.

    El BID publica oportunidades de procurement para proyectos de desarrollo
    en América Latina y el Caribe.

    Fuente: https://www.iadb.org/en/projects/procurement
    API: Procurement Notices API
    """

    portal_name = "BID (IDB)"
    portal_country = "multilateral"
    source_type = "multilateral"
    requires_authentication = False

    # API endpoint para procurement notices
    API_URL = "https://www.iadb.org/en/projects/search-json"

    def __init__(self):
        super().__init__(api_url=self.API_URL)

    def _fetch_contracts_impl(
        self,
        keywords: Optional[List[str]] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        days_back: int = 30
    ) -> List[ContractData]:
        """
        Obtiene oportunidades de procurement del BID.

        El BID tiene un sistema de búsqueda de proyectos que incluye
        información de procurement asociada.
        """
        contracts = []

        try:
            # Parámetros de búsqueda
            params = {
                "type": "procurement",
                "status": "active",
                "page": 1,
                "per_page": 100,
            }

            # Agregar keywords si existen
            if keywords:
                params["q"] = " ".join(keywords[:5])  # Máximo 5 keywords

            response = self._make_request("", params=params)

            if not response:
                logger.warning(f"{self.portal_name}: No response from API")
                return self._fetch_from_web_fallback(keywords, days_back)

            # Parsear resultados
            items = response.get("results", response.get("data", []))

            for item in items:
                try:
                    contract = self._normalize_contract(item)
                    if contract:
                        # Filtrar por monto si se especifica
                        if min_amount and contract.amount and contract.amount < min_amount:
                            continue
                        if max_amount and contract.amount and contract.amount > max_amount:
                            continue

                        contracts.append(contract)
                except Exception as e:
                    logger.debug(f"Error normalizando contrato BID: {e}")
                    continue

            logger.info(f"{self.portal_name}: {len(contracts)} oportunidades encontradas")

        except Exception as e:
            logger.error(f"{self.portal_name}: Error fetching: {e}")
            # Intentar fallback
            return self._fetch_from_web_fallback(keywords, days_back)

        return contracts

    def _normalize_contract(self, raw: dict) -> Optional[ContractData]:
        """Normaliza un contrato del BID al formato estándar."""
        try:
            # El BID puede tener diferentes estructuras de datos
            external_id = raw.get("id") or raw.get("project_number") or raw.get("notice_id")
            if not external_id:
                return None

            title = raw.get("title") or raw.get("project_name") or raw.get("description", "")[:200]
            if not title:
                return None

            # Parsear monto (puede venir en diferentes campos)
            amount = None
            for amount_field in ["amount", "contract_value", "estimated_value", "total_cost"]:
                if raw.get(amount_field):
                    try:
                        amount = float(str(raw[amount_field]).replace(",", "").replace("$", ""))
                        break
                    except ValueError:
                        continue

            # Parsear fecha de publicación
            pub_date = None
            for date_field in ["publication_date", "posted_date", "created_at", "date"]:
                if raw.get(date_field):
                    try:
                        pub_date = datetime.fromisoformat(raw[date_field].replace("Z", "+00:00"))
                        break
                    except (ValueError, AttributeError):
                        continue

            # Parsear deadline
            deadline = None
            for deadline_field in ["deadline", "closing_date", "submission_deadline", "due_date"]:
                if raw.get(deadline_field):
                    try:
                        deadline = datetime.fromisoformat(raw[deadline_field].replace("Z", "+00:00"))
                        break
                    except (ValueError, AttributeError):
                        continue

            # URL del proyecto
            url = raw.get("url") or raw.get("link")
            if not url and external_id:
                url = f"https://www.iadb.org/en/projects/{external_id}"

            return ContractData(
                external_id=f"IDB-{external_id}",
                title=title,
                description=raw.get("description") or raw.get("summary"),
                entity="Banco Interamericano de Desarrollo (BID)",
                amount=amount,
                currency="USD",
                country="multilateral",
                source=self.portal_name,
                url=url,
                publication_date=pub_date,
                deadline=deadline,
                raw_data=raw
            )

        except Exception as e:
            logger.debug(f"Error normalizando contrato BID: {e}")
            return None

    def _fetch_from_web_fallback(
        self,
        keywords: Optional[List[str]] = None,
        days_back: int = 30
    ) -> List[ContractData]:
        """
        Fallback: scrapea la página web si el API no funciona.

        Nota: Este es un método de respaldo y puede ser menos confiable.
        """
        contracts = []

        try:
            import requests
            from bs4 import BeautifulSoup

            url = "https://www.iadb.org/en/projects/procurement-notices"

            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # Buscar items de procurement (estructura puede variar)
            items = soup.select(".procurement-item, .notice-item, .project-card")

            for item in items[:50]:  # Limitar a 50
                try:
                    title_elem = item.select_one("h3, h4, .title, a")
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    link = title_elem.get("href", "")

                    if not link.startswith("http"):
                        link = f"https://www.iadb.org{link}"

                    # Filtrar por keywords si existen
                    if keywords:
                        text_lower = title.lower()
                        if not any(kw.lower() in text_lower for kw in keywords):
                            continue

                    contract = ContractData(
                        external_id=f"IDB-WEB-{hash(title) % 100000}",
                        title=title,
                        description=None,
                        entity="Banco Interamericano de Desarrollo (BID)",
                        amount=None,
                        currency="USD",
                        country="multilateral",
                        source=self.portal_name,
                        url=link,
                        publication_date=datetime.now(),
                        deadline=None,
                        raw_data={"source": "web_scrape"}
                    )
                    contracts.append(contract)

                except Exception as e:
                    logger.debug(f"Error parseando item web BID: {e}")
                    continue

            logger.info(f"{self.portal_name} (web fallback): {len(contracts)} items")

        except Exception as e:
            logger.error(f"{self.portal_name} web fallback error: {e}")

        return contracts
