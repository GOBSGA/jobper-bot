"""
Tests para api/schemas.py

Verifica validaciones de Pydantic: marketplace, auth, contratos.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPublishContractSchema:
    """Validaciones de PublishContractSchema para publicar en marketplace."""

    @pytest.fixture
    def Schema(self):
        from api.schemas import PublishContractSchema
        return PublishContractSchema

    def test_valid_minimal(self, Schema):
        obj = Schema(title="Contrato de desarrollo")
        assert obj.title == "Contrato de desarrollo"

    def test_title_too_short_raises(self, Schema):
        with pytest.raises(Exception):
            Schema(title="ab")  # min_length=5

    def test_budget_min_cannot_exceed_budget_max(self, Schema):
        with pytest.raises(Exception):
            Schema(title="Título válido", budget_min=1_000_000, budget_max=500_000)

    def test_budget_equal_min_max_is_valid(self, Schema):
        obj = Schema(title="Título válido", budget_min=500_000, budget_max=500_000)
        assert obj.budget_min == obj.budget_max

    def test_budget_min_without_max_is_valid(self, Schema):
        obj = Schema(title="Título válido", budget_min=100_000)
        assert obj.budget_min == 100_000
        assert obj.budget_max is None

    def test_budget_max_without_min_is_valid(self, Schema):
        obj = Schema(title="Título válido", budget_max=100_000)
        assert obj.budget_max == 100_000

    def test_negative_budget_raises(self, Schema):
        with pytest.raises(Exception):
            Schema(title="Título válido", budget_min=-1)

    def test_excessive_budget_raises(self, Schema):
        # Más de 10 billones COP → fuera de rango
        with pytest.raises(Exception):
            Schema(title="Título válido", budget_max=100_000_000_000_000)

    def test_is_remote_defaults_to_false(self, Schema):
        obj = Schema(title="Título válido")
        assert obj.is_remote is False

    def test_keywords_limited(self, Schema):
        # Solo 20 keywords máximo
        obj = Schema(title="Título válido", keywords=["kw"] * 25)
        assert len(obj.keywords) == 20
