"""
Scrapers para portales privados y multilaterales
"""

from scrapers.private.base_private import PrivatePortalScraper
from scrapers.private.ecopetrol import EcopetrolScraper
from scrapers.private.epm import EPMScraper

__all__ = [
    "PrivatePortalScraper",
    "EcopetrolScraper",
    "EPMScraper",
]
