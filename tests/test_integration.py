"""
Tests de integración para Jobper Bot v3.0
Verifica que todos los módulos se importan correctamente
"""
import pytest
from datetime import datetime, timedelta


class TestImports:
    """Verifica que todos los módulos se importan correctamente."""

    def test_import_config(self):
        """Config debe importarse sin errores."""
        from config import Config
        assert Config.SECOP_API_URL is not None
        assert Config.INDUSTRIES is not None

    def test_import_database(self):
        """Database models y manager deben importarse."""
        from database.models import User, Contract, ConversationState
        from database.manager import DatabaseManager
        assert User is not None
        assert DatabaseManager is not None

    def test_import_scrapers(self):
        """Scrapers deben importarse sin errores."""
        from scrapers.base import BaseScraper, ContractData
        from scrapers.secop import SecopScraper
        from scrapers.sam import SamGovScraper, CombinedScraper
        assert CombinedScraper is not None

    def test_import_private_scrapers(self):
        """Scrapers privados deben importarse."""
        from scrapers.private.base_private import PrivatePortalScraper
        from scrapers.private.ecopetrol import EcopetrolScraper
        from scrapers.private.epm import EPMScraper
        assert PrivatePortalScraper is not None
        assert EcopetrolScraper is not None
        assert EPMScraper is not None

    def test_import_multilateral_scrapers(self):
        """Scrapers multilaterales deben importarse."""
        from scrapers.private.multilateral.idb import IDBScraper
        from scrapers.private.multilateral.worldbank import WorldBankScraper
        from scrapers.private.multilateral.ungm import UNGMScraper
        assert IDBScraper is not None
        assert WorldBankScraper is not None
        assert UNGMScraper is not None

    def test_import_matching(self):
        """Matching engine debe importarse."""
        from matching.engine import MatchingEngine, get_matching_engine, ScoredContract
        assert MatchingEngine is not None
        assert get_matching_engine is not None

    def test_import_alerts(self):
        """Alerts deben importarse."""
        from alerts.deadline_monitor import DeadlineMonitor, get_deadline_monitor
        from alerts.urgency_calculator import UrgencyCalculator, UrgencyScore
        assert DeadlineMonitor is not None
        assert UrgencyCalculator is not None

    def test_import_scheduler(self):
        """Scheduler debe importarse."""
        from scheduler.jobs import JobScheduler, get_scheduler
        assert JobScheduler is not None
        assert get_scheduler is not None

    def test_import_conversation(self):
        """Conversation handlers deben importarse."""
        from conversation.handlers import ConversationHandler
        from conversation.messages import Messages
        assert ConversationHandler is not None
        assert Messages is not None


class TestCombinedScraper:
    """Tests para el CombinedScraper v3.0."""

    def test_scraper_initialization(self):
        """CombinedScraper debe inicializarse correctamente."""
        from scrapers.sam import CombinedScraper
        scraper = CombinedScraper(include_multilateral=True, include_private=True)
        assert scraper.secop is not None
        assert scraper.sam is not None
        assert scraper.include_multilateral is True
        assert scraper.include_private is True

    def test_get_available_sources(self):
        """get_available_sources debe retornar estructura correcta."""
        from scrapers.sam import CombinedScraper
        scraper = CombinedScraper()
        sources = scraper.get_available_sources()

        assert "government" in sources
        assert "multilateral" in sources
        assert "private" in sources
        assert "secop" in sources["government"]
        assert "sam" in sources["government"]


class TestMatchingEngine:
    """Tests para el MatchingEngine v3.0."""

    def test_engine_weights(self):
        """MatchingEngine debe tener los pesos v3.0."""
        from matching.engine import MatchingEngine
        engine = MatchingEngine(use_semantic=False)

        # Verificar pesos v3.0
        assert engine.WEIGHTS["semantic_match"] == 35
        assert engine.WEIGHTS["keyword_match"] == 25
        assert engine.WEIGHTS["industry_match"] == 15
        assert engine.WEIGHTS["budget_match"] == 15
        assert engine.WEIGHTS["recency"] == 10

    def test_get_user_keywords(self):
        """_get_user_keywords debe combinar industria y personalizadas."""
        from matching.engine import MatchingEngine
        engine = MatchingEngine(use_semantic=False)

        user = {
            "industry": "tecnologia",
            "include_keywords": ["custom1", "custom2"]
        }
        keywords = engine._get_user_keywords(user)

        assert "custom1" in keywords
        assert "custom2" in keywords
        # Debe incluir keywords de industria también
        assert len(keywords) > 2


