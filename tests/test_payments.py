"""
Tests para services/payments.py

Cubre lógica de negocio pura (sin DB ni Redis):
- Trust level calculation
- Feature access control por plan
- Plan normalization y jerarquía
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# TRUST LEVEL TESTS
# =============================================================================


class TestCalculateTrustLevel:
    """calculate_trust_level: determina nivel de confianza según pagos verificados."""

    @pytest.fixture(autouse=True)
    def import_fn(self):
        from services.payments import calculate_trust_level
        self.fn = calculate_trust_level

    def test_zero_payments_is_new(self):
        assert self.fn(0) == "new"

    def test_one_payment_is_bronze(self):
        assert self.fn(1) == "bronze"

    def test_two_payments_is_silver(self):
        assert self.fn(2) == "silver"

    def test_four_payments_is_gold(self):
        assert self.fn(4) == "gold"

    def test_eight_payments_is_platinum(self):
        assert self.fn(8) == "platinum"

    def test_large_count_stays_platinum(self):
        assert self.fn(100) == "platinum"

    def test_three_payments_is_silver(self):
        # 3 >= threshold 2 (silver) pero < 4 (gold)
        assert self.fn(3) == "silver"


# =============================================================================
# PLAN ACCESS TESTS
# =============================================================================


class TestCheckFeatureAccess:
    """check_feature_access: controla acceso a features por plan."""

    @pytest.fixture(autouse=True)
    def import_fn(self, monkeypatch):
        from services.payments import check_feature_access
        self.fn = check_feature_access

    def test_ungated_feature_always_accessible(self):
        # Feature que no existe en FEATURE_GATES → acceso libre
        assert self.fn("free", "feature_inexistente") is True

    def test_free_plan_cannot_access_pipeline(self):
        assert self.fn("free", "pipeline") is False

    def test_competidor_can_access_pipeline(self):
        assert self.fn("competidor", "pipeline") is True

    def test_dominador_can_access_all(self):
        # El plan más alto debe tener acceso a todo lo gateado
        gated_features = ["pipeline", "marketplace", "ai_analysis", "push_alerts"]
        for feature in gated_features:
            assert self.fn("dominador", feature) is True, f"dominador debe acceder a {feature}"

    def test_legacy_plan_alias_works(self):
        # 'alertas' es alias de 'cazador' — mismos permisos
        from services.payments import check_feature_access
        assert check_feature_access("alertas", "pipeline") == check_feature_access("cazador", "pipeline")

    def test_cazador_cannot_access_marketplace(self):
        # Marketplace requiere 'competidor' o superior
        assert self.fn("cazador", "marketplace") is False


# =============================================================================
# PLAN NORMALIZATION TESTS
# =============================================================================


class TestNormalizePlan:
    """normalize_plan: convierte aliases heredados a nombres canónicos."""

    @pytest.fixture(autouse=True)
    def import_fn(self):
        from core.plans import normalize_plan
        self.fn = normalize_plan

    def test_canonical_names_unchanged(self):
        for plan in ["free", "cazador", "competidor", "estratega", "dominador"]:
            assert self.fn(plan) == plan

    def test_alertas_normalizes_to_cazador(self):
        assert self.fn("alertas") == "cazador"

    def test_business_normalizes_to_competidor(self):
        assert self.fn("business") == "competidor"

    def test_enterprise_normalizes_to_dominador(self):
        assert self.fn("enterprise") == "dominador"

    def test_empty_string_returns_free(self):
        assert self.fn("") == "free"

    def test_none_returns_free(self):
        assert self.fn(None) == "free"


# =============================================================================
# PLAN HIERARCHY TESTS
# =============================================================================


class TestPlanHierarchy:
    """Verifica que la jerarquía de planes sea correcta y transitiva."""

    def test_dominador_is_highest(self):
        from core.plans import PLAN_ORDER
        assert PLAN_ORDER["dominador"] > PLAN_ORDER["estratega"]
        assert PLAN_ORDER["dominador"] > PLAN_ORDER["competidor"]
        assert PLAN_ORDER["dominador"] > PLAN_ORDER["cazador"]
        assert PLAN_ORDER["dominador"] > PLAN_ORDER["free"]

    def test_plan_order_is_strictly_increasing(self):
        from core.plans import PLAN_ORDER
        canonical = ["free", "cazador", "competidor", "estratega", "dominador"]
        levels = [PLAN_ORDER[p] for p in canonical]
        assert levels == sorted(levels), "Jerarquía de planes debe ser estrictamente creciente"

    def test_check_plan_access_transitivity(self):
        from core.plans import check_plan_access
        # Si dominador >= estratega >= competidor >= cazador >= free
        assert check_plan_access("dominador", "estratega") is True
        assert check_plan_access("estratega", "competidor") is True
        assert check_plan_access("competidor", "cazador") is True
        assert check_plan_access("cazador", "free") is True

    def test_lower_plan_cannot_access_higher(self):
        from core.plans import check_plan_access
        assert check_plan_access("free", "cazador") is False
        assert check_plan_access("cazador", "competidor") is False
        assert check_plan_access("competidor", "estratega") is False
