"""
Scrapers para organizaciones multilaterales (BID, Banco Mundial, ONU)

Lazy imports to avoid deadlocks when source_registry loads scrapers
via importlib in parallel — eager imports in __init__.py caused
_ModuleLock deadlocks between idb/ungm/worldbank.
"""


def __getattr__(name):
    if name == "IDBScraper":
        from scrapers.private.multilateral.idb import IDBScraper

        return IDBScraper
    if name == "WorldBankScraper":
        from scrapers.private.multilateral.worldbank import WorldBankScraper

        return WorldBankScraper
    if name == "UNGMScraper":
        from scrapers.private.multilateral.ungm import UNGMScraper

        return UNGMScraper
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["IDBScraper", "WorldBankScraper", "UNGMScraper"]
