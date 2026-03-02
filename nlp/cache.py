"""
Caché de embeddings para Jobper Bot v3.0
Gestiona el caché en memoria y persistencia de embeddings
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """
    Caché en memoria para embeddings con TTL y límite de tamaño.

    Optimiza el rendimiento evitando recálculos frecuentes de embeddings.
    """

    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        """
        Inicializa el caché.

        Args:
            max_size: Máximo número de embeddings en caché
            ttl_hours: Tiempo de vida de cada entrada en horas
        """
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self._cache: Dict[str, Tuple[np.ndarray, datetime]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[np.ndarray]:
        """
        Obtiene un embedding del caché.

        Args:
            key: Clave del embedding

        Returns:
            np.ndarray o None si no existe o expiró
        """
        with self._lock:
            if key not in self._cache:
                return None

            embedding, timestamp = self._cache[key]

            # Verificar TTL
            if datetime.now(timezone.utc) - timestamp > self.ttl:
                del self._cache[key]
                return None

            return embedding

    def set(self, key: str, embedding: np.ndarray) -> None:
        """
        Guarda un embedding en el caché.

        Args:
            key: Clave del embedding
            embedding: Embedding a guardar
        """
        with self._lock:
            # Limpiar si excede el tamaño máximo
            if len(self._cache) >= self.max_size:
                self._evict_oldest()

            self._cache[key] = (embedding, datetime.now(timezone.utc))

    def delete(self, key: str) -> bool:
        """
        Elimina un embedding del caché.

        Args:
            key: Clave del embedding

        Returns:
            bool: True si se eliminó, False si no existía
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> int:
        """
        Limpia todo el caché.

        Returns:
            int: Número de entradas eliminadas
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    def size(self) -> int:
        """Retorna el número de entradas en caché."""
        return len(self._cache)

    def _evict_oldest(self) -> None:
        """Elimina las entradas más antiguas (25% del caché)."""
        if not self._cache:
            return

        # Ordenar por timestamp y eliminar el 25% más antiguo
        sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][1])

        to_remove = max(1, len(sorted_keys) // 4)
        for key in sorted_keys[:to_remove]:
            del self._cache[key]

        logger.debug(f"Evicted {to_remove} entries from embedding cache")

    def cleanup_expired(self) -> int:
        """
        Elimina todas las entradas expiradas.

        Returns:
            int: Número de entradas eliminadas
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            expired_keys = [key for key, (_, timestamp) in self._cache.items() if now - timestamp > self.ttl]

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

            return len(expired_keys)

    def get_stats(self) -> Dict[str, any]:
        """Obtiene estadísticas del caché."""
        with self._lock:
            now = datetime.now(timezone.utc)
            ages = [(now - timestamp).total_seconds() / 3600 for _, timestamp in self._cache.values()]

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl_hours": self.ttl.total_seconds() / 3600,
                "avg_age_hours": sum(ages) / len(ages) if ages else 0,
                "oldest_hours": max(ages) if ages else 0,
            }


# Instancia global del caché
_contract_cache: Optional[EmbeddingCache] = None
_user_cache: Optional[EmbeddingCache] = None


def get_contract_cache() -> EmbeddingCache:
    """Obtiene el caché de embeddings de contratos."""
    global _contract_cache
    if _contract_cache is None:
        _contract_cache = EmbeddingCache(max_size=5000, ttl_hours=48)
    return _contract_cache


def get_user_cache() -> EmbeddingCache:
    """Obtiene el caché de embeddings de usuarios."""
    global _user_cache
    if _user_cache is None:
        _user_cache = EmbeddingCache(max_size=500, ttl_hours=168)  # 1 semana
    return _user_cache


def contract_cache_key(external_id: str) -> str:
    """Genera clave de caché para un contrato."""
    return f"contract:{external_id}"


def user_cache_key(phone: str) -> str:
    """Genera clave de caché para un usuario."""
    return f"user:{phone}"
