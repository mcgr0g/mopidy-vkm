"""Tests for the VKM web interface."""

import json
import unittest
from unittest.mock import MagicMock, patch

from tornado.testing import AsyncHTTPTestCase

from mopidy_vkm.auth import AuthStatus
from mopidy_vkm.auth.service import VKMAuthService
from mopidy_vkm.backend import VKMBackend
from mopidy_vkm.web.app import create_web_app
from mopidy_vkm.web.handlers import (
    MainHandler,
)


class MockBackend(VKMBackend):
    """Mock backend for testing."""

    def __init__(self) -> None:
        """Initialize the mock backend."""
        # Skip the parent class initialization
        self.auth_service = MagicMock(spec=VKMAuthService)
        self.auth_service.get_status.return_value = {"status": "success"}


class MockCore:
    """Mock core for testing."""

    def __init__(self) -> None:
        """Initialize the mock core."""
        self.backends = MagicMock()
        self.backends.backends = [MockBackend()]


class TestWebHandlers(AsyncHTTPTestCase):
    """Test the web handlers."""

    def get_app(self) -> object:
        """Get the application for testing."""
        self.config = {"debug": True}
        self.core = MockCore()
        return create_web_app(self.config, self.core)

    def test_main_handler(self) -> None:
        """Test the main handler."""
        # Patch the render method to avoid template rendering
        with patch.object(MainHandler, "render") as mock_render:
            # Make the request
            self.fetch("/vkm")

            # Check that the render method was called
            mock_render.assert_called_once_with("vkm/index.html")

    def test_status_handler(self) -> None:
        """Test the status handler."""
        # Set up the mock auth service
        auth_service = self.core.backends.backends[0].auth_service
        auth_service.get_status.return_value = {
            "status": "success",
            "user_id": "test_user_id",
        }

        # Make the request
        response = self.fetch("/vkm/auth/status")

        # Check the response
        assert response.code == 200
        data = json.loads(response.body)
        assert data["status"] == "success"
        assert data["user_id"] == "test_user_id"

    def test_status_handler_no_backend(self) -> None:
        """Test the status handler with no backend."""
        # Set up the mock backends with no VKM backend
        self.core.backends.backends = []

        # Make the request
        response = self.fetch("/vkm/auth/status")

        # Check the response
        assert response.code == 503
        data = json.loads(response.body)
        assert data["status"] == "error"
        assert data["error"] == "VKM backend not available"

    def test_login_handler(self) -> None:
        """Test the login handler."""
        # Set up the mock auth service
        auth_service = self.core.backends.backends[0].auth_service
        auth_service.get_status.return_value = {"status": "processing"}

        # Make the request
        response = self.fetch(
            "/vkm/auth/login",
            method="POST",
            body=json.dumps({"login": "test_login", "password": "test_password"}),
        )

        # Check the response
        assert response.code == 200
        data = json.loads(response.body)
        assert data["status"] == "processing"

        # Check that the auth service was called
        auth_service.start_auth.assert_called_once_with("test_login", "test_password")

    def test_login_handler_missing_fields(self) -> None:
        """Test the login handler with missing fields."""
        # Make the request with missing password
        response = self.fetch(
            "/vkm/auth/login",
            method="POST",
            body=json.dumps({"login": "test_login"}),
        )

        # Check the response
        assert response.code == 400
        data = json.loads(response.body)
        assert data["status"] == "error"
        assert data["error"] == "Login and password are required"

    def test_verify_handler_captcha(self) -> None:
        """Test the verify handler with captcha."""
        # Set up the mock auth service
        auth_service = self.core.backends.backends[0].auth_service
        auth_service.get_status.return_value = {
            "status": AuthStatus.CAPTCHA_REQUIRED.value
        }

        # Make the request
        response = self.fetch(
            "/vkm/auth/verify",
            method="POST",
            body=json.dumps({"captcha": "test_captcha"}),
        )

        # Check the response
        assert response.code == 200

        # Check that the auth service was called
        auth_service.submit_captcha.assert_called_once_with("test_captcha")

    def test_verify_handler_two_factor(self) -> None:
        """Test the verify handler with two-factor."""
        # Set up the mock auth service
        auth_service = self.core.backends.backends[0].auth_service
        auth_service.get_status.return_value = {
            "status": AuthStatus.TWO_FACTOR_REQUIRED.value
        }

        # Make the request
        response = self.fetch(
            "/vkm/auth/verify",
            method="POST",
            body=json.dumps({"code": "test_code"}),
        )

        # Check the response
        assert response.code == 200

        # Check that the auth service was called
        auth_service.submit_two_factor.assert_called_once_with("test_code")

    def test_verify_handler_invalid(self) -> None:
        """Test the verify handler with invalid data."""
        # Set up the mock auth service
        auth_service = self.core.backends.backends[0].auth_service
        auth_service.get_status.return_value = {"status": "success"}

        # Make the request
        response = self.fetch(
            "/vkm/auth/verify",
            method="POST",
            body=json.dumps({"captcha": "test_captcha"}),
        )

        # Check the response
        assert response.code == 400
        data = json.loads(response.body)
        assert data["status"] == "error"

    def test_cancel_handler(self) -> None:
        """Test the cancel handler."""
        # Set up the mock auth service
        auth_service = self.core.backends.backends[0].auth_service
        auth_service.get_status.return_value = {"status": "error", "error": "Cancelled"}

        # Make the request
        response = self.fetch(
            "/vkm/auth/cancel",
            method="POST",
            body="",
        )

        # Check the response
        assert response.code == 200
        data = json.loads(response.body)
        assert data["status"] == "error"
        assert data["error"] == "Cancelled"

        # Check that the auth service was called
        auth_service.cancel_auth.assert_called_once()


if __name__ == "__main__":
    unittest.main()
