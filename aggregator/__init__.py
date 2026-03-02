"""
Jobper Universal Aggregator
Sistema de agregación universal de fuentes de contratos.

Permite conectar cualquier fuente de datos (APIs, scrapers, feeds)
y normalizar los contratos a un formato común para procesamiento.

ESTADO (2026-03): Módulo candidato a futura integración.
  - El pipeline activo de ingesta usa services/ingestion.py (llamado desde app.py cada 6h).
  - Este aggregator es un diseño más avanzado con prioridades por fuente (CRITICAL/HIGH/NORMAL)
    y ThreadPoolExecutor, pero actualmente NO está conectado al flujo de producción.
  - Decisión pendiente: migrar services/ingestion.py hacia este sistema o descartarlo.
  - NO eliminar sin evaluar primero: contiene ContractNormalizer con lógica de
    normalización de monedas y categorías que no existe en services/.
"""

from aggregator.normalizer import ContractNormalizer
from aggregator.scheduler import AggregationScheduler
from aggregator.source_registry import SourceConfig, SourceRegistry
from aggregator.universal import UniversalAggregator

__all__ = ["UniversalAggregator", "SourceRegistry", "SourceConfig", "ContractNormalizer", "AggregationScheduler"]
