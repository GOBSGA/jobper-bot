"""
Jobper Universal Aggregator
Sistema de agregación universal de fuentes de contratos.

Permite conectar cualquier fuente de datos (APIs, scrapers, feeds)
y normalizar los contratos a un formato común para procesamiento.
"""
from aggregator.universal import UniversalAggregator
from aggregator.source_registry import SourceRegistry, SourceConfig
from aggregator.normalizer import ContractNormalizer
from aggregator.scheduler import AggregationScheduler

__all__ = [
    "UniversalAggregator",
    "SourceRegistry",
    "SourceConfig",
    "ContractNormalizer",
    "AggregationScheduler"
]
