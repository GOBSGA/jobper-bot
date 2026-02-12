"""
Tests for authentication service.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from services.auth import (
    register_with_password,
    login_with_password,
    _hash_password,
    _verify_password,
)


class TestPasswordAuth:
    """Test password authentication functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "secure_password_123"
        hashed = _hash_password(password)

        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != password  # Should be hashed, not plain text

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "secure_password_123"
        hashed = _hash_password(password)

        assert _verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "secure_password_123"
        wrong_password = "wrong_password"
        hashed = _hash_password(password)

        assert _verify_password(wrong_password, hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash."""
        password = "secure_password_123"
        invalid_hash = "not_a_valid_hash"

        assert _verify_password(password, invalid_hash) is False

    @patch('services.auth.UnitOfWork')
    @patch('services.auth.task_send_email')
    def test_register_with_password_success(self, mock_email, mock_uow):
        """Test successful registration with password."""
        # Mock UnitOfWork
        mock_context = Mock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.users.get_by_email.return_value = None  # User doesn't exist

        email = "test@example.com"
        password = "secure_password_123"

        result = register_with_password(email, password)

        # Should return access_token and user data
        assert "access_token" in result
        assert "refresh_token" in result
        assert "user" in result
        assert result.get("is_new") is True

        # Should create user
        mock_context.users.create.assert_called_once()

        # Should commit transaction
        mock_context.commit.assert_called_once()

    @patch('services.auth.UnitOfWork')
    def test_register_with_password_weak_password(self, mock_uow):
        """Test registration with weak password."""
        email = "test@example.com"
        password = "123"  # Too short

        result = register_with_password(email, password)

        assert "error" in result
        assert "al menos 6 caracteres" in result["error"]

    @patch('services.auth.UnitOfWork')
    def test_register_with_password_existing_user(self, mock_uow):
        """Test registration when user already exists."""
        # Mock UnitOfWork
        mock_context = Mock()
        mock_uow.return_value.__enter__.return_value = mock_context

        # Mock existing user
        existing_user = Mock()
        existing_user.email = "test@example.com"
        mock_context.users.get_by_email.return_value = existing_user

        email = "test@example.com"
        password = "secure_password_123"

        result = register_with_password(email, password)

        assert "error" in result
        assert "Ya existe" in result["error"]

    @patch('services.auth.UnitOfWork')
    def test_login_with_password_success(self, mock_uow):
        """Test successful login with password."""
        # Mock UnitOfWork
        mock_context = Mock()
        mock_uow.return_value.__enter__.return_value = mock_context

        # Mock user with password
        password = "secure_password_123"
        hashed = _hash_password(password)

        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.password_hash = hashed
        mock_user.plan = "trial"
        mock_user.is_admin = False

        mock_context.users.get_by_email.return_value = mock_user

        result = login_with_password("test@example.com", password)

        assert "access_token" in result
        assert "refresh_token" in result
        assert "user" in result

    @patch('services.auth.UnitOfWork')
    def test_login_with_password_wrong_password(self, mock_uow):
        """Test login with wrong password."""
        # Mock UnitOfWork
        mock_context = Mock()
        mock_uow.return_value.__enter__.return_value = mock_context

        # Mock user with password
        correct_password = "secure_password_123"
        wrong_password = "wrong_password"
        hashed = _hash_password(correct_password)

        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.password_hash = hashed

        mock_context.users.get_by_email.return_value = mock_user

        result = login_with_password("test@example.com", wrong_password)

        assert "error" in result
        assert "incorrectos" in result["error"]

    @patch('services.auth.UnitOfWork')
    def test_login_with_password_user_not_found(self, mock_uow):
        """Test login with non-existent user."""
        # Mock UnitOfWork
        mock_context = Mock()
        mock_uow.return_value.__enter__.return_value = mock_context
        mock_context.users.get_by_email.return_value = None

        result = login_with_password("nonexistent@example.com", "password")

        assert "error" in result
        assert "incorrectos" in result["error"]

    @patch('services.auth.UnitOfWork')
    def test_login_with_password_no_password_hash(self, mock_uow):
        """Test login when user has no password (magic link only)."""
        # Mock UnitOfWork
        mock_context = Mock()
        mock_uow.return_value.__enter__.return_value = mock_context

        # Mock user without password
        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.password_hash = None  # No password set

        mock_context.users.get_by_email.return_value = mock_user

        result = login_with_password("test@example.com", "any_password")

        assert "error" in result
        assert "magic link" in result["error"]
