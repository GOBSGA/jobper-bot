"""
Scraper para el Banco Mundial (World Bank)
Obtiene oportunidades de procurement del Banco Mundial
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from scrapers.base import ContractData
from scrapers.private.base_private import PrivatePortalScraper

logger = logging.getLogger(__name__)


class WorldBankScraper(PrivatePortalScraper):
    """
    Scraper para oportunidades del Banco Mundial.

    El Banco Mundial publica procurement notices para proyectos
    de desarrollo en todo el mundo.

    API: World Bank Procurement API
    Docs: https://projects.worldbank.org/en/projects-operations/procurement
    """

    portal_name = "Banco Mundial"
    portal_country = "multilateral"
    source_type = "multilateral"
    requires_authentication = False

    # API endpoint - World Bank tiene API pública
    API_URL = "https://search.worldbank.org/api/v2/procnotices"

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
        Obtiene oportunidades de procurement del Banco Mundial.

        La API del Banco Mundial soporta búsqueda por texto y filtros.
        """
        contracts = []

        try:
            # Calcular fecha límite
            date_from = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

            # Parámetros de búsqueda
            params = {
                "format": "json",
                "rows": 100,
                "os": 0,  # offset
                "strdate": date_from,
                "status": "Active",
            }

            # Agregar búsqueda por texto si hay keywords
            if keywords:
                params["qterm"] = " OR ".join(keywords[:5])

            response = self._make_request("", params=params)

            if not response:
                logger.warning(f"{self.portal_name}: No response, trying alternative endpoint")
                return self._fetch_alternative(keywords, days_back)

            # La respuesta puede tener diferentes estructuras
            notices = response.get("procnotices", response.get("documents", []))
            if isinstance(notices, dict):
                notices = list(notices.values())

            for notice in notices:
                try:
                    contract = self._normalize_contract(notice)
                    if contract:
                        # Filtrar por monto
                        if min_amount and contract.amount and contract.amount < min_amount:
                            continue
                        if max_amount and contract.amount and contract.amount > max_amount:
                            continue

                        contracts.append(contract)
                except Exception as e:
                    logger.debug(f"Error normalizando contrato WB: {e}")
                    continue

            logger.info(f"{self.portal_name}: {len(contracts)} oportunidades encontradas")

        except Exception as e:
            logger.error(f"{self.portal_name}: Error fetching: {e}")
            return self._fetch_alternative(keywords, days_back)

        return contracts

    def _normalize_contract(self, raw: dict) -> Optional[ContractData]:
        """Normaliza un notice del Banco Mundial al formato estándar."""
        try:
            # IDs del Banco Mundial
            external_id = (
                raw.get("id") or
                raw.get("noticeNo") or
                raw.get("notice_id") or
                raw.get("project_id")
            )
            if not external_id:
                return None

            # Título
            title = (
                raw.get("title") or
                raw.get("notice_title") or
                raw.get("project_name") or
                ""
            )
            if not title:
                return None

            # Descripción
            description = raw.get("description") or raw.get("notice_text")

            # Entidad ejecutora
            entity = raw.get("borrower") or raw.get("agency") or "Banco Mundial"

            # Monto estimado
            amount = None
            for field in ["contractvalue", "estimated_amount", "amount", "value"]:
                if raw.get(field):
                    try:
                        val = str(raw[field]).replace(",", "").replace("$", "").strip()
                        amount = float(val)
                        break
                    except ValueError:
                        continue

            # Fechas
            pub_date = self._parse_date(
                raw.get("notice_posted_date") or
                raw.get("submission_date") or
                raw.get("created_date")
            )

            deadline = self._parse_date(
                raw.get("deadline_date") or
                raw.get("submission_deadline") or
                raw.get("closing_date")
            )

            # URL
            url = raw.get("url") or raw.get("notice_url")
            if not url and external_id:
                url = f"https://projects.worldbank.org/en/projects-operations/procurement-detail/{external_id}"

            # País del proyecto (si está disponible)
            country_name = raw.get("country") or raw.get("countryname") or "multilateral"

            return ContractData(
                external_id=f"WB-{external_id}",
                title=title[:500],
                description=description[:2000] if description else None,
                entity=entity,
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
            logger.debug(f"Error normalizando contrato WB: {e}")
            return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parsea fechas en varios formatos."""
        if not date_str:
            return None

        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d",
            "%d-%b-%Y",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(date_str)[:19], fmt)
            except ValueError:
                continue

        return None

    def _fetch_alternative(
        self,
        keywords: Optional[List[str]] = None,
        days_back: int = 30
    ) -> List[ContractData]:
        """
        Método alternativo usando la API de proyectos.
        """
        contracts = []

        try:
            # API alternativa de proyectos
            alt_url = "https://search.worldbank.org/api/v2/projects"

            params = {
                "format": "json",
                "rows": 50,
                "status_exact": "Active",
                "fl": "id,project_name,countryname,totalamt,boardapprovaldate,closingdate,project_abstract"
            }

            if keywords:
                params["qterm"] = " ".join(keywords[:3])

            response = self._make_request(alt_url, params=params)

            if not response:
                return contracts

            projects = response.get("projects", {})
            if isinstance(projects, dict):
                projects = list(projects.values())

            for proj in projects:
                try:
                    if isinstance(proj, dict):
                        contract = ContractData(
                            external_id=f"WB-PROJ-{proj.get('id', '')}",
                            title=proj.get("project_name", "")[:500],
                            description=proj.get("project_abstract"),
                            entity=f"Banco Mundial - {proj.get('countryname', '')}",
                            amount=float(proj.get("totalamt", 0)) if proj.get("totalamt") else None,
                            currency="USD",
                            country="multilateral",
                            source=self.portal_name,
                            url=f"https://projects.worldbank.org/en/projects-operations/project-detail/{proj.get('id', '')}",
                            publication_date=self._parse_date(proj.get("boardapprovaldate")),
                            deadline=self._parse_date(proj.get("closingdate")),
                            raw_data=proj
                        )
                        contracts.append(contract)
                except Exception as e:
                    logger.debug(f"Error en proyecto WB: {e}")
                    continue

            logger.info(f"{self.portal_name} (alt): {len(contracts)} proyectos")

        except Exception as e:
            logger.error(f"{self.portal_name} alternative error: {e}")

        return contracts
