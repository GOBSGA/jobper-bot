"""
Módulo de optimización para scrapers de Jobper Bot.

Incluye:
- Cache con TTL para evitar requests repetidos
- Ejecución paralela de scrapers
- Búsqueda optimizada de keywords con regex compilado

Complejidades:
- Cache hit: O(1)
- Parallel fetch: O(max_latency) vs O(sum_latencies) secuencial
- Keyword matching: O(L) vs O(K × L) sin optimizar
"""

from __future__ import annotations

import hashlib
import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# CACHE CON TTL
# =============================================================================


@dataclass
class CacheEntry:
    """Entrada de cache con timestamp."""

    data: Any
    timestamp: datetime
    hits: int = 0


class TTLCache:
    """
    Cache thread-safe con Time-To-Live.

    Complejidad:
    - get/set: O(1) amortizado
    - cleanup: O(n) pero se ejecuta periódicamente

    Uso:
        cache = TTLCache(ttl_minutes=15)
        cache.set("key", data)
        result = cache.get("key")  # None si expiró
    """

    def __init__(self, ttl_minutes: int = 15, max_entries: int = 1000):
        self._cache: Dict[str, CacheEntry] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
        self._max_entries = max_entries
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def _generate_key(self, *args, **kwargs) -> str:
        """Genera una cache key única basada en argumentos."""
        key_data = f"{args}-{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene valor del cache si existe y no expiró.

        Complejidad: O(1)
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats["misses"] += 1
                return None

            # Verificar TTL
            if datetime.now() - entry.timestamp > self._ttl:
                del self._cache[key]
                self._stats["misses"] += 1
                self._stats["evictions"] += 1
                return None

            entry.hits += 1
            self._stats["hits"] += 1
            return entry.data

    def set(self, key: str, data: Any) -> None:
        """
        Guarda valor en cache.

        Complejidad: O(1) amortizado, O(n) si requiere cleanup
        """
        with self._lock:
            # Cleanup si excede max_entries
            if len(self._cache) >= self._max_entries:
                self._cleanup()

            self._cache[key] = CacheEntry(data=data, timestamp=datetime.now())

    def _cleanup(self) -> None:
        """
        Elimina entradas expiradas y las menos usadas si es necesario.

        Complejidad: O(n log n) por el sort
        """
        now = datetime.now()

        # Eliminar expiradas
        expired = [k for k, v in self._cache.items() if now - v.timestamp > self._ttl]
        for k in expired:
            del self._cache[k]
            self._stats["evictions"] += 1

        # Si aún excede, eliminar las menos usadas (LFU)
        if len(self._cache) >= self._max_entries:
            sorted_entries = sorted(self._cache.items(), key=lambda x: (x[1].hits, x[1].timestamp))
            to_remove = len(self._cache) - self._max_entries // 2
            for key, _ in sorted_entries[:to_remove]:
                del self._cache[key]
                self._stats["evictions"] += 1

    def clear(self) -> None:
        """Limpia todo el cache."""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> dict:
        """Retorna estadísticas del cache."""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total if total > 0 else 0
            return {**self._stats, "entries": len(self._cache), "hit_rate": f"{hit_rate:.1%}"}


# =============================================================================
# EJECUCIÓN PARALELA
# =============================================================================


class ParallelExecutor:
    """
    Ejecutor paralelo para scrapers.

    Complejidad temporal:
    - Secuencial: O(n × avg_latency)
    - Paralelo: O(max_latency)

    Mejora: ~5-10x para 13 scrapers
    """

    def __init__(self, max_workers: int = 10, timeout: int = 30):
        self.max_workers = max_workers
        self.timeout = timeout

    def execute_all(self, tasks: List[Tuple[str, Callable, dict]], fail_fast: bool = False) -> Dict[str, Any]:
        """
        Ejecuta múltiples tareas en paralelo.

        Args:
            tasks: Lista de (nombre, función, kwargs)
            fail_fast: Si True, cancela todo al primer error

        Returns:
            Dict con resultados {nombre: resultado o error}

        Complejidad: O(max_task_time) en tiempo real
        """
        results = {}
        errors = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar todas las tareas
            future_to_name = {executor.submit(func, **kwargs): name for name, func, kwargs in tasks}

            # Recoger resultados conforme terminan
            for future in as_completed(future_to_name, timeout=self.timeout):
                name = future_to_name[future]
                try:
                    results[name] = future.result()
                    logger.debug(f"✅ {name} completado")
                except Exception as e:
                    errors[name] = str(e)
                    logger.warning(f"❌ {name} falló: {e}")

                    if fail_fast:
                        # Cancelar tareas pendientes
                        for f in future_to_name:
                            f.cancel()
                        break

        return {"results": results, "errors": errors}


# =============================================================================
# BÚSQUEDA OPTIMIZADA DE KEYWORDS
# =============================================================================


