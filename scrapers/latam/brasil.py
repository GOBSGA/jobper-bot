"""
Scrapers para Brasil - ComprasNet (Gobierno) y Petrobras (Empresa Pública)
Brasil es el mercado de contratación pública más grande de LATAM (~$200B USD/año)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from scrapers.base import BaseScraper, ContractData

logger = logging.getLogger(__name__)

# ComprasNet - Portal de Compras del Gobierno Federal de Brasil
COMPRASNET_API_URL = "https://compras.dados.gov.br/licitacoes/v1/licitacoes.json"

# Petrobras - Portal de Compras
PETROBRAS_BASE_URL = "https://canaldesuprimento.petrobras.com.br"


class ComprasNetScraper(BaseScraper):
    """
    Scraper para ComprasNet - Portal de Compras del Gobierno Federal de Brasil.

    ComprasNet es el sistema de compras electrónicas del gobierno brasileño.
    Incluye todas las licitaciones del gobierno federal.

    API: https://compras.dados.gov.br/
    """

    def __init__(self):
        super().__init__(COMPRASNET_API_URL)

    def fetch_contracts(
        self, keywords: List[str] = None, min_amount: float = None, max_amount: float = None, days_back: int = 7
    ) -> List[ContractData]:
        """
        Obtiene licitaciones de ComprasNet (Brasil).

        Args:
            keywords: Palabras clave para filtrar
            min_amount: Monto mínimo en BRL (reales)
            max_amount: Monto máximo en BRL
            days_back: Días hacia atrás para buscar

        Returns:
            Lista de ContractData normalizados
        """
        params = self._build_query(keywords, min_amount, max_amount, days_back)

        logger.info("🇧🇷 Consultando ComprasNet Brasil...")
        logger.debug(f"Query params: {params}")

        data = self._safe_request(self.api_url, params)

        if not data:
            logger.warning("No se obtuvieron datos de ComprasNet Brasil")
            return []

        # ComprasNet devuelve {"_embedded": {"licitacoes": [...]}}
        results = []
        if isinstance(data, dict):
            embedded = data.get("_embedded", {})
            results = embedded.get("licitacoes", [])
        elif isinstance(data, list):
            results = data

        contracts = []
        for raw in results:
            try:
                contract = self._normalize_contract(raw)
                if contract:
                    # Filtrar por monto
                    if min_amount and contract.amount and contract.amount < min_amount:
                        continue
                    if max_amount and contract.amount and contract.amount > max_amount:
                        continue
                    contracts.append(contract)
            except Exception as e:
                logger.error(f"Error normalizando contrato Brasil: {e}")
                continue

        logger.info(f"✅ ComprasNet Brasil: {len(contracts)} licitações obtidas")
        return contracts

    def _build_query(
        self, keywords: List[str] = None, min_amount: float = None, max_amount: float = None, days_back: int = 7
    ) -> dict:
        """Construye los parámetros de consulta para ComprasNet."""

        date_limit = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        params = {
            "data_publicacao_min": date_limit,
            "situacao": "aberta",  # Solo licitaciones abiertas
            "offset": 0,
            "limit": 200,
        }

        # Filtro de keywords (buscar en objeto)
        if keywords:
            params["objeto"] = keywords[0] if keywords else ""

        return params

    def _normalize_contract(self, raw: dict) -> Optional[ContractData]:
        """Normaliza una licitación de ComprasNet al formato estándar."""

        # ID único
        external_id = raw.get("identificador") or raw.get("numero_licitacao", "")
        if not external_id:
            return None

        # Parsear fechas
        pub_date = self._parse_date(raw.get("data_publicacao") or raw.get("data_abertura_proposta"))
        deadline = self._parse_date(raw.get("data_entrega_proposta") or raw.get("data_encerramento"))

        # Parsear monto
        amount = None
        for field in ["valor_estimado", "valor_licitacao", "valor_total"]:
            if raw.get(field):
                try:
                    amount = float(raw[field])
                    if amount > 0:
                        break
                except (ValueError, TypeError):
                    continue

        # Construir URL
        url = self._build_url(raw)

        return ContractData(
            external_id=str(external_id),
            title=raw.get("objeto", "Sem título")[:500],
            description=raw.get("objeto", ""),
            entity=raw.get("orgao") or raw.get("nome_uasg", "Governo Federal do Brasil"),
            amount=amount,
            currency="BRL",
            country="brasil",
            source="ComprasNet",
            url=url,
            publication_date=pub_date,
            deadline=deadline,
            raw_data=raw,
        )

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parsea fechas de ComprasNet."""
        if not date_str:
            return None

        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(date_str)[:26], fmt)
            except ValueError:
                continue

        return None

    def _build_url(self, raw: dict) -> str:
        """Construye la URL de la licitación en ComprasNet."""
        identificador = raw.get("identificador", "")
        if identificador:
            return f"https://www.gov.br/compras/pt-br/acesso-a-informacao/consulta-detalhada/{identificador}"

        uasg = raw.get("uasg", "")
        numero = raw.get("numero_licitacao", "")
        if uasg and numero:
            return f"https://comprasnet.gov.br/acesso.asp?url=/Livre/Pregao/{uasg}/{numero}"

        return "https://www.gov.br/compras/pt-br"


