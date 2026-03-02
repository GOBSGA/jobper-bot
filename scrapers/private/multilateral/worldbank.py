"""
Scraper para el Banco Mundial (World Bank)
Obtiene proyectos activos del Banco Mundial con presencia en Colombia/LAC.

API: https://search.worldbank.org/api/v2/projects
Docs: https://data.worldbank.org/products/api
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from scrapers.base import ContractData
from scrapers.private.base_private import PrivatePortalScraper

logger = logging.getLogger(__name__)


class WorldBankScraper(PrivatePortalScraper):
    """
    Scraper para proyectos/oportunidades del Banco Mundial.

    Usa la API pública de proyectos del Banco Mundial, filtrando por Colombia
    y países de América Latina. Los proyectos incluyen oportunidades de
    procurement asociadas.

    API: search.worldbank.org/api/v2/projects
    """

    portal_name = "Banco Mundial"
    portal_country = "multilateral"
    source_type = "multilateral"
    requires_authentication = False

    # API endpoint — versión confirmada como funcional
    API_URL = "https://search.worldbank.org/api/v2/projects"

    # Países LAC más relevantes para usuarios colombianos
    LAC_COUNTRIES = ["CO", "PE", "EC", "MX", "BR", "AR", "CL", "PA", "VE"]

    def __init__(self):
        super().__init__(api_url=self.API_URL)

    def _fetch_contracts_impl(
        self,
        keywords: Optional[List[str]] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        days_back: int = 30,
    ) -> List[ContractData]:
        """Obtiene proyectos activos del Banco Mundial en Colombia/LAC."""
        contracts = []

        # Intentar primero Colombia, luego LAC amplio
        country_filters = ["CO", None]  # None = sin filtro de país

        for country_code in country_filters:
            batch = self._fetch_for_country(country_code, keywords, days_back)
            contracts.extend(batch)
            if len(contracts) >= 20:
                break

        # Filtrar por monto si se especifica
        if min_amount or max_amount:
            contracts = [
                c for c in contracts
                if not c.amount or (
                    (not min_amount or c.amount >= min_amount) and
                    (not max_amount or c.amount <= max_amount)
                )
            ]

        logger.info(f"{self.portal_name}: {len(contracts)} proyectos encontrados")
        return contracts

    def _fetch_for_country(
        self,
        country_code: Optional[str],
        keywords: Optional[List[str]],
        days_back: int,
    ) -> List[ContractData]:
        """Fetch proyectos para un país específico (o global si country_code=None)."""
        params = {
            "format": "json",
            "rows": 50,
            "status_exact": "Active",
            "fl": "id,project_name,countryname,totalamt,boardapprovaldate,closingdate,project_abstract,lendprojecttype",
        }

        if country_code:
            params["countrycode_exact"] = country_code

        if keywords:
            params["qterm"] = " ".join(keywords[:3])

        try:
            response = self._make_request(self.API_URL, params=params)
            if not response:
                return []

            projects = response.get("projects", {})
            if isinstance(projects, dict):
                projects = list(projects.values())
            elif not isinstance(projects, list):
                return []

            contracts = []
            for proj in projects:
                if not isinstance(proj, dict):
                    continue
                try:
                    contract = self._normalize_project(proj)
                    if contract:
                        contracts.append(contract)
                except Exception as e:
                    logger.debug(f"Error normalizando proyecto WB: {e}")

            return contracts

        except Exception as e:
            logger.error(f"{self.portal_name}: Error fetching country={country_code}: {e}")
            return []

    def _normalize_project(self, proj: dict) -> Optional[ContractData]:
        """Normaliza un proyecto del Banco Mundial al formato estándar."""
        try:
            project_id = proj.get("id", "")
            if not project_id:
                return None

            title = proj.get("project_name", "").strip()
            if not title:
                return None

            # Monto total
            amount = None
            raw_amount = proj.get("totalamt")
            if raw_amount:
                try:
                    amount = float(str(raw_amount).replace(",", ""))
                    if amount <= 0:
                        amount = None
                except (ValueError, TypeError):
                    pass

            # Fechas
            pub_date = self._parse_date(proj.get("boardapprovaldate"))
            deadline = self._parse_date(proj.get("closingdate"))

            # Descripción
            description = proj.get("project_abstract", "")
            if isinstance(description, dict):
                description = description.get("cdata", "") or str(description)

            # País
            country_name = proj.get("countryname", "")
            if isinstance(country_name, dict):
                country_name = str(country_name)

            entity = f"Banco Mundial — {country_name}" if country_name else "Banco Mundial"

            url = f"https://projects.worldbank.org/en/projects-operations/project-detail/{project_id}"

            return ContractData(
                external_id=f"WB-{project_id}",
                title=title[:500],
                description=str(description)[:2000] if description else None,
                entity=entity,
                amount=amount,
                currency="USD",
                country="multilateral",
                source=self.portal_name,
                source_type=self.source_type,
                url=url,
                publication_date=pub_date or datetime.now(timezone.utc),
                deadline=deadline,
                raw_data={"project_id": project_id, "country": country_name},
            )

        except Exception as e:
            logger.debug(f"Error normalizando proyecto WB: {e}")
            return None

    def _parse_date(self, date_str) -> Optional[datetime]:
        """Parsea fechas del Banco Mundial."""
        if not date_str:
            return None

        # Puede venir como dict con cdata
        if isinstance(date_str, dict):
            date_str = date_str.get("cdata", "") or str(date_str)

        date_str = str(date_str).strip()[:19]

        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%d-%b-%Y",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        return None