class KeywordMatcher:
    """
    Matcher de keywords optimizado con regex compilado.

    Complejidad:
    - Sin optimizar: O(K × L) donde K=keywords, L=longitud texto
    - Con regex: O(L) - el regex engine usa autómata

    Uso:
        matcher = KeywordMatcher(["software", "desarrollo", "TI"])
        if matcher.matches("Contrato de desarrollo de software"):
            print("Match!")
    """

    def __init__(self, keywords: List[str] = None):
        self._keywords = []
        self._pattern: Optional[re.Pattern] = None
        self._exclude_pattern: Optional[re.Pattern] = None

        if keywords:
            self.set_keywords(keywords)

    def set_keywords(self, include: List[str] = None, exclude: List[str] = None) -> None:
        """
        Configura keywords de inclusión y exclusión.

        Complejidad: O(K) para compilar
        """
        if include:
            self._keywords = [kw.lower() for kw in include if kw]
            # Crear patrón OR para todas las keywords
            # Escapar caracteres especiales de regex
            escaped = [re.escape(kw) for kw in self._keywords]
            pattern_str = "|".join(escaped)
            self._pattern = re.compile(pattern_str, re.IGNORECASE)
        else:
            self._pattern = None
            self._keywords = []

        if exclude:
            escaped_ex = [re.escape(kw.lower()) for kw in exclude if kw]
            if escaped_ex:
                pattern_str = "|".join(escaped_ex)
                self._exclude_pattern = re.compile(pattern_str, re.IGNORECASE)
        else:
            self._exclude_pattern = None

    def matches(self, text: str) -> bool:
        """
        Verifica si el texto coincide con los criterios.

        Complejidad: O(L) donde L = len(text)

        Returns:
            True si coincide con alguna keyword de inclusión
            y no coincide con ninguna de exclusión
        """
        if not text:
            return False

        # Si no hay keywords, todo coincide
        if not self._pattern:
            return True

        # Verificar exclusiones primero (más rápido fallar temprano)
        if self._exclude_pattern and self._exclude_pattern.search(text):
            return False

        # Verificar inclusiones
        return bool(self._pattern.search(text))

    def find_matches(self, text: str) -> List[str]:
        """
        Encuentra todas las keywords que coinciden.

        Complejidad: O(L × M) donde M = número de matches
        """
        if not text or not self._pattern:
            return []

        return [m.group() for m in self._pattern.finditer(text)]

    def score(self, text: str) -> float:
        """
        Calcula un score de relevancia basado en matches.

        Complejidad: O(L)

        Returns:
            Score entre 0 y 1
        """
        if not text or not self._keywords:
            return 0.0

        matches = self.find_matches(text.lower())
        unique_matches = set(m.lower() for m in matches)

        # Score = keywords encontradas / total keywords
        return len(unique_matches) / len(self._keywords)


# =============================================================================
# SCRAPER WRAPPER CON OPTIMIZACIONES
# =============================================================================


class OptimizedScraperWrapper:
    """
    Wrapper que añade cache y ejecución paralela a cualquier scraper.

    Uso:
        wrapper = OptimizedScraperWrapper(cache_ttl=15, max_workers=10)
        results = wrapper.fetch_parallel([
            ("secop", secop_scraper.fetch_contracts, {"keywords": [...]}),
            ("sam", sam_scraper.fetch_contracts, {"keywords": [...]}),
        ])
    """

    def __init__(self, cache_ttl: int = 15, max_workers: int = 10, request_timeout: int = 30):
        self.cache = TTLCache(ttl_minutes=cache_ttl)
        self.executor = ParallelExecutor(max_workers=max_workers, timeout=request_timeout)
        self.keyword_matcher = KeywordMatcher()

    def fetch_with_cache(self, scraper_name: str, fetch_func: Callable, **kwargs) -> List[Any]:
        """
        Ejecuta fetch con cache.

        Complejidad: O(1) si cache hit, O(fetch) si miss
        """
        cache_key = self.cache._generate_key(scraper_name, **kwargs)

        # Intentar cache
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.info(f"📦 Cache hit para {scraper_name}")
            return cached

        # Fetch y guardar en cache
        logger.info(f"🌐 Fetching {scraper_name}...")
        result = fetch_func(**kwargs)
        self.cache.set(cache_key, result)

        return result

    def fetch_parallel(self, tasks: List[Tuple[str, Callable, dict]], use_cache: bool = True) -> Dict[str, List[Any]]:
        """
        Ejecuta múltiples scrapers en paralelo con cache opcional.

        Args:
            tasks: Lista de (nombre, función, kwargs)
            use_cache: Si usar cache

        Returns:
            Dict {nombre: resultados}

        Complejidad: O(max_latency) + O(1) para cache hits
        """
        if use_cache:
            # Preparar tareas con wrapper de cache
            cached_tasks = []
            results = {}

            for name, func, kwargs in tasks:
                cache_key = self.cache._generate_key(name, **kwargs)
                cached = self.cache.get(cache_key)

                if cached is not None:
                    results[name] = cached
                    logger.info(f"📦 Cache hit: {name}")
                else:
                    cached_tasks.append((name, func, kwargs))

            # Ejecutar solo las que no están en cache
            if cached_tasks:
                parallel_results = self.executor.execute_all(cached_tasks)

                # Guardar en cache y agregar a resultados
                for name, data in parallel_results["results"].items():
                    # Encontrar kwargs original para la cache key
                    for n, _, kw in cached_tasks:
                        if n == name:
                            cache_key = self.cache._generate_key(name, **kw)
                            self.cache.set(cache_key, data)
                            break
                    results[name] = data

            return results
        else:
            # Sin cache, ejecutar todo en paralelo
            parallel_results = self.executor.execute_all(tasks)
            return parallel_results["results"]

    def get_cache_stats(self) -> dict:
        """Retorna estadísticas del cache."""
        return self.cache.get_stats()
