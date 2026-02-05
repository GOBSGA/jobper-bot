"""
Módulo NLP para Jobper Bot v3.0
Incluye embeddings semánticos, búsqueda por similitud y análisis de contratos con IA
"""
from nlp.embeddings import EmbeddingService, get_embedding_service
from nlp.semantic_search import SemanticMatcher, get_semantic_matcher
from nlp.cache import EmbeddingCache
from nlp.contract_analyzer import ContractAnalyzer, ContractAnalysis, format_analysis_for_whatsapp

__all__ = [
    "EmbeddingService",
    "get_embedding_service",
    "SemanticMatcher",
    "get_semantic_matcher",
    "EmbeddingCache",
    "ContractAnalyzer",
    "ContractAnalysis",
    "format_analysis_for_whatsapp",
]
