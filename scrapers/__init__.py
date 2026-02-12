"""
Scrapers package para Jobper Bot v3.0
Incluye scrapers gubernamentales, multilaterales, privados y LATAM
"""

from scrapers.base import BaseScraper, ContractData

# LATAM scrapers
from scrapers.latam import ChileCompraScraper, CompraNetScraper, ComprarScraper, SeaceScraper
from scrapers.sam import CombinedScraper, SamGovScraper
from scrapers.secop import SecopScraper

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
