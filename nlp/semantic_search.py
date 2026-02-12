"""
Motor de búsqueda semántica para Jobper Bot v3.0
Encuentra contratos relevantes usando similitud de embeddings
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np

from config import Config
from database.manager import DatabaseManager
from nlp.embeddings import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)


@dataclass
class SemanticMatch:
    """Resultado de una búsqueda semántica."""

    contract: Dict[str, Any]
    semantic_score: float
    matched_industries: List[str]
    explanation: str


class SemanticMatcher:
    """
    Motor de matching semántico para contratos.

    Compara embeddings de contratos con perfiles de usuario
    e industrias para encontrar los más relevantes.
    """

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.db = DatabaseManager()
        self._industry_embeddings_cache: Dict[str, np.ndarray] = {}

    def initialize_industry_embeddings(self) -> int:
        """
        Pre-computa y almacena embeddings para todas las industrias.

        Returns:
            int: Número de industrias procesadas
        """
        count = 0

        for industry_key, industry_data in Config.INDUSTRIES.items():
            keywords = industry_data.get("keywords", [])
            if not keywords:
                continue

            # Crear texto representativo de la industria
            industry_text = self.embedding_service.create_text_for_embedding(
                title=industry_data["name"], keywords=keywords
            )

            # Generar embedding
            embedding = self.embedding_service.encode_single(industry_text)
            embedding_bytes = self.embedding_service.serialize(embedding)
            keywords_hash = self.embedding_service.hash_keywords(keywords)

            # Guardar en base de datos
            self.db.get_or_create_industry_embedding(
                industry_key=industry_key,
                embedding=embedding_bytes,
                keywords_hash=keywords_hash,
                model_name=self.embedding_service.model_name,
            )

            # Cachear en memoria
            self._industry_embeddings_cache[industry_key] = embedding

            logger.info(f"Embedding generado para industria: {industry_key}")
            count += 1

        return count

    def get_industry_embedding(self, industry_key: str) -> Optional[np.ndarray]:
        """
        Obtiene el embedding de una industria (de caché o BD).

        Args:
            industry_key: Clave de la industria

        Returns:
            np.ndarray o None: Embedding de la industria
        """
        # Primero buscar en caché
        if industry_key in self._industry_embeddings_cache:
            return self._industry_embeddings_cache[industry_key]

        # Buscar en base de datos
        ind_emb = self.db.get_industry_embedding(industry_key)
        if ind_emb and ind_emb.get("embedding"):
            embedding = self.embedding_service.deserialize(ind_emb["embedding"])
            self._industry_embeddings_cache[industry_key] = embedding
            return embedding

        return None

    def load_all_industry_embeddings(self) -> int:
        """
        Carga todos los embeddings de industrias en caché.

        Returns:
            int: Número de embeddings cargados
        """
        all_emb = self.db.get_all_industry_embeddings()

        for ind_emb in all_emb:
            if ind_emb.get("embedding"):
                embedding = self.embedding_service.deserialize(ind_emb["embedding"])
                self._industry_embeddings_cache[ind_emb["industry_key"]] = embedding

        return len(self._industry_embeddings_cache)

    def compute_contract_embedding(self, contract: Dict[str, Any], save_to_db: bool = True) -> np.ndarray:
        """
        Genera y opcionalmente guarda el embedding de un contrato.

        Args:
            contract: Diccionario del contrato
            save_to_db: Si True, guarda el embedding en la BD

        Returns:
            np.ndarray: Embedding del contrato
        """
        # Crear texto para embedding
        text = self.embedding_service.create_text_for_embedding(
            title=contract.get("title", ""), description=contract.get("description"), entity=contract.get("entity")
        )

        embedding = self.embedding_service.encode_single(text)

        if save_to_db and contract.get("id"):
            embedding_bytes = self.embedding_service.serialize(embedding)
            self.db.update_contract_embedding(
                contract_id=contract["id"], embedding=embedding_bytes, model_name=self.embedding_service.model_name
            )

        return embedding

    def compute_user_profile_embedding(self, user: Dict[str, Any], save_to_db: bool = True) -> np.ndarray:
        """
        Genera y opcionalmente guarda el embedding del perfil de un usuario.

        Combina la industria del usuario con sus keywords personalizadas.

        Args:
            user: Diccionario del usuario
            save_to_db: Si True, guarda el embedding en la BD

        Returns:
            np.ndarray: Embedding del perfil
        """
        parts = []

        # Agregar nombre de industria
        industry = user.get("industry")
        if industry and industry in Config.INDUSTRIES:
            parts.append(Config.INDUSTRIES[industry]["name"])
            parts.extend(Config.INDUSTRIES[industry].get("keywords", []))

        # Agregar keywords del usuario
        include_kw = user.get("include_keywords", [])
        if include_kw:
            parts.extend(include_kw)

        if not parts:
            # Usuario sin preferencias, usar embedding genérico
            parts = ["contrato", "licitación", "oportunidad"]

        text = " ".join(parts)
        embedding = self.embedding_service.encode_single(text)

        if save_to_db and user.get("phone"):
            embedding_bytes = self.embedding_service.serialize(embedding)
            self.db.update_user_embedding(phone=user["phone"], embedding=embedding_bytes)

        return embedding

    def score_contract_semantic(
        self,
        contract: Dict[str, Any],
        user: Dict[str, Any],
        contract_embedding: Optional[np.ndarray] = None,
        user_embedding: Optional[np.ndarray] = None,
    ) -> SemanticMatch:
        """
        Calcula el score semántico de un contrato para un usuario.

        Args:
            contract: Diccionario del contrato
            user: Diccionario del usuario
            contract_embedding: Embedding pre-calculado del contrato (opcional)
            user_embedding: Embedding pre-calculado del usuario (opcional)

        Returns:
            SemanticMatch: Resultado con score y explicación
        """
        # Obtener o calcular embeddings
        if contract_embedding is None:
            contract_embedding = self.compute_contract_embedding(contract, save_to_db=False)

        if user_embedding is None:
            user_embedding = self.compute_user_profile_embedding(user, save_to_db=False)

        # Calcular similitud con perfil del usuario
        user_similarity = self.embedding_service.similarity(contract_embedding, user_embedding)

        # Calcular similitud con industria del usuario
        industry_similarity = 0.0
        matched_industries = []

        industry = user.get("industry")
        if industry:
            ind_embedding = self.get_industry_embedding(industry)
            if ind_embedding is not None:
                industry_similarity = self.embedding_service.similarity(contract_embedding, ind_embedding)
                if industry_similarity > Config.SEMANTIC_SIMILARITY_THRESHOLD:
                    matched_industries.append(industry)

        # Score combinado (ponderado)
        # 60% similitud con perfil completo, 40% similitud con industria
        combined_score = (user_similarity * 0.6) + (industry_similarity * 0.4)

        # Normalizar a escala 0-100
        semantic_score = max(0, min(100, combined_score * 100))

        # Generar explicación
        explanation = self._generate_explanation(
            user_similarity=user_similarity,
            industry_similarity=industry_similarity,
            industry=industry,
            semantic_score=semantic_score,
        )

        return SemanticMatch(
            contract=contract,
            semantic_score=semantic_score,
            matched_industries=matched_industries,
            explanation=explanation,
        )

    def find_similar_contracts(
        self, contracts: List[Dict[str, Any]], user: Dict[str, Any], min_score: float = 30.0, limit: int = 20
    ) -> List[SemanticMatch]:
        """
        Encuentra los contratos más similares para un usuario.

        Args:
            contracts: Lista de contratos a evaluar
            user: Usuario para el cual buscar
            min_score: Score mínimo para incluir (0-100)
            limit: Máximo de resultados

        Returns:
            List[SemanticMatch]: Lista de matches ordenados por score
        """
        if not contracts:
            return []

        # Pre-calcular embedding del usuario
        user_embedding = self.compute_user_profile_embedding(user, save_to_db=False)

        matches = []

        for contract in contracts:
            match = self.score_contract_semantic(contract=contract, user=user, user_embedding=user_embedding)

            if match.semantic_score >= min_score:
                matches.append(match)

        # Ordenar por score descendente
        matches.sort(key=lambda x: x.semantic_score, reverse=True)

        return matches[:limit]

    def batch_compute_embeddings(self, contracts: List[Dict[str, Any]], batch_size: int = 32) -> List[np.ndarray]:
        """
        Calcula embeddings para múltiples contratos en batch.

        Args:
            contracts: Lista de contratos
            batch_size: Tamaño del batch para procesamiento

        Returns:
            List[np.ndarray]: Lista de embeddings
        """
        texts = []
        for contract in contracts:
            text = self.embedding_service.create_text_for_embedding(
                title=contract.get("title", ""), description=contract.get("description"), entity=contract.get("entity")
            )
            texts.append(text)

        # Procesar en batches
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_embeddings = self.embedding_service.encode(batch_texts)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def _generate_explanation(
        self, user_similarity: float, industry_similarity: float, industry: Optional[str], semantic_score: float
    ) -> str:
        """Genera una explicación legible del score."""
        parts = []

        if semantic_score >= 70:
            parts.append("Alta relevancia")
        elif semantic_score >= 50:
            parts.append("Relevancia media")
        elif semantic_score >= 30:
            parts.append("Relevancia baja")
        else:
            parts.append("Poca relevancia")

        if industry and industry_similarity > 0.5:
            industry_name = Config.INDUSTRIES.get(industry, {}).get("name", industry)
            parts.append(f"coincide con {industry_name}")

        return " - ".join(parts)


def get_semantic_matcher() -> SemanticMatcher:
    """Obtiene una instancia del matcher semántico."""
    return SemanticMatcher()
