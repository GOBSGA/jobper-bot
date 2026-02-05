"""
Scrapers para portales de contratación pública de Latinoamérica.

Países soportados:
- México: CompraNet (gob.mx)
- Chile: ChileCompra (mercadopublico.cl)
- Perú: SEACE (seace.gob.pe)
- Argentina: COMPR.AR (comprar.gob.ar)
- Brasil: ComprasNet (gov.br) + Petrobras
"""

from scrapers.latam.mexico import CompraNetScraper
from scrapers.latam.chile import ChileCompraScraper
from scrapers.latam.peru import SeaceScraper
from scrapers.latam.argentina import ComprarScraper
from scrapers.latam.brasil import ComprasNetScraper as BrasilComprasNetScraper, PetrobrasScraper

__all__ = [
    "CompraNetScraper",       # México
    "ChileCompraScraper",     # Chile
    "SeaceScraper",           # Perú
    "ComprarScraper",         # Argentina
    "BrasilComprasNetScraper", # Brasil (gobierno)
    "PetrobrasScraper",       # Brasil (Petrobras)
]
