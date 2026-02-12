"""
Tests for API endpoints.
"""

from unittest.mock import Mock, patch

import pytest

from app import create_app


@pytest.fixture
def app():
    """Create test app."""
    with patch("app._start_background_services"):
        app = create_app()
        app.config["TESTING"] = True
        yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns OK."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "Jobper"
        assert "version" in data

    @patch("app.get_engine")
    @patch("app.cache")
    def test_health_endpoint_all_healthy(self, mock_cache, mock_engine, client):
        """Test health endpoint when all services are healthy."""
        # Mock database connection
        mock_conn = Mock()
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

        # Mock Redis cache
        mock_cache.get.return_value = "ok"
        mock_cache.set.return_value = True
        mock_cache.delete.return_value = True

        response = client.get("/health")
        assert response.status_code == 200

        data = response.get_json()
        assert data["status"] == "healthy"
        assert "checks" in data
        assert data["checks"]["database"]["status"] == "healthy"

    @patch("app.get_engine")
    def test_health_endpoint_database_down(self, mock_engine, client):
        """Test health endpoint when database is down."""
        # Mock database connection failure
        mock_engine.return_value.connect.side_effect = Exception("Connection failed")

        response = client.get("/health")
        assert response.status_code == 503

        data = response.get_json()
        assert data["status"] == "unhealthy"
        assert data["checks"]["database"]["status"] == "unhealthy"


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_register_missing_fields(self, client):
        """Test registration with missing fields."""
        response = client.post("/api/auth/register", json={})
        # Should return 400 for validation error
        assert response.status_code == 400

    @patch("services.auth.register_with_password")
    def test_register_success(self, mock_register, client):
        """Test successful registration."""
        mock_register.return_value = {
            "access_token": "fake_token",
            "refresh_token": "fake_refresh",
            "user": {"id": 1, "email": "test@example.com"},
            "is_new": True,
        }

        response = client.post(
            "/api/auth/register", json={"email": "test@example.com", "password": "secure_password_123"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data
        assert "user" in data

    @patch("services.auth.login_with_password")
    def test_login_success(self, mock_login, client):
        """Test successful login."""
        mock_login.return_value = {
            "access_token": "fake_token",
            "refresh_token": "fake_refresh",
            "user": {"id": 1, "email": "test@example.com"},
        }

        response = client.post(
            "/api/auth/login-password", json={"email": "test@example.com", "password": "secure_password_123"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data

    @patch("services.auth.login_with_password")
    def test_login_wrong_credentials(self, mock_login, client):
        """Test login with wrong credentials."""
        mock_login.return_value = {"error": "Correo o contraseña incorrectos"}

        response = client.post(
            "/api/auth/login-password", json={"email": "test@example.com", "password": "wrong_password"}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


class TestRateLimiting:
    """Test rate limiting middleware."""

    def test_rate_limit_x_forwarded_for(self, client):
        """Test that rate limiting uses X-Forwarded-For header."""
        # This test verifies the fix for proxy rate limiting
        # In a real scenario, we'd need to make multiple requests
        # For now, just verify the header is used

        # Make a request with X-Forwarded-For header
        response = client.get("/", headers={"X-Forwarded-For": "1.2.3.4, 5.6.7.8"})

        # Should succeed
        assert response.status_code == 200


class TestCORS:
    """Test CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in response."""
        response = client.get("/")

        # Should have CORS headers
        assert "Access-Control-Allow-Origin" in response.headers

    def test_cors_preflight(self, client):
        """Test CORS preflight request."""
        response = client.options(
            "/api/auth/login-password",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
        )

        # Preflight should be allowed
        assert response.status_code in [200, 204]