class PetrobrasScraper(BaseScraper):
    """
    Scraper para portal de proveedores de Petrobras.

    Petrobras es la empresa más grande de Brasil y una de las mayores
    petroleras del mundo. Compra ~$80B USD/año en bienes y servicios.

    URL: https://canaldesuprimento.petrobras.com.br
    """

    portal_name = "Petrobras"
    portal_country = "brasil"
    source_type = "state_enterprise"

    def __init__(self):
        super().__init__(PETROBRAS_BASE_URL)

    def fetch_contracts(
        self, keywords: List[str] = None, min_amount: float = None, max_amount: float = None, days_back: int = 30
    ) -> List[ContractData]:
        """
        Obtiene oportunidades de Petrobras.

        Petrobras publica oportunidades en su Canal de Suprimento.
        """
        contracts = []

        try:
            import requests
            from bs4 import BeautifulSoup

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            }

            # URLs del portal de proveedores
            urls_to_try = [
                "https://canaldesuprimento.petrobras.com.br/oportunidades",
                "https://transparencia.petrobras.com.br/licitacoes-e-contratos",
                "https://petrobras.com.br/fornecedores",
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
                logger.warning("Petrobras: No se pudo acceder al portal")
                return contracts

            # Buscar elementos de oportunidades
            opportunity_elements = (
                soup.select(".oportunidade, .licitacao, .contrato-item")
                or soup.select("article.opportunity")
                or soup.select(".card-processo")
                or soup.select('a[href*="licitacao"], a[href*="oportunidade"]')
            )

            for element in opportunity_elements[:30]:
                try:
                    contract = self._parse_opportunity(element, keywords)
                    if contract:
                        if min_amount and contract.amount and contract.amount < min_amount:
                            continue
                        if max_amount and contract.amount and contract.amount > max_amount:
                            continue
                        contracts.append(contract)
                except Exception as e:
                    logger.debug(f"Error parsing Petrobras element: {e}")
                    continue

            # Fallback: buscar links de contratación
            if not contracts:
                contracts = self._fallback_extraction(soup, keywords)

            logger.info(f"✅ Petrobras: {len(contracts)} oportunidades encontradas")

        except Exception as e:
            logger.error(f"Petrobras: Error fetching: {e}")

        return contracts

    def _parse_opportunity(self, element, keywords: Optional[List[str]] = None) -> Optional[ContractData]:
        """Parsea un elemento HTML de oportunidad de Petrobras."""
        try:
            # Obtener título
            title_elem = element.select_one("h2, h3, h4, .titulo, a")
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
            url = PETROBRAS_BASE_URL

            if link:
                href = link.get("href", "")
                if href:
                    if href.startswith("/"):
                        url = f"{PETROBRAS_BASE_URL}{href}"
                    elif href.startswith("http"):
                        url = href

            external_id = f"PETRO-{hash(title) % 1000000}"

            return ContractData(
                external_id=external_id,
                title=title[:500],
                description=None,
                entity="Petrobras S.A.",
                amount=None,
                currency="BRL",
                country="brasil",
                source="Petrobras",
                url=url,
                publication_date=datetime.now(),
                deadline=None,
                raw_data={"source": "web_scrape"},
            )

        except Exception as e:
            logger.debug(f"Error parsing Petrobras opportunity: {e}")
            return None

    def _fallback_extraction(self, soup, keywords: Optional[List[str]] = None) -> List[ContractData]:
        """Extracción de fallback buscando links relevantes."""
        contracts = []

        contract_keywords = [
            "licitacao",
            "contratacao",
            "fornecedor",
            "suprimento",
            "oportunidade",
            "processo",
            "edital",
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
                url = f"{PETROBRAS_BASE_URL}{url}"

            contract = ContractData(
                external_id=f"PETRO-LINK-{hash(text) % 100000}",
                title=text[:500],
                description=None,
                entity="Petrobras S.A.",
                amount=None,
                currency="BRL",
                country="brasil",
                source="Petrobras",
                url=url,
                publication_date=datetime.now(),
                deadline=None,
                raw_data={"source": "fallback_extraction"},
            )
            contracts.append(contract)

        return contracts
