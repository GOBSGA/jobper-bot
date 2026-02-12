"""
Calculador de urgencia para Jobper Bot v3.0
Determina la prioridad de contratos basado en múltiples factores
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class UrgencyScore:
    """Score de urgencia para un contrato."""

    total_score: float  # 0-100
    deadline_score: float  # Puntos por deadline cercano
    value_score: float  # Puntos por valor del contrato
    match_score: float  # Puntos por match con usuario
    priority: str  # "critical", "high", "medium", "low"
    days_until_deadline: Optional[int]
    reasons: List[str]


class UrgencyCalculator:
    """
    Calcula la urgencia/prioridad de un contrato para un usuario.

    Factores considerados:
    - Cercanía del deadline (más cercano = más urgente)
    - Valor del contrato (mayor valor = más importante)
    - Match score con el usuario
    - Tipo de fuente (gobierno vs privado vs multilateral)
    """

    # Pesos para cada factor
    WEIGHTS = {
        "deadline": 50,  # 50% del score
        "value": 20,  # 20% del score
        "match": 20,  # 20% del score
        "source_type": 10,  # 10% del score
    }

    # Prioridades por score total
    PRIORITY_THRESHOLDS = {
        80: "critical",
        60: "high",
        40: "medium",
        0: "low",
    }

    def calculate(self, contract: Dict[str, Any], user: Dict[str, Any], relevance_score: float = 0) -> UrgencyScore:
        """
        Calcula el score de urgencia para un contrato.

        Args:
            contract: Diccionario del contrato
            user: Diccionario del usuario
            relevance_score: Score de relevancia pre-calculado (0-100)

        Returns:
            UrgencyScore con el análisis completo
        """
        reasons = []

        # 1. Score por deadline
        deadline_score, days_until = self._calculate_deadline_score(contract)
        if deadline_score > 0:
            if days_until == 0:
                reasons.append("Cierra HOY")
            elif days_until == 1:
                reasons.append("Cierra mañana")
            elif days_until and days_until <= 3:
                reasons.append(f"Cierra en {days_until} días")

        # 2. Score por valor
        value_score = self._calculate_value_score(contract, user)
        if value_score > 15:
            reasons.append("Alto valor")

        # 3. Score por match (usar el provisto o 0)
        match_score = (relevance_score / 100) * self.WEIGHTS["match"]
        if relevance_score >= 70:
            reasons.append("Alta relevancia")

        # 4. Score por tipo de fuente
        source_score = self._calculate_source_score(contract)
        source_type = contract.get("source_type", "government")
        if source_type == "multilateral":
            reasons.append("Oportunidad multilateral")

        # Calcular total
        total_score = deadline_score + value_score + match_score + source_score
        total_score = max(0, min(100, total_score))

        # Determinar prioridad
        priority = self._get_priority(total_score)

        return UrgencyScore(
            total_score=total_score,
            deadline_score=deadline_score,
            value_score=value_score,
            match_score=match_score,
            priority=priority,
            days_until_deadline=days_until,
            reasons=reasons,
        )

    def _calculate_deadline_score(self, contract: Dict[str, Any]) -> tuple[float, Optional[int]]:
        """
        Calcula score basado en cercanía del deadline.

        Returns:
            Tuple de (score, días_hasta_deadline)
        """
        deadline = contract.get("deadline")
        if not deadline:
            return 0.0, None

        if isinstance(deadline, str):
            try:
                deadline = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
            except ValueError:
                return 0.0, None

        # Normalizar timezone
        if deadline.tzinfo is not None:
            deadline = deadline.replace(tzinfo=None)

        now = datetime.now()
        days_until = (deadline - now).days

        if days_until < 0:
            # Ya venció
            return 0.0, days_until

        max_points = self.WEIGHTS["deadline"]

        if days_until == 0:
            # Cierra hoy - máxima urgencia
            return max_points, days_until
        elif days_until == 1:
            return max_points * 0.9, days_until
        elif days_until == 2:
            return max_points * 0.8, days_until
        elif days_until == 3:
            return max_points * 0.7, days_until
        elif days_until <= 7:
            return max_points * 0.5, days_until
        elif days_until <= 14:
            return max_points * 0.3, days_until
        elif days_until <= 30:
            return max_points * 0.1, days_until
        else:
            return 0.0, days_until

    def _calculate_value_score(self, contract: Dict[str, Any], user: Dict[str, Any]) -> float:
        """Calcula score basado en el valor del contrato."""
        amount = contract.get("amount")
        if not amount:
            return 0.0

        currency = contract.get("currency", "COP")

        # Normalizar a COP
        if currency == "USD":
            amount = amount * 4000

        max_points = self.WEIGHTS["value"]

        # Verificar preferencias de presupuesto del usuario
        min_budget = user.get("min_budget")
        max_budget = user.get("max_budget")

        # Si está dentro del rango preferido, bonus
        in_range = True
        if min_budget and amount < min_budget:
            in_range = False
        if max_budget and amount > max_budget:
            in_range = False

        if in_range:
            # Escala logarítmica basada en el monto
            # Contratos más grandes = más puntos (hasta cierto punto)
            if amount >= 10_000_000_000:  # 10B+
                return max_points
            elif amount >= 1_000_000_000:  # 1B+
                return max_points * 0.8
            elif amount >= 500_000_000:  # 500M+
                return max_points * 0.6
            elif amount >= 100_000_000:  # 100M+
                return max_points * 0.4
            elif amount >= 50_000_000:  # 50M+
                return max_points * 0.2
            else:
                return max_points * 0.1
        else:
            # Fuera del rango preferido, menos puntos
            return max_points * 0.05

    def _calculate_source_score(self, contract: Dict[str, Any]) -> float:
        """Calcula score basado en el tipo de fuente."""
        source_type = contract.get("source_type", "government")
        max_points = self.WEIGHTS["source_type"]

        # Multilaterales tienen menos competencia típicamente
        if source_type == "multilateral":
            return max_points
        elif source_type == "private":
            return max_points * 0.8
        else:  # government
            return max_points * 0.5

    def _get_priority(self, score: float) -> str:
        """Determina la prioridad basada en el score total."""
        for threshold, priority in sorted(self.PRIORITY_THRESHOLDS.items(), reverse=True):
            if score >= threshold:
                return priority
        return "low"

    def batch_calculate(
        self, contracts: List[Dict[str, Any]], user: Dict[str, Any], relevance_scores: Optional[Dict[str, float]] = None
    ) -> List[tuple[Dict[str, Any], UrgencyScore]]:
        """
        Calcula urgencia para múltiples contratos.

        Args:
            contracts: Lista de contratos
            user: Usuario
            relevance_scores: Dict de external_id -> score (opcional)

        Returns:
            Lista de (contrato, UrgencyScore) ordenada por urgencia
        """
        results = []

        for contract in contracts:
            relevance = 0
            if relevance_scores:
                relevance = relevance_scores.get(contract.get("external_id", ""), 0)

            score = self.calculate(contract, user, relevance)
            results.append((contract, score))

        # Ordenar por score total descendente
        results.sort(key=lambda x: x[1].total_score, reverse=True)

        return results


def get_urgency_calculator() -> UrgencyCalculator:
    """Obtiene una instancia del calculador de urgencia."""
    return UrgencyCalculator()
