"""
Scraper para SECOP I & II - Sistema de Contratación Pública de Colombia
API: Datos Abiertos Colombia (Socrata)
Soporta paginación para obtener TODOS los contratos disponibles.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from scrapers.base import BaseScraper, ContractData
from config import Config

logger = logging.getLogger(__name__)

# Multiple SECOP datasets on datos.gov.co
SECOP_DATASETS = {
    "procesos": {
        "url": "https://www.datos.gov.co/resource/p6dx-8zbt.json",
        "source": "SECOP II",
        "title_field": "nombre_del_procedimiento",
        "description_field": "descripci_n_del_procedimiento",
        "entity_field": "entidad",
        "date_field": "fecha_de_publicacion_del",
        "deadline_field": "fecha_de_cierre",
        "amount_fields": ["valor_total_adjudicacion", "precio_base", "valor_del_contrato"],
        "id_field": "id_del_proceso",
        "order_field": "precio_base DESC",
    },
    "adjudicados": {
        "url": "https://www.datos.gov.co/resource/jbjy-vk9h.json",
        "source": "SECOP II Adjudicados",
        "title_field": "nombre_del_procedimiento",
        "description_field": "descripci_n_del_procedimiento",
        "entity_field": "nombre_de_la_entidad",
        "date_field": "fecha_de_adjudicacion",
        "deadline_field": "fecha_de_fin_del_contrato",
        "amount_fields": ["valor_del_contrato", "valor_de_pago_adelantado", "valor_facturado"],
        "id_field": "id_del_portafolio",
        "order_field": "valor_del_contrato DESC",
    },
    "secop1": {
        "url": "https://www.datos.gov.co/resource/xvdy-vvsk.json",
        "source": "SECOP I",
        "title_field": "nombre_del_procedimiento",
        "description_field": "detalle_del_objeto_a_contratar",
        "entity_field": "nombre_de_la_entidad",
        "date_field": "fecha_de_publicacion_del",
        "deadline_field": "fecha_de_cierre_del_proceso",
        "amount_fields": ["cuantia_proceso", "cuantia_contrato"],
        "id_field": "id_del_proceso",
        "order_field": "cuantia_proceso DESC",
    },
    "ejecucion": {
        "url": "https://www.datos.gov.co/resource/rgxm-mmea.json",
        "source": "SECOP II Ejecución",
        "title_field": "nombre_del_procedimiento",
        "description_field": "descripci_n_del_procedimiento",
        "entity_field": "nombre_de_la_entidad",
        "date_field": "fecha_de_inicio_del_contrato",
        "deadline_field": "fecha_de_fin_del_contrato",
        "amount_fields": ["valor_del_contrato", "valor_contrato_con_adiciones"],
        "id_field": "id_del_portafolio",
        "order_field": "valor_del_contrato DESC",
    },
    "tvec": {
        "url": "https://www.datos.gov.co/resource/s587-gt5p.json",
        "source": "Tienda Virtual",
        "title_field": "descripcion",
        "description_field": "descripcion",
        "entity_field": "entidad_compradora",
        "date_field": "fecha_de_creacion",
        "deadline_field": "fecha_de_creacion",
        "amount_fields": ["valor_total_adjudicacion", "precio_base"],
        "id_field": "id_orden",
        "order_field": "valor_total_adjudicacion DESC",
    },
}

PAGE_SIZE = 1000
MAX_CONTRACTS_PER_RUN = 50000


class SecopScraper(BaseScraper):
    """Scraper para la API de SECOP (Colombia) con paginación y multi-dataset."""

    def __init__(self, dataset_key: str = "procesos"):
        self.dataset_config = SECOP_DATASETS[dataset_key]
        super().__init__(self.dataset_config["url"])

    def fetch_contracts(
        self,
        keywords: List[str] = None,
        min_amount: float = None,
        max_amount: float = None,
        days_back: int = 7
    ) -> List[ContractData]:
        """Obtiene contratos con paginación automática."""
        all_contracts = []
        offset = 0

        while offset < MAX_CONTRACTS_PER_RUN:
            params = self._build_query(keywords, min_amount, max_amount, days_back, offset)

            logger.info(f"🇨🇴 {self.dataset_config['source']} offset={offset}...")

            data = self._safe_request(self.api_url, params)

            if not data:
                break

            for raw in data:
                try:
                    contract = self._normalize_contract(raw)
                    all_contracts.append(contract)
                except Exception as e:
                    logger.error(f"Error normalizando contrato: {e}")
                    continue

            if len(data) < PAGE_SIZE:
                break

            offset += PAGE_SIZE

        logger.info(f"✅ {self.dataset_config['source']}: {len(all_contracts)} contratos obtenidos")
        return all_contracts

    def _build_query(
        self,
        keywords: List[str] = None,
        min_amount: float = None,
        max_amount: float = None,
        days_back: int = 7,
        offset: int = 0,
    ) -> dict:
        """Construye los parámetros de consulta SoQL."""
        cfg = self.dataset_config
        date_limit = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%dT%H:%M:%S')

        conditions = [f"{cfg['date_field']} >= '{date_limit}'"]

        amount_field = cfg["amount_fields"][0] if cfg["amount_fields"] else "precio_base"
        if min_amount:
            conditions.append(f"{amount_field} >= {min_amount}")
        if max_amount:
            conditions.append(f"{amount_field} <= {max_amount}")

        if keywords:
            keyword_conditions = []
            title_field = cfg["title_field"]
            for kw in keywords:
                kw_safe = kw.lower().replace("'", "''")
                keyword_conditions.append(
                    f"lower({title_field}) like '%{kw_safe}%'"
                )
            if keyword_conditions:
                conditions.append(f"({' OR '.join(keyword_conditions)})")

        where_clause = " AND ".join(conditions)

        return {
            "$where": where_clause,
            "$limit": PAGE_SIZE,
            "$offset": offset,
            "$order": cfg.get("order_field", "precio_base DESC"),
        }

    def _normalize_contract(self, raw: dict) -> ContractData:
        """Normaliza un contrato al formato estándar."""
        cfg = self.dataset_config

        external_id = raw.get(cfg["id_field"]) or raw.get("uid", "")
        pub_date = self._parse_date(raw.get(cfg["date_field"]))
        deadline = self._parse_date(raw.get(cfg["deadline_field"]))
        url = self._build_url(raw)

        amount = None
        for amount_field in cfg["amount_fields"]:
            if raw.get(amount_field):
                try:
                    val = float(raw[amount_field])
                    if val > 0:
                        amount = val
                        break
                except (ValueError, TypeError):
                    continue

        return ContractData(
            external_id=str(external_id),
            title=raw.get(cfg["title_field"], "Sin título"),
            description=raw.get(cfg["description_field"], ""),
            entity=raw.get(cfg["entity_field"], ""),
            amount=amount,
            currency="COP",
            country="colombia",
            source=cfg["source"],
            url=url,
            publication_date=pub_date,
            deadline=deadline,
            raw_data=raw,
        )

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parsea una fecha de SECOP."""
        if not date_str:
            return None

        formats = [
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str[:26], fmt)
            except ValueError:
                continue

        return None

    def _build_url(self, raw: dict) -> str:
        """Construye la URL del proceso en SECOP."""
        url_proceso = raw.get("urlproceso")
        if isinstance(url_proceso, dict) and url_proceso.get("url"):
            return url_proceso["url"]

        process_id = raw.get(self.dataset_config["id_field"], "")
        if process_id:
            return f"https://community.secop.gov.co/Public/Tendering/OpportunityDetail/Index?noticeUID=CO1.NTC.{process_id}"

        return "https://www.colombiacompra.gov.co/secop-ii"
