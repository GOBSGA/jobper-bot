"""
Scrapers package para Jobper Bot v5.0
Scrapers activos: Colombia (SECOP), privados colombianos y multilaterales.
"""

from scrapers.base import BaseScraper, ContractData
from scrapers.secop import SecopScraper

__all__ = [
    "BaseScraper",
    "ContractData",
    "SecopScraper",
]
