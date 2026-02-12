"""
Jobper Search — Elasticsearch with PostgreSQL FTS fallback
Natural language query parsing, contract indexing, autocomplete.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from config import Config

logger = logging.getLogger(__name__)

_es_client = None
_es_available = None


# =============================================================================
# ELASTICSEARCH CLIENT
# =============================================================================


def _get_es():
    global _es_client, _es_available

    if _es_available is False:
        return None

    if _es_client is not None:
        return _es_client

    if not Config.ELASTICSEARCH_URL:
        _es_available = False
        return None

    try:
        from elasticsearch import Elasticsearch

        _es_client = Elasticsearch(Config.ELASTICSEARCH_URL)
        _es_client.info()
        _es_available = True
        logger.info("Elasticsearch: connected")
        _ensure_index()
        return _es_client
    except Exception as e:
        logger.warning(f"Elasticsearch unavailable: {e}")
        _es_available = False
        return None


def _ensure_index():
    """Create index with Spanish analyzer if it doesn't exist."""
    es = _es_client
    idx = Config.ELASTICSEARCH_INDEX

    if es and not es.indices.exists(index=idx):
        es.indices.create(
            index=idx,
            body={
                "settings": {
                    "analysis": {
                        "analyzer": {
                            "spanish_custom": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "spanish_stop", "spanish_stemmer"],
                            }
                        },
                        "filter": {
                            "spanish_stop": {"type": "stop", "stopwords": "_spanish_"},
                            "spanish_stemmer": {"type": "stemmer", "language": "spanish"},
                        },
                    }
                },
                "mappings": {
                    "properties": {
                        "title": {"type": "text", "analyzer": "spanish_custom"},
                        "description": {"type": "text", "analyzer": "spanish_custom"},
                        "entity": {"type": "text"},
                        "source": {"type": "keyword"},
                        "country": {"type": "keyword"},
                        "source_type": {"type": "keyword"},
                        "amount": {"type": "float"},
                        "deadline": {"type": "date"},
                        "created_at": {"type": "date"},
                    }
                },
            },
        )
        logger.info(f"ES index '{idx}' created")


def is_healthy() -> bool:
    es = _get_es()
    if es:
        try:
            return es.ping()
        except Exception:
            return False
    return False


# =============================================================================
# INDEX
# =============================================================================


def index_contract(contract_dict: dict):
    """Index a single contract in Elasticsearch."""
    es = _get_es()
    if not es:
        return

    doc = {
        "title": contract_dict.get("title", ""),
        "description": contract_dict.get("description", ""),
        "entity": contract_dict.get("entity", ""),
        "source": contract_dict.get("source", ""),
        "country": contract_dict.get("country", ""),
        "source_type": contract_dict.get("source_type", ""),
        "amount": contract_dict.get("amount"),
        "deadline": contract_dict.get("deadline"),
        "created_at": contract_dict.get("created_at"),
    }

    try:
        es.index(
            index=Config.ELASTICSEARCH_INDEX,
            id=contract_dict.get("id"),
            body=doc,
        )
    except Exception as e:
        logger.error(f"ES index failed: {e}")


def index_contract_by_id(contract_id: int):
    """Fetch contract from DB and index it."""
    from core.database import UnitOfWork

    with UnitOfWork() as uow:
        contract = uow.contracts.get(contract_id)
        if not contract:
            return

        index_contract(
            {
                "id": contract.id,
                "title": contract.title,
                "description": contract.description,
                "entity": contract.entity,
                "source": contract.source,
                "country": contract.country,
                "source_type": contract.source_type,
                "amount": contract.amount,
                "deadline": contract.deadline.isoformat() if contract.deadline else None,
                "created_at": contract.created_at.isoformat() if contract.created_at else None,
            }
        )


# =============================================================================
# SEARCH
# =============================================================================


