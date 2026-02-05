"""
Motor de Matching Inteligente para Jobper v3.0
Calcula relevancia de contratos usando keywords + embeddings semánticos
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field

from scrapers.base import ContractData
from config import Config

logger = logging.getLogger(__name__)


@dataclass
class ScoredContract:
    """Contrato con su score de relevancia calculado."""
    contract: ContractData
    score: float  # 0-100 (score combinado)
    keyword_score: float = 0.0
    semantic_score: float = 0.0
    matched_keywords: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)


class MatchingEngine:
    """
    Motor de matching que calcula la relevancia de contratos para usuarios.

    El score se calcula basado en:
    - Similitud semántica (embeddings) - 35 puntos
    - Coincidencia de palabras clave - 25 puntos
    - Match de industria - 15 puntos
    - Rango de presupuesto - 15 puntos
    - Recencia - 10 puntos
    """

    # Pesos para cada factor del score
    WEIGHTS = {
        "semantic_match": 35,     # NUEVO: Hasta 35 puntos por similitud semántica
        "keyword_match": 25,      # Reducido de 40 a 25 puntos
        "industry_match": 15,     # Reducido de 25 a 15 puntos
        "budget_match": 15,       # Reducido de 20 a 15 puntos
        "recency": 10,            # Reducido de 15 a 10 puntos
    }

    def __init__(self, use_semantic: bool = True):
        """
        Inicializa el motor de matching.

        Args:
            use_semantic: Si True, usa embeddings semánticos (requiere modelo cargado)
        """
        self.use_semantic = use_semantic
        self._semantic_matcher = None

    @property
    def semantic_matcher(self):
        """Lazy loading del matcher semántico."""
        if self._semantic_matcher is None and self.use_semantic:
            try:
                from nlp.semantic_search import get_semantic_matcher
                self._semantic_matcher = get_semantic_matcher()
                logger.info("Matcher semántico cargado")
            except ImportError as e:
                logger.warning(f"No se pudo cargar matcher semántico: {e}")
                self.use_semantic = False
            except Exception as e:
                logger.warning(f"Error cargando matcher semántico: {e}")
                self.use_semantic = False
        return self._semantic_matcher

    def score_contracts_for_user(
        self,
        user: Dict[str, Any],
        contracts: List[ContractData]
    ) -> List[ScoredContract]:
        """
        Calcula el score de relevancia de cada contrato para un usuario.

        Args:
            user: Diccionario con preferencias del usuario
            contracts: Lista de contratos a evaluar

        Returns:
            Lista de ScoredContract ordenada por score descendente
        """
        scored = []

        # Obtener keywords del usuario
        user_keywords = self._get_user_keywords(user)
        exclude_keywords = set(kw.lower() for kw in (user.get("exclude_keywords") or []))

        # Pre-calcular embedding del usuario si semantic está habilitado
        user_embedding = None
        if self.use_semantic and self.semantic_matcher:
            try:
                user_embedding = self.semantic_matcher.compute_user_profile_embedding(
                    user, save_to_db=False
                )
            except Exception as e:
                logger.warning(f"Error calculando embedding de usuario: {e}")

        for contract in contracts:
            # Verificar país
            if not self._matches_country(user, contract):
                continue

            # Verificar exclusiones
            if self._should_exclude(contract, exclude_keywords):
                continue

            # Calcular score
            score_result = self._calculate_score(
                user=user,
                contract=contract,
                user_keywords=user_keywords,
                user_embedding=user_embedding
            )

            if score_result["score"] > 0:
                scored.append(ScoredContract(
                    contract=contract,
                    score=score_result["score"],
                    keyword_score=score_result["keyword_score"],
                    semantic_score=score_result["semantic_score"],
                    matched_keywords=score_result["matched_keywords"],
                    reasons=score_result["reasons"]
                ))

        # Ordenar por score descendente
        scored.sort(key=lambda x: x.score, reverse=True)

        phone = user.get("phone", "unknown")
        logger.info(f"Matching para {phone}: {len(scored)}/{len(contracts)} contratos relevantes")

        return scored

    def get_top_contracts(
        self,
        user: Dict[str, Any],
        contracts: List[ContractData],
        limit: int = 10,
        min_score: float = 25
    ) -> List[ScoredContract]:
        """
        Obtiene los mejores contratos para un usuario.

        Args:
            user: Diccionario con preferencias
            contracts: Lista de contratos
            limit: Máximo de contratos a retornar
            min_score: Score mínimo para incluir

        Returns:
            Top N contratos ordenados por relevancia
        """
        scored = self.score_contracts_for_user(user, contracts)

        # Filtrar por score mínimo
        filtered = [s for s in scored if s.score >= min_score]

        return filtered[:limit]

    def _get_user_keywords(self, user: Dict[str, Any]) -> set:
        """Obtiene todas las keywords del usuario (industria + personalizadas)."""
        keywords = set()

        # Keywords de la industria
        industry = user.get("industry")
        if industry and industry in Config.INDUSTRIES:
            industry_kws = Config.INDUSTRIES[industry].get("keywords", [])
            keywords.update(kw.lower() for kw in industry_kws)

        # Keywords personalizadas
        include_keywords = user.get("include_keywords")
        if include_keywords:
            keywords.update(kw.lower() for kw in include_keywords)

        return keywords

    def _matches_country(self, user: Dict[str, Any], contract: ContractData) -> bool:
        """Verifica si el contrato coincide con el país del usuario."""
        user_countries = user.get("countries", "all")

        if user_countries in ("all", "both"):
            return True

        if user_countries == "colombia" and contract.country == "colombia":
            return True

        if user_countries == "usa" and contract.country == "usa":
            return True

        # Contratos multilaterales siempre pasan si el usuario acepta "all"
        if contract.country == "multilateral" and user_countries == "all":
            return True

        return False

    def _should_exclude(self, contract: ContractData, exclude_keywords: set) -> bool:
        """Verifica si el contrato debe excluirse por keywords negativas."""
        if not exclude_keywords:
            return False

        text = self._get_searchable_text(contract)

        for kw in exclude_keywords:
            if kw in text:
                return True

        return False

    def _get_searchable_text(self, contract: ContractData) -> str:
        """Obtiene el texto de búsqueda del contrato."""
        parts = [
            contract.title or "",
            contract.description or "",
            contract.entity or "",
        ]
        return " ".join(parts).lower()

    def _calculate_score(
        self,
        user: Dict[str, Any],
        contract: ContractData,
        user_keywords: set,
        user_embedding=None
    ) -> Dict[str, Any]:
        """
        Calcula el score total de un contrato para un usuario.

        Returns:
            Dict con score, keyword_score, semantic_score, matched_keywords, reasons
        """
        score = 0.0
        keyword_score = 0.0
        semantic_score = 0.0
        matched_keywords = []
        reasons = []

        text = self._get_searchable_text(contract)

        # 1. SEMANTIC MATCHING (35 puntos máximo) - NUEVO
        if self.use_semantic and self.semantic_matcher and user_embedding is not None:
            try:
                # Crear dict del contrato para el matcher
                contract_dict = {
                    "title": contract.title,
                    "description": contract.description,
                    "entity": contract.entity
                }

                semantic_match = self.semantic_matcher.score_contract_semantic(
                    contract=contract_dict,
                    user=user,
                    user_embedding=user_embedding
                )

                # El semantic_score viene en escala 0-100, normalizar a nuestros puntos
                semantic_score = (semantic_match.semantic_score / 100) * self.WEIGHTS["semantic_match"]
                score += semantic_score

                if semantic_match.semantic_score >= 50:
                    reasons.append(f"✓ Alta similitud semántica ({semantic_match.semantic_score:.0f}%)")
                elif semantic_match.semantic_score >= 30:
                    reasons.append(f"○ Similitud semántica media ({semantic_match.semantic_score:.0f}%)")

            except Exception as e:
                logger.debug(f"Error en scoring semántico: {e}")

        # 2. KEYWORD MATCHING (25 puntos máximo)
        if user_keywords:
            matches = 0
            for kw in user_keywords:
                if kw in text:
                    matches += 1
                    matched_keywords.append(kw)

            if matches > 0:
                keyword_score = min(
                    self.WEIGHTS["keyword_match"],
                    self.WEIGHTS["keyword_match"] * (matches / len(user_keywords)) * 1.5
                )
                score += keyword_score
                reasons.append(f"✓ {matches} palabras clave coinciden")

        # 3. INDUSTRY MATCH (15 puntos)
        industry = user.get("industry")
        if industry and industry in Config.INDUSTRIES:
            industry_kws = Config.INDUSTRIES[industry].get("keywords", [])
            industry_matches = sum(1 for kw in industry_kws if kw.lower() in text)

            if industry_matches > 0:
                industry_score = min(
                    self.WEIGHTS["industry_match"],
                    self.WEIGHTS["industry_match"] * (industry_matches / max(len(industry_kws), 1))
                )
                score += industry_score
                reasons.append(f"✓ Coincide con industria ({industry_matches} términos)")

        # 4. BUDGET MATCH (15 puntos)
        if contract.amount:
            amount = contract.amount

            # Convertir USD a COP si es necesario
            if contract.currency == "USD":
                amount = amount * Config.EXCHANGE_RATES.get("USD_TO_COP", 4000)

            budget_match = True
            min_budget = user.get("min_budget")
            max_budget = user.get("max_budget")

            if min_budget and amount < min_budget:
                budget_match = False
            if max_budget and amount > max_budget:
                budget_match = False

            if budget_match:
                score += self.WEIGHTS["budget_match"]
                reasons.append("✓ Dentro del presupuesto")
            else:
                score -= 5  # Penalización menor
                reasons.append("△ Fuera del rango de presupuesto preferido")

        # 5. RECENCY (10 puntos)
        if contract.publication_date:
            try:
                if isinstance(contract.publication_date, datetime):
                    pub_date = contract.publication_date
                else:
                    pub_date = datetime.fromisoformat(str(contract.publication_date))

                days_old = (datetime.now() - pub_date).days

                if days_old <= 1:
                    score += self.WEIGHTS["recency"]
                    reasons.append("✓ Publicado hoy/ayer")
                elif days_old <= 3:
                    score += self.WEIGHTS["recency"] * 0.8
                    reasons.append("✓ Publicado esta semana")
                elif days_old <= 7:
                    score += self.WEIGHTS["recency"] * 0.5
                    reasons.append("○ Publicado hace una semana")
                else:
                    score += self.WEIGHTS["recency"] * 0.2
            except Exception:
                pass

        # Normalizar score a 0-100
        score = max(0, min(100, score))

        return {
            "score": score,
            "keyword_score": keyword_score,
            "semantic_score": semantic_score,
            "matched_keywords": matched_keywords,
            "reasons": reasons
        }

    def filter_by_budget(
        self,
        contracts: List[ContractData],
        min_amount: float = None,
        max_amount: float = None
    ) -> List[ContractData]:
        """Filtra contratos por rango de presupuesto."""
        filtered = []

        for contract in contracts:
            if not contract.amount:
                continue

            amount = contract.amount

            if min_amount and amount < min_amount:
                continue
            if max_amount and amount > max_amount:
                continue

            filtered.append(contract)

        return filtered

    def deduplicate(
        self,
        contracts: List[ContractData]
    ) -> List[ContractData]:
        """Elimina contratos duplicados por external_id."""
        seen = set()
        unique = []

        for contract in contracts:
            if contract.external_id not in seen:
                seen.add(contract.external_id)
                unique.append(contract)

        return unique


def get_matching_engine(use_semantic: bool = True) -> MatchingEngine:
    """Obtiene una instancia del motor de matching."""
    return MatchingEngine(use_semantic=use_semantic)
