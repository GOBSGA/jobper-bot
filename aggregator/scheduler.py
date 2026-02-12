"""
Aggregation Scheduler
Programador de agregaciones automáticas.

Ejecuta actualizaciones periódicas de fuentes según su prioridad
y envía notificaciones de nuevos contratos relevantes.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from aggregator.source_registry import SourcePriority, SourceRegistry, get_source_registry
from aggregator.universal import UniversalAggregator, get_aggregator

logger = logging.getLogger(__name__)


@dataclass
class SchedulerStats:
    """Estadísticas del scheduler."""

    started_at: Optional[datetime] = None
    last_run: Optional[datetime] = None
    total_runs: int = 0
    total_contracts_found: int = 0
    total_notifications_sent: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "total_runs": self.total_runs,
            "total_contracts_found": self.total_contracts_found,
            "total_notifications_sent": self.total_notifications_sent,
            "recent_errors": self.errors[-5:] if self.errors else [],
        }


class AggregationScheduler:
    """
    Programador de agregaciones automáticas.

    Ejecuta actualizaciones de fuentes según prioridad:
    - CRITICAL: cada 5 minutos
    - HIGH: cada 15 minutos
    - NORMAL: cada hora
    - LOW: cada 6 horas
    - DAILY: una vez al día
    """

    # Intervalos en segundos por prioridad
    INTERVALS = {
        SourcePriority.CRITICAL: 5 * 60,  # 5 minutos
        SourcePriority.HIGH: 15 * 60,  # 15 minutos
        SourcePriority.NORMAL: 60 * 60,  # 1 hora
        SourcePriority.LOW: 6 * 60 * 60,  # 6 horas
        SourcePriority.DAILY: 24 * 60 * 60,  # 24 horas
    }

    def __init__(
        self,
        aggregator: Optional[UniversalAggregator] = None,
        registry: Optional[SourceRegistry] = None,
        on_new_contracts: Optional[Callable] = None,
    ):
        """
        Inicializa el scheduler.

        Args:
            aggregator: Agregador a usar
            registry: Registro de fuentes
            on_new_contracts: Callback cuando hay nuevos contratos
        """
        self.aggregator = aggregator or get_aggregator()
        self.registry = registry or get_source_registry()
        self.on_new_contracts = on_new_contracts

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_run_by_priority: Dict[SourcePriority, datetime] = {}
        self._known_contract_ids: set = set()

        self.stats = SchedulerStats()

        logger.info("AggregationScheduler inicializado")

    def start(self):
        """Inicia el scheduler en background."""
        if self._running:
            logger.warning("Scheduler ya está corriendo")
            return

        self._running = True
        self.stats.started_at = datetime.now()

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        logger.info("Scheduler iniciado")

    def stop(self):
        """Detiene el scheduler."""
        self._running = False

        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

        logger.info("Scheduler detenido")

    def run_now(self, priority: Optional[SourcePriority] = None) -> Dict[str, Any]:
        """
        Ejecuta agregación inmediata.

        Args:
            priority: Prioridad específica o todas si None

        Returns:
            Resultado de la agregación
        """
        logger.info(f"Ejecutando agregación manual: {priority or 'todas'}")

        if priority:
            sources = self.registry.get_by_priority(priority)
        else:
            sources = self.registry.get_enabled()

        source_keys = list(sources.keys())

        from aggregator.universal import AggregationMode

        result = self.aggregator.aggregate(mode=AggregationMode.SELECTIVE, sources=source_keys, use_cache=False)

        # Procesar nuevos contratos
        new_contracts = self._identify_new_contracts(result.contracts)

        if new_contracts and self.on_new_contracts:
            try:
                self.on_new_contracts(new_contracts)
                self.stats.total_notifications_sent += len(new_contracts)
            except Exception as e:
                logger.error(f"Error en callback de nuevos contratos: {e}")

        self.stats.total_runs += 1
        self.stats.last_run = datetime.now()
        self.stats.total_contracts_found += len(new_contracts)

        return {
            "total_contracts": result.total_contracts,
            "new_contracts": len(new_contracts),
            "sources_queried": result.sources_queried,
            "duration_seconds": result.duration_seconds,
        }

    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado del scheduler."""
        return {
            "running": self._running,
            "stats": self.stats.to_dict(),
            "next_runs": self._get_next_runs(),
            "sources_status": self._get_sources_status(),
        }

    def _run_loop(self):
        """Loop principal del scheduler."""
        logger.info("Scheduler loop iniciado")

        # Esperar un poco antes de la primera ejecución
        time.sleep(10)

        while self._running:
            try:
                self._check_and_run()
            except Exception as e:
                logger.error(f"Error en scheduler loop: {e}")
                self.stats.errors.append({"time": datetime.now().isoformat(), "error": str(e)})

            # Dormir 1 minuto entre checks
            time.sleep(60)

        logger.info("Scheduler loop terminado")

    def _check_and_run(self):
        """Verifica qué fuentes necesitan actualización y las ejecuta."""
        now = datetime.now()

        for priority in SourcePriority:
            interval = self.INTERVALS.get(priority, 3600)
            last_run = self._last_run_by_priority.get(priority)

            # Verificar si es tiempo de ejecutar
            should_run = False
            if last_run is None:
                should_run = True
            elif (now - last_run).total_seconds() >= interval:
                should_run = True

            if should_run:
                self._run_priority(priority)
                self._last_run_by_priority[priority] = now

    def _run_priority(self, priority: SourcePriority):
        """Ejecuta agregación para una prioridad."""
        sources = self.registry.get_by_priority(priority)

        if not sources:
            return

        logger.info(f"Ejecutando agregación {priority.value}: {len(sources)} fuentes")

        source_keys = list(sources.keys())

        try:
            from aggregator.universal import AggregationMode

            result = self.aggregator.aggregate(mode=AggregationMode.SELECTIVE, sources=source_keys, use_cache=False)

            # Identificar contratos nuevos
            new_contracts = self._identify_new_contracts(result.contracts)

            if new_contracts:
                logger.info(f"Encontrados {len(new_contracts)} contratos nuevos")

                if self.on_new_contracts:
                    self.on_new_contracts(new_contracts)
                    self.stats.total_notifications_sent += len(new_contracts)

            self.stats.total_runs += 1
            self.stats.last_run = datetime.now()
            self.stats.total_contracts_found += len(new_contracts)

        except Exception as e:
            logger.error(f"Error ejecutando prioridad {priority}: {e}")
            self.stats.errors.append({"time": datetime.now().isoformat(), "priority": priority.value, "error": str(e)})

    def _identify_new_contracts(self, contracts) -> List:
        """Identifica contratos que no hemos visto antes."""
        new_contracts = []

        for contract in contracts:
            contract_id = getattr(contract, "id", None) or getattr(contract, "external_id", None)

            if contract_id and contract_id not in self._known_contract_ids:
                self._known_contract_ids.add(contract_id)
                new_contracts.append(contract)

        # Limitar tamaño del set de IDs conocidos
        if len(self._known_contract_ids) > 100000:
            # Mantener solo los últimos 50000
            self._known_contract_ids = set(list(self._known_contract_ids)[-50000:])

        return new_contracts

    def _get_next_runs(self) -> Dict[str, str]:
        """Calcula próximas ejecuciones por prioridad."""
        now = datetime.now()
        next_runs = {}

        for priority in SourcePriority:
            interval = self.INTERVALS.get(priority, 3600)
            last_run = self._last_run_by_priority.get(priority)

            if last_run:
                next_run = last_run + timedelta(seconds=interval)
            else:
                next_run = now

            next_runs[priority.value] = next_run.isoformat()

        return next_runs

    def _get_sources_status(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene estado de las fuentes."""
        status = {}

        for key, config in self.registry.get_enabled().items():
            status[key] = {
                "priority": config.priority.value,
                "status": config.status.value,
                "last_fetch": config.last_fetch.isoformat() if config.last_fetch else None,
                "error_count": config.error_count,
            }

        return status


# Singleton
_scheduler = None


def get_aggregation_scheduler(on_new_contracts: Optional[Callable] = None) -> AggregationScheduler:
    """Obtiene la instancia singleton del scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AggregationScheduler(on_new_contracts=on_new_contracts)
    return _scheduler