def search(query: str, user_id: int, page: int = 1, per_page: int = 20) -> dict:
    """Search contracts via Elasticsearch."""
    es = _get_es()
    if not es:
        return {"results": [], "total": 0, "page": page, "pages": 0}

    parsed = parse_natural_query(query)

    # Build ES query
    must = []
    filter_clauses = []

    if parsed.get("text"):
        must.append(
            {
                "multi_match": {
                    "query": parsed["text"],
                    "fields": ["title^3", "description", "entity^2"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            }
        )

    if parsed.get("source"):
        filter_clauses.append({"term": {"source": parsed["source"]}})

    if parsed.get("min_budget"):
        filter_clauses.append({"range": {"amount": {"gte": parsed["min_budget"]}}})

    if parsed.get("max_budget"):
        filter_clauses.append({"range": {"amount": {"lte": parsed["max_budget"]}}})

    body = {
        "query": {
            "bool": {
                "must": must or [{"match_all": {}}],
                "filter": filter_clauses,
            }
        },
        "from": (page - 1) * per_page,
        "size": per_page,
        "sort": [{"_score": "desc"}, {"created_at": "desc"}],
    }

    try:
        resp = es.search(index=Config.ELASTICSEARCH_INDEX, body=body)
        hits = resp["hits"]
        total = hits["total"]["value"] if isinstance(hits["total"], dict) else hits["total"]

        results = []
        for hit in hits["hits"]:
            doc = hit["_source"]
            doc["id"] = int(hit["_id"]) if hit["_id"].isdigit() else hit["_id"]
            doc["_score"] = hit["_score"]
            results.append(doc)

        return {
            "results": results,
            "total": total,
            "page": page,
            "pages": (total + per_page - 1) // per_page,
        }
    except Exception as e:
        logger.error(f"ES search failed: {e}")
        return {"results": [], "total": 0, "page": page, "pages": 0}


# =============================================================================
# AUTOCOMPLETE
# =============================================================================


def suggest(partial_text: str, limit: int = 5) -> list[str]:
    """Return autocomplete suggestions."""
    es = _get_es()
    if not es or not partial_text:
        return []

    try:
        resp = es.search(
            index=Config.ELASTICSEARCH_INDEX,
            body={
                "query": {
                    "multi_match": {
                        "query": partial_text,
                        "fields": ["title", "entity"],
                        "type": "phrase_prefix",
                    }
                },
                "size": limit,
                "_source": ["title"],
            },
        )
        return [hit["_source"]["title"] for hit in resp["hits"]["hits"]]
    except Exception:
        return []


# =============================================================================
# NATURAL LANGUAGE QUERY PARSER
# =============================================================================

# Budget patterns: "más de 100 millones", "entre 50 y 200 millones"
_BUDGET_PATTERNS = [
    (r"más de (\d+)\s*(?:millones?|M)", lambda m: {"min_budget": int(m.group(1)) * 1_000_000}),
    (r"menos de (\d+)\s*(?:millones?|M)", lambda m: {"max_budget": int(m.group(1)) * 1_000_000}),
    (
        r"entre (\d+)\s*y\s*(\d+)\s*(?:millones?|M)",
        lambda m: {
            "min_budget": int(m.group(1)) * 1_000_000,
            "max_budget": int(m.group(2)) * 1_000_000,
        },
    ),
]

# Source patterns
_SOURCE_MAP = {
    "secop": "secop",
    "gobierno": "secop",
    "público": "secop",
    "publico": "secop",
    "ecopetrol": "ecopetrol",
    "epm": "epm",
    "bid": "idb",
    "banco mundial": "worldbank",
    "onu": "ungm",
}

# City patterns
_CITIES = [
    "bogotá",
    "bogota",
    "medellín",
    "medellin",
    "cali",
    "barranquilla",
    "cartagena",
    "bucaramanga",
    "pereira",
    "manizales",
    "cúcuta",
    "cucuta",
    "ibagué",
    "ibague",
    "santa marta",
    "villavicencio",
    "pasto",
    "montería",
]


def parse_natural_query(text: str) -> dict:
    """
    Parse a natural language query into structured search params.
    Example: "software más de 100 millones en bogotá" →
    {"text": "software", "min_budget": 100000000, "city": "bogotá"}
    """
    if not text:
        return {"text": ""}

    result = {"text": text.strip()}
    remaining = text.lower()

    # Extract budget
    for pattern, extractor in _BUDGET_PATTERNS:
        match = re.search(pattern, remaining, re.IGNORECASE)
        if match:
            result.update(extractor(match))
            remaining = remaining[: match.start()] + remaining[match.end() :]

    # Extract source
    for keyword, source_key in _SOURCE_MAP.items():
        if keyword in remaining:
            result["source"] = source_key
            remaining = remaining.replace(keyword, "")

    # Extract city
    for city in _CITIES:
        if city in remaining:
            result["city"] = city
            remaining = remaining.replace(city, "").replace(" en ", " ")

    # Clean remaining text
    result["text"] = " ".join(remaining.split()).strip()

    return result