class TestDeadlineMonitor:
    """Tests para el DeadlineMonitor."""

    def test_urgency_levels(self):
        """DeadlineMonitor debe tener niveles de urgencia correctos."""
        from alerts.deadline_monitor import DeadlineMonitor, UrgencyLevel

        assert UrgencyLevel.CRITICAL.value == 1  # Hoy
        assert UrgencyLevel.HIGH.value == 2  # Mañana
        assert UrgencyLevel.MEDIUM.value == 3  # 3 días

    def test_calculate_urgency(self):
        """_calculate_urgency debe retornar nivel correcto."""
        from alerts.deadline_monitor import DeadlineMonitor

        monitor = DeadlineMonitor()

        # Deadline hoy
        today = datetime.now().replace(hour=23, minute=59)
        assert monitor._calculate_urgency(today) == 1

        # Deadline mañana
        tomorrow = datetime.now() + timedelta(days=1)
        assert monitor._calculate_urgency(tomorrow) == 2

        # Deadline en 2-3 días
        in_3_days = datetime.now() + timedelta(days=3)
        assert monitor._calculate_urgency(in_3_days) == 3

        # Deadline en más de 3 días
        in_5_days = datetime.now() + timedelta(days=5)
        assert monitor._calculate_urgency(in_5_days) is None


class TestUrgencyCalculator:
    """Tests para el UrgencyCalculator."""

    def test_weights_sum_to_100(self):
        """Los pesos deben sumar 100."""
        from alerts.urgency_calculator import UrgencyCalculator

        calculator = UrgencyCalculator()
        total = sum(calculator.WEIGHTS.values())
        assert total == 100

    def test_urgency_score_dataclass(self):
        """UrgencyScore debe ser un dataclass válido."""
        from alerts.urgency_calculator import UrgencyScore

        score = UrgencyScore(
            total_score=85.5,
            deadline_score=50.0,
            value_score=20.0,
            match_score=10.0,
            source_score=5.5,
            priority_label="Alta",
            reasons=["Deadline próximo"]
        )

        assert score.total_score == 85.5
        assert score.priority_label == "Alta"
        assert len(score.reasons) == 1


class TestConversationHandler:
    """Tests para ConversationHandler v3.0."""

    def test_fuentes_command_recognized(self):
        """El comando 'fuentes' debe ser reconocido."""
        from conversation.handlers import ConversationHandler

        handler = ConversationHandler()

        # Simular usuario activo
        user = {
            "phone": "+573001234567",
            "state": "active",
            "industry": "tecnologia"
        }

        # El comando fuentes debe ser manejado globalmente
        # (no podemos testearlo completamente sin mock de DB)
        assert hasattr(handler, '_show_available_sources')


class TestMessages:
    """Tests para Messages v3.0."""

    def test_help_includes_fuentes(self):
        """El mensaje de ayuda debe incluir el comando fuentes."""
        from conversation.messages import Messages

        assert "fuentes" in Messages.HELP.lower()

    def test_urgent_alert_templates(self):
        """Los templates de alertas urgentes deben existir."""
        from conversation.messages import Messages

        assert hasattr(Messages, 'URGENT_ALERT_HEADER')
        assert hasattr(Messages, 'URGENT_ALERT_CONTRACT')
        assert hasattr(Messages, 'URGENT_ALERT_FOOTER')

    def test_welcome_back_includes_fuentes(self):
        """WELCOME_BACK debe incluir opción de fuentes."""
        from conversation.messages import Messages

        assert "5" in Messages.WELCOME_BACK
        assert "fuentes" in Messages.WELCOME_BACK.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
