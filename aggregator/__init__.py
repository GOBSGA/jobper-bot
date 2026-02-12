"""
Jobper Universal Aggregator
Sistema de agregación universal de fuentes de contratos.

Permite conectar cualquier fuente de datos (APIs, scrapers, feeds)
y normalizar los contratos a un formato común para procesamiento.
"""

from aggregator.normalizer import ContractNormalizer
from aggregator.scheduler import AggregationScheduler
from aggregator.source_registry import SourceConfig, SourceRegistry
from aggregator.universal import UniversalAggregator

__all__ = ["UniversalAggregator", "SourceRegistry", "SourceConfig", "ContractNormalizer", "AggregationScheduler"]
