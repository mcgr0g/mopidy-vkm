"""Tests for multi-step authentication flow."""

import unittest
from unittest.mock import Mock, patch

from mopidy_vkm.auth.exceptions import (
    AuthCancelledError,
    AuthFailedError,
    CaptchaRequiredError,
    TwoFactorRequiredError,
)
from mopidy_vkm.auth.handlers import AuthHandlers
from mopidy_vkm.auth.service import VKMAuthService
from mopidy_vkm.auth.status import AuthStatus


class TestMultiStepAuth(unittest.TestCase):
    """Test multi-step authentication flow."""

    def setUp(self) -> None:
        """Set up test environment."""
        import tempfile

        # Create a temporary file for test config
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            self.config_path = temp_file.name

        self.config = {}
        self.service = VKMAuthService(self.config_path, self.config)

    def tearDown(self) -> None:
        """Clean up test environment."""
        from pathlib import Path

        if hasattr(self, "config_path") and Path(self.config_path).exists():
            Path(self.config_path).unlink()

    def test_captcha_flow_exception_handling(self) -> None:
        """Test captcha required exception flow."""
        with patch(
            "mopidy_vkm.auth.handlers.get_global_auth_handlers"
        ) as mock_get_handlers:
            mock_handlers = Mock(spec=AuthHandlers)
            mock_handlers.captcha_handler = Mock()
            mock_handlers.two_factor_handler = Mock()
            mock_get_handlers.return_value = mock_handlers

            with patch("vkpymusic.TokenReceiver") as mock_token_receiver:
                mock_receiver = Mock()
                mock_token_receiver.return_value = mock_receiver
                mock_receiver.auth.side_effect = CaptchaRequiredError(
                    captcha_url="https://captcha.example.com/image.png", handlers=Mock()
                )

                # Start authentication
                self.service.start_auth("test@example.com", "password")

                # Wait for thread to complete
                if self.service._auth_thread:
                    self.service._auth_thread.join(timeout=1.0)

                # Verify status is CAPTCHA_REQUIRED
                assert self.service.status == AuthStatus.CAPTCHA_REQUIRED
                assert (
                    self.service.captcha_img == "https://captcha.example.com/image.png"
                )

    def test_two_factor_flow_exception_handling(self) -> None:
        """Test two-factor authentication required exception flow."""
        with patch(
            "mopidy_vkm.auth.handlers.get_global_auth_handlers"
        ) as mock_get_handlers:
            mock_handlers = Mock(spec=AuthHandlers)
            mock_handlers.captcha_handler = Mock()
            mock_handlers.two_factor_handler = Mock()
            mock_get_handlers.return_value = mock_handlers

            with patch("vkpymusic.TokenReceiver") as mock_token_receiver:
                mock_receiver = Mock()
                mock_token_receiver.return_value = mock_receiver
                mock_receiver.auth.side_effect = TwoFactorRequiredError(Mock())

                # Start authentication
                self.service.start_auth("test@example.com", "password")

                # Wait for thread to complete
                if self.service._auth_thread:
                    self.service._auth_thread.join(timeout=1.0)

                # Verify status is TWO_FACTOR_REQUIRED
                assert self.service.status == AuthStatus.TWO_FACTOR_REQUIRED

    def test_auth_cancelled_exception_handling(self) -> None:
        """Test authentication cancelled exception flow."""
        with patch(
            "mopidy_vkm.auth.handlers.get_global_auth_handlers"
        ) as mock_get_handlers:
            mock_handlers = Mock(spec=AuthHandlers)
            mock_handlers.captcha_handler = Mock()
            mock_handlers.two_factor_handler = Mock()
            mock_get_handlers.return_value = mock_handlers

            with patch("vkpymusic.TokenReceiver") as mock_token_receiver:
                mock_receiver = Mock()
                mock_token_receiver.return_value = mock_receiver
                mock_receiver.auth.side_effect = AuthCancelledError()

                # Start authentication
                self.service.start_auth("test@example.com", "password")

                # Wait for thread to complete
                if self.service._auth_thread:
                    self.service._auth_thread.join(timeout=1.0)

                # Verify status is ERROR with cancelled message
                assert self.service.status == AuthStatus.ERROR
                assert self.service.error_message == "Authentication cancelled by user"

    def test_auth_failed_exception_handling(self) -> None:
        """Test authentication failed exception flow."""
        with patch(
            "mopidy_vkm.auth.handlers.get_global_auth_handlers"
        ) as mock_get_handlers:
            mock_handlers = Mock(spec=AuthHandlers)
            mock_handlers.captcha_handler = Mock()
            mock_handlers.two_factor_handler = Mock()
            mock_get_handlers.return_value = mock_handlers

            with patch("vkpymusic.TokenReceiver") as mock_token_receiver:
                mock_receiver = Mock()
                mock_token_receiver.return_value = mock_receiver
                mock_receiver.auth.side_effect = AuthFailedError("Invalid credentials")

                # Start authentication
                self.service.start_auth("test@example.com", "password")

                # Wait for thread to complete
                if self.service._auth_thread:
                    self.service._auth_thread.join(timeout=1.0)

                # Verify status is ERROR with specific message
                assert self.service.status == AuthStatus.ERROR
                assert self.service.error_message == "Invalid credentials"

    def test_successful_auth_flow(self) -> None:
        """Test successful authentication flow."""
        with patch(
            "mopidy_vkm.auth.handlers.get_global_auth_handlers"
        ) as mock_get_handlers:
            mock_handlers = Mock(spec=AuthHandlers)
            mock_handlers.captcha_handler = Mock()
            mock_handlers.two_factor_handler = Mock()
            mock_get_handlers.return_value = mock_handlers

            with patch("vkpymusic.TokenReceiver") as mock_token_receiver:
                mock_receiver = Mock()
                mock_token_receiver.return_value = mock_receiver
                mock_receiver.auth.return_value = True

                with patch.object(
                    self.service, "save_token"
                ) as mock_save, patch.object(self.service, "load_service") as mock_load:
                    mock_load.return_value = Mock()

                    # Start authentication
                    self.service.start_auth("test@example.com", "password")

                    # Wait for thread to complete
                    if self.service._auth_thread:
                        self.service._auth_thread.join(timeout=1.0)

                    # Verify status is SUCCESS
                    assert self.service.status == AuthStatus.SUCCESS
                    mock_save.assert_called_once_with(mock_receiver)

    def test_submit_captcha_with_handlers(self) -> None:
        """Test captcha submission through global handlers."""
        # Create real handlers and set status properly
        real_handlers = AuthHandlers()

        # Mock the call inside service.submit_captcha
        with patch(
            "mopidy_vkm.auth.service.get_global_auth_handlers",
            return_value=real_handlers,
        ):
            # Set status through lock to simulate real scenario
            with real_handlers._auth_lock:
                real_handlers.status = AuthStatus.CAPTCHA_REQUIRED

            # Submit captcha
            self.service.submit_captcha("test123")

            # Verify internal state was updated
            assert real_handlers._captcha_solution == "test123"

    def test_submit_two_factor_with_handlers(self) -> None:
        """Test two-factor code submission through global handlers."""
        # Create real handlers and set status properly
        real_handlers = AuthHandlers()

        # Mock the call inside service.submit_two_factor
        with patch(
            "mopidy_vkm.auth.service.get_global_auth_handlers",
            return_value=real_handlers,
        ):
            # Set status through lock to simulate real scenario
            with real_handlers._auth_lock:
                real_handlers.status = AuthStatus.TWO_FACTOR_REQUIRED

            # Submit two-factor code
            self.service.submit_two_factor("123456")

            # Verify internal state was updated
            assert real_handlers._two_factor_code == "123456"

    def test_status_includes_captcha_info(self) -> None:
        """Test that status includes captcha information when required."""
        self.service.status = AuthStatus.CAPTCHA_REQUIRED
        self.service.captcha_img = "https://captcha.example.com/test.png"

        status = self.service.get_status()

        assert status["status"] == "captcha_required"
        assert status["captcha_img"] == "https://captcha.example.com/test.png"

    def test_status_includes_error_info(self) -> None:
        """Test that status includes error information when error occurs."""
        self.service.status = AuthStatus.ERROR
        self.service.error_message = "Test error message"

        status = self.service.get_status()

        assert status["status"] == "error"
        assert status["error"] == "Test error message"


if __name__ == "__main__":
    unittest.main()
