"""
Scrapers para organizaciones multilaterales (BID, Banco Mundial, ONU)
"""
from scrapers.private.multilateral.idb import IDBScraper
from scrapers.private.multilateral.worldbank import WorldBankScraper
from scrapers.private.multilateral.ungm import UNGMScraper

__all__ = ["IDBScraper", "WorldBankScraper", "UNGMScraper"]
