"""
Scrapers para portales de contratación pública de Latinoamérica.

Países soportados:
- México: CompraNet (gob.mx)
- Chile: ChileCompra (mercadopublico.cl)
- Perú: SEACE (seace.gob.pe)
- Argentina: COMPR.AR (comprar.gob.ar)
- Brasil: ComprasNet (gov.br) + Petrobras
"""

from scrapers.latam.argentina import ComprarScraper
from scrapers.latam.brasil import ComprasNetScraper as BrasilComprasNetScraper
from scrapers.latam.brasil import PetrobrasScraper
from scrapers.latam.chile import ChileCompraScraper
from scrapers.latam.mexico import CompraNetScraper
from scrapers.latam.peru import SeaceScraper

__all__ = [
    "CompraNetScraper",  # México
    "ChileCompraScraper",  # Chile
    "SeaceScraper",  # Perú
    "ComprarScraper",  # Argentina
    "BrasilComprasNetScraper",  # Brasil (gobierno)
    "PetrobrasScraper",  # Brasil (Petrobras)
]
