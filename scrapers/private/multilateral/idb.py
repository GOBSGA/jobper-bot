"""
Scraper para el Banco Interamericano de Desarrollo (BID/IDB)
Obtiene proyectos activos del BID en Colombia y América Latina.

API: https://api.iadb.org/api/v1/ (IADB Open Data)
Portal: https://www.iadb.org/en/projects
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from scrapers.base import ContractData
from scrapers.private.base_private import PrivatePortalScraper

logger = logging.getLogger(__name__)


class IDBScraper(PrivatePortalScraper):
    """
    Scraper para proyectos del Banco Interamericano de Desarrollo (BID).

    Usa la API pública de proyectos del IADB, que incluye información de
    procurement y licitaciones asociadas a proyectos en Colombia y LAC.

    API primaria: IADB.org project search JSON
    Fallback: World Bank-style search API
    """

    portal_name = "BID (IDB)"
    portal_country = "multilateral"
    source_type = "multilateral"
    requires_authentication = False

    # API de proyectos del IADB
    PROJECTS_API = "https://www.iadb.org/en/projects/search.json"
    # Datos abiertos IADB (CKAN)
    DATA_API = "https://data.iadb.org/api/action/datastore_search"

    def __init__(self):
        super().__init__(api_url=self.PROJECTS_API)

    def _fetch_contracts_impl(
        self,
        keywords: Optional[List[str]] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        days_back: int = 30,
    ) -> List[ContractData]:
        """Obtiene proyectos activos del BID en Colombia/LAC."""
        contracts = []

        # Estrategia 1: API de proyectos IADB
        try:
            contracts = self._fetch_from_projects_api(keywords, days_back)
        except Exception as e:
            logger.warning(f"{self.portal_name}: Projects API falló: {e}")

        # Estrategia 2: API de datos abiertos IADB
        if not contracts:
            try:
                contracts = self._fetch_from_data_api(keywords)
            except Exception as e:
                logger.warning(f"{self.portal_name}: Data API falló: {e}")

        # Filtrar por monto
        if (min_amount or max_amount) and contracts:
            contracts = [
                c for c in contracts
                if not c.amount or (
                    (not min_amount or c.amount >= min_amount) and
                    (not max_amount or c.amount <= max_amount)
                )
            ]

        logger.info(f"{self.portal_name}: {len(contracts)} proyectos encontrados")
        return contracts

    def _fetch_from_projects_api(
        self,
        keywords: Optional[List[str]] = None,
        days_back: int = 30,
    ) -> List[ContractData]:
        """Usa la API de búsqueda de proyectos de IADB.org."""
        import requests

        params = {
            "country": "CO",  # Colombia primero
            "status": "active",
            "page": 1,
            "per_page": 50,
        }

        if keywords:
            params["q"] = " ".join(keywords[:3])

        headers = {
            "User-Agent": "Jobper-Bot/3.0 (Contract Monitor)",
            "Accept": "application/json",
            "Accept-Language": "es-CO,es;q=0.9",
        }

        response = requests.get(
            self.PROJECTS_API,
            params=params,
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("results", data.get("projects", data.get("data", [])))

        contracts = []
        for item in items:
            if not isinstance(item, dict):
                continue
            contract = self._normalize_project(item)
            if contract:
                contracts.append(contract)

        return contracts

    def _fetch_from_data_api(self, keywords: Optional[List[str]] = None) -> List[ContractData]:
        """
        Usa la API de datos abiertos del IADB (CKAN-based).
        Intenta obtener datos de procurement públicos.
        """
        import requests

        # Intentar recurso de procurement del IADB data portal
        # Resource IDs conocidos del portal IADB
        resource_attempts = [
            # Procurement notices
            {"resource_id": "procurement", "filters": {"country": "CO"}},
        ]

        headers = {
            "User-Agent": "Jobper-Bot/3.0",
            "Accept": "application/json",
        }

        for attempt in resource_attempts:
            try:
                params = {
                    "resource_id": attempt["resource_id"],
                    "limit": 50,
                }
                if keywords:
                    params["q"] = " ".join(keywords[:3])

                response = requests.get(
                    self.DATA_API,
                    params=params,
                    headers=headers,
                    timeout=15,
                )
                if response.status_code != 200:
                    continue

                data = response.json()
                if not data.get("success"):
                    continue

                records = data.get("result", {}).get("records", [])
                contracts = []
                for rec in records:
                    contract = self._normalize_record(rec)
                    if contract:
                        contracts.append(contract)

                if contracts:
                    return contracts

            except Exception as e:
                logger.debug(f"IDB data API attempt failed: {e}")
                continue

        return []

    def _normalize_project(self, raw: dict) -> Optional[ContractData]:
        """Normaliza un proyecto del BID al formato estándar."""
        try:
            project_id = (
                raw.get("id") or raw.get("project_number") or
                raw.get("project_id") or raw.get("idb_id")
            )
            if not project_id:
                return None

            title = (
                raw.get("title") or raw.get("project_name") or
                raw.get("name") or ""
            ).strip()
            if not title:
                return None

            # Monto
            amount = None
            for field in ["amount", "total_cost", "loan_amount", "totalamt", "value"]:
                val = raw.get(field)
                if val:
                    try:
                        amount = float(str(val).replace(",", "").replace("$", ""))
                        if amount > 0:
                            break
                        amount = None
                    except (ValueError, TypeError):
                        continue

            # Fechas
            pub_date = self._parse_date(
                raw.get("approval_date") or raw.get("boardapprovaldate") or
                raw.get("publication_date") or raw.get("date")
            )
            deadline = self._parse_date(
                raw.get("closing_date") or raw.get("closingdate") or
                raw.get("deadline") or raw.get("expiry_date")
            )

            # URL
            url = raw.get("url") or raw.get("link")
            if not url:
                url = f"https://www.iadb.org/en/projects/{project_id}"

            # País/Entidad
            country_name = raw.get("country") or raw.get("countryname") or "LAC"
            entity = f"BID — {country_name}" if country_name != "LAC" else "Banco Interamericano de Desarrollo"

            return ContractData(
                external_id=f"IDB-{project_id}",
                title=title[:500],
                description=(raw.get("description") or raw.get("abstract") or "")[:2000] or None,
                entity=entity,
                amount=amount,
                currency="USD",
                country="multilateral",
                source=self.portal_name,
                source_type=self.source_type,
                url=url,
                publication_date=pub_date or datetime.now(timezone.utc),
                deadline=deadline,
                raw_data={"project_id": str(project_id)},
            )

        except Exception as e:
            logger.debug(f"Error normalizando proyecto BID: {e}")
            return None

    def _normalize_record(self, raw: dict) -> Optional[ContractData]:
        """Normaliza un registro del portal de datos abiertos IADB."""
        try:
            rec_id = raw.get("id") or raw.get("_id") or raw.get("notice_id")
            if not rec_id:
                return None

            title = raw.get("title") or raw.get("description", "")[:200]
            if not title:
                return None

            return ContractData(
                external_id=f"IDB-DATA-{rec_id}",
                title=str(title)[:500],
                description=raw.get("description"),
                entity=raw.get("entity") or "BID (IDB)",
                amount=None,
                currency="USD",
                country="multilateral",
                source=self.portal_name,
                source_type=self.source_type,
                url=raw.get("url") or "https://www.iadb.org/en/projects",
                publication_date=datetime.now(timezone.utc),
                deadline=None,
                raw_data=raw,
            )
        except Exception as e:
            logger.debug(f"Error normalizando record BID: {e}")
            return None

    def _parse_date(self, date_str) -> Optional[datetime]:
        """Parsea fechas del BID."""
        if not date_str:
            return None

        date_str = str(date_str).strip()[:19]

        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d-%b-%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        return None
