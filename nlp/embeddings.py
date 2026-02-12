"""
Servicio de embeddings para Jobper Bot v3.0
Genera y gestiona embeddings semánticos usando sentence-transformers
"""

from __future__ import annotations

import hashlib
import logging
import pickle
from typing import List, Optional, Union

import numpy as np

from config import Config

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Servicio para generar y comparar embeddings semánticos.

    Usa sentence-transformers con un modelo multilingüe para
    soportar español e inglés.
    """

    _instance = None
    _model = None

    def __new__(cls):
        """Singleton para evitar cargar el modelo múltiples veces."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def model(self):
        """Carga lazy del modelo de embeddings."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info(f"Cargando modelo de embeddings: {Config.EMBEDDING_MODEL}")
                self._model = SentenceTransformer(Config.EMBEDDING_MODEL)
                logger.info("Modelo cargado exitosamente")
            except ImportError:
                logger.error("sentence-transformers no instalado. Instalar con: pip install sentence-transformers")
                raise
            except Exception as e:
                logger.error(f"Error cargando modelo: {e}")
                raise
        return self._model

    @property
    def model_name(self) -> str:
        """Nombre del modelo actual."""
        return Config.EMBEDDING_MODEL

    @property
    def dimension(self) -> int:
        """Dimensión de los embeddings."""
        return Config.EMBEDDING_DIMENSION

    def encode(self, texts: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        Genera embeddings para uno o más textos.

        Args:
            texts: Texto o lista de textos a codificar
            normalize: Si True, normaliza los vectores (recomendado para similitud coseno)

        Returns:
            np.ndarray: Array de embeddings con shape (n_texts, dimension)
        """
        if isinstance(texts, str):
            texts = [texts]

        # Limpiar textos vacíos
        texts = [t.strip() if t else "" for t in texts]

        try:
            embeddings = self.model.encode(
                texts, convert_to_numpy=True, normalize_embeddings=normalize, show_progress_bar=False
            )
            return embeddings
        except Exception as e:
            logger.error(f"Error generando embeddings: {e}")
            raise

    def encode_single(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        Genera embedding para un solo texto.

        Args:
            text: Texto a codificar

        Returns:
            np.ndarray: Vector de embedding con shape (dimension,)
        """
        embeddings = self.encode([text], normalize=normalize)
        return embeddings[0]

    def similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calcula la similitud coseno entre dos embeddings.

        Args:
            emb1: Primer embedding
            emb2: Segundo embedding

        Returns:
            float: Similitud coseno en rango [-1, 1], típicamente [0, 1] para textos
        """
        # Si los embeddings están normalizados, el producto punto es el coseno
        if emb1.ndim == 1 and emb2.ndim == 1:
            return float(np.dot(emb1, emb2))

        # Para matrices
        return float(np.dot(emb1, emb2.T))

    def batch_similarity(self, query_embedding: np.ndarray, corpus_embeddings: np.ndarray) -> np.ndarray:
        """
        Calcula similitud entre un query y múltiples documentos.

        Args:
            query_embedding: Embedding del query (dimension,)
            corpus_embeddings: Embeddings del corpus (n_docs, dimension)

        Returns:
            np.ndarray: Array de similitudes (n_docs,)
        """
        if corpus_embeddings.ndim == 1:
            corpus_embeddings = corpus_embeddings.reshape(1, -1)

        return np.dot(corpus_embeddings, query_embedding)

    def serialize(self, embedding: np.ndarray) -> bytes:
        """
        Serializa un embedding para almacenamiento en base de datos.

        Args:
            embedding: Embedding a serializar

        Returns:
            bytes: Embedding serializado
        """
        return pickle.dumps(embedding.astype(np.float32))

    def deserialize(self, data: bytes) -> np.ndarray:
        """
        Deserializa un embedding desde bytes.

        Args:
            data: Bytes del embedding

        Returns:
            np.ndarray: Embedding deserializado
        """
        return pickle.loads(data)

    def create_text_for_embedding(
        self,
        title: str,
        description: Optional[str] = None,
        entity: Optional[str] = None,
        keywords: Optional[List[str]] = None,
    ) -> str:
        """
        Crea un texto optimizado para generar embedding.

        Combina título, descripción, entidad y keywords en un formato
        que maximiza la captura semántica.

        Args:
            title: Título del contrato/documento
            description: Descripción opcional
            entity: Entidad contratante opcional
            keywords: Lista de palabras clave opcionales

        Returns:
            str: Texto combinado para embedding
        """
        parts = []

        if title:
            parts.append(title.strip())

        if description:
            # Truncar descripción a 500 chars para evitar textos muy largos
            desc = description.strip()[:500]
            parts.append(desc)

        if entity:
            parts.append(f"Entidad: {entity.strip()}")

        if keywords:
            parts.append(f"Keywords: {', '.join(keywords)}")

        return " | ".join(parts)

    def hash_keywords(self, keywords: List[str]) -> str:
        """
        Genera un hash de una lista de keywords para detectar cambios.

        Args:
            keywords: Lista de keywords

        Returns:
            str: Hash MD5 de las keywords ordenadas
        """
        sorted_kw = sorted([k.lower().strip() for k in keywords])
        text = ",".join(sorted_kw)
        return hashlib.md5(text.encode()).hexdigest()


def get_embedding_service() -> EmbeddingService:
    """Obtiene la instancia singleton del servicio de embeddings."""
    return EmbeddingService()
