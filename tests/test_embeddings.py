"""
Tests para nlp/embeddings.py

Verifica la migración de pickle → numpy nativo y el comportamiento
del servicio de embeddings (sin cargar el modelo real).
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEmbeddingSerialize:
    """Serialización/deserialización con numpy nativo (sin pickle)."""

    @pytest.fixture
    def service(self):
        from nlp.embeddings import EmbeddingService
        return EmbeddingService()

    def test_serialize_returns_bytes(self, service):
        emb = np.random.rand(384).astype(np.float32)
        result = service.serialize(emb)
        assert isinstance(result, bytes)

    def test_deserialize_returns_ndarray(self, service):
        emb = np.random.rand(384).astype(np.float32)
        data = service.serialize(emb)
        restored = service.deserialize(data)
        assert isinstance(restored, np.ndarray)

    def test_roundtrip_preserves_values(self, service):
        emb = np.array([0.1, 0.2, 0.3, -0.5, 0.8] * 76 + [0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        data = service.serialize(emb)
        restored = service.deserialize(data)
        np.testing.assert_array_almost_equal(emb, restored, decimal=6)

    def test_no_pickle_in_serialized_bytes(self, service):
        """Verifica que la serialización NO use pickle (que empieza con \x80)."""
        emb = np.ones(384, dtype=np.float32)
        data = service.serialize(emb)
        assert not data.startswith(b"\x80"), "Los bytes no deben ser un pickle serializado"

    def test_serialize_converts_to_float32(self, service):
        """Embedding float64 se convierte a float32 al serializar."""
        emb_f64 = np.ones(384, dtype=np.float64)
        data = service.serialize(emb_f64)
        restored = service.deserialize(data)
        assert restored.dtype == np.float32


class TestCreateTextForEmbedding:
    """create_text_for_embedding: prepara texto para generar embeddings."""

    @pytest.fixture
    def service(self):
        from nlp.embeddings import EmbeddingService
        return EmbeddingService()

    def test_only_title(self, service):
        result = service.create_text_for_embedding("Contrato de TI")
        assert result == "Contrato de TI"

    def test_title_and_description(self, service):
        result = service.create_text_for_embedding("Título", description="Descripción")
        assert "Título" in result
        assert "Descripción" in result

    def test_description_truncated_at_500_chars(self, service):
        long_desc = "a" * 600
        result = service.create_text_for_embedding("T", description=long_desc)
        # El texto largo se trunca antes de incluirse
        assert len(result) < 600

    def test_keywords_included(self, service):
        result = service.create_text_for_embedding("T", keywords=["python", "django"])
        assert "python" in result
        assert "django" in result

    def test_empty_title_returns_empty_string(self, service):
        result = service.create_text_for_embedding("")
        assert result == ""


class TestHashKeywords:
    """hash_keywords: genera hash reproducible de keywords."""

    @pytest.fixture
    def service(self):
        from nlp.embeddings import EmbeddingService
        return EmbeddingService()

    def test_same_keywords_same_hash(self, service):
        kw = ["python", "django", "postgresql"]
        assert service.hash_keywords(kw) == service.hash_keywords(kw)

    def test_order_independent(self, service):
        kw1 = ["python", "django"]
        kw2 = ["django", "python"]
        assert service.hash_keywords(kw1) == service.hash_keywords(kw2)

    def test_case_independent(self, service):
        kw1 = ["Python"]
        kw2 = ["python"]
        assert service.hash_keywords(kw1) == service.hash_keywords(kw2)

    def test_different_keywords_different_hash(self, service):
        assert service.hash_keywords(["python"]) != service.hash_keywords(["java"])
