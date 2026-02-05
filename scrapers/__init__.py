"""
Scrapers package para Jobper Bot v3.0
Incluye scrapers gubernamentales, multilaterales, privados y LATAM
"""
from scrapers.base import BaseScraper, ContractData
from scrapers.secop import SecopScraper
from scrapers.sam import SamGovScraper, CombinedScraper

# LATAM scrapers
from scrapers.latam import (
    CompraNetScraper,
    ChileCompraScraper,
    SeaceScraper,
    ComprarScraper,
)

__all__ = [
    "BaseScraper",
    "ContractData",
    "SecopScraper",
    "SamGovScraper",
    "CombinedScraper",
    # LATAM
    "CompraNetScraper",
    "ChileCompraScraper",
    "SeaceScraper",
    "ComprarScraper",
]
