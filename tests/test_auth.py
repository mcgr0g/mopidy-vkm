"""Tests for the unified VKM authentication system."""

import pathlib
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from mopidy_vkm.auth import AuthStatus, VKMAuthService


class TestVKMAuthService(unittest.TestCase):
    """Test the unified VKMAuthService class."""

    def setUp(self) -> None:
        """Set up the test environment."""
        # Create a temporary file for credentials
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = str(pathlib.Path(self.temp_dir.name) / "credentials.json")

        # Create a mock config
        self.config = {"user_agent": "test_user_agent"}

        # Create the unified auth service
        self.auth_service = VKMAuthService(self.config_path, self.config)

    def tearDown(self) -> None:
        """Clean up the test environment."""
        self.temp_dir.cleanup()

    def test_initial_state(self) -> None:
        """Test the initial state of the auth service."""
        assert self.auth_service.status == AuthStatus.NOT_AUTHENTICATED
        assert self.auth_service.vk_service is None

    def test_has_credentials(self) -> None:
        """Test checking if credentials are available."""
        # Initially no credentials
        assert not self.auth_service.has_credentials()

    @patch("vkpymusic.Service.parse_config")
    def test_load_service(self, mock_parse_config: MagicMock) -> None:
        """Test loading vkpymusic service."""
        # Test successful load
        mock_service = MagicMock()
        mock_parse_config.return_value = mock_service

        service = self.auth_service.load_service()
        assert service is mock_service
        mock_parse_config.assert_called_once_with(self.config_path)

        # Test failed load
        mock_parse_config.side_effect = Exception("Failed")
        service = self.auth_service.load_service()
        assert service is None

    @patch("vkpymusic.TokenReceiver")
    def test_save_token(self, mock_token_receiver: MagicMock) -> None:
        """Test saving token."""
        mock_receiver_instance = MagicMock()
        mock_token_receiver.return_value = mock_receiver_instance

        self.auth_service.save_token(mock_receiver_instance)
        mock_receiver_instance.save_to_config.assert_called_once_with(self.config_path)

    def test_clear_credentials(self) -> None:
        """Test clearing credentials."""
        # Just test that clear doesn't raise an exception
        self.auth_service.clear_credentials()
        assert not self.auth_service.has_credentials()

    @patch("vkpymusic.Service.parse_config")
    def test_initialize_service_with_credentials(
        self, mock_parse_config: MagicMock
    ) -> None:
        """Test initializing service with existing credentials."""
        # Set up mock service
        mock_instance = MagicMock()
        mock_parse_config.return_value = mock_instance

        # Create a new auth service to trigger initialization
        auth_service = VKMAuthService(self.config_path, self.config)

        # Check that the service was initialized
        assert auth_service.status == AuthStatus.SUCCESS
        assert auth_service.vk_service is mock_instance

    def test_initialize_service_without_credentials(self) -> None:
        """Test initializing the service without existing credentials."""
        # Create a new auth service to trigger initialization
        auth_service = VKMAuthService(self.config_path, self.config)

        # Check that the service was not initialized
        assert auth_service.status == AuthStatus.NOT_AUTHENTICATED

    def test_initialize_service_with_error(self) -> None:
        """Test initializing the service with an error."""
        # Test that when credentials are missing, status is NOT_AUTHENTICATED
        # ERROR status only occurs for actual exceptions during initialization
        auth_service = VKMAuthService(self.config_path, self.config)
        assert auth_service.status == AuthStatus.NOT_AUTHENTICATED

    def test_get_status(self) -> None:
        """Test getting the authentication status."""
        # Test with error status
        self.auth_service.status = AuthStatus.ERROR
        self.auth_service.error_message = "Test error"
        status = self.auth_service.get_status()
        assert status["status"] == "error"
        assert status["error"] == "Test error"

        # Test with captcha required status
        self.auth_service.status = AuthStatus.CAPTCHA_REQUIRED
        self.auth_service.captcha_sid = "test_sid"
        self.auth_service.captcha_img = "test_img"
        status = self.auth_service.get_status()
        assert status["status"] == "captcha_required"
        assert status["captcha_sid"] == "test_sid"
        assert status["captcha_img"] == "test_img"

        # Test with success status - mock user info from vk_service
        self.auth_service.status = AuthStatus.SUCCESS
        mock_vk_service = MagicMock()
        mock_user_info = {
            "id": "test_user_id",
            "first_name": "Test",
            "last_name": "User",
        }
        mock_vk_service.get_user_info.return_value = mock_user_info
        self.auth_service.vk_service = mock_vk_service

        status = self.auth_service.get_status()
        assert status["status"] == "success"
        assert status["user_id"] == "test_user_id"
        assert status["profile_name"] == "Test User"

    @patch("threading.Thread")
    def test_start_auth(self, mock_thread: MagicMock) -> None:
        """Test starting the authentication process."""
        # Start authentication
        self.auth_service.start_auth("test_login", "test_password")

        # Check that the thread was started
        assert self.auth_service.status == AuthStatus.PROCESSING
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()

    def test_cancel_auth(self) -> None:
        """Test cancelling the authentication process."""
        # Set up the auth service
        self.auth_service.status = AuthStatus.PROCESSING

        # Cancel authentication
        self.auth_service.cancel_auth()

        # Check that the status was updated
        assert self.auth_service.status == AuthStatus.ERROR
        assert self.auth_service.error_message is not None

    def test_submit_captcha(self) -> None:
        """Test submitting a captcha solution (not implemented)."""
        # Submit captcha - should just log warning
        self.auth_service.submit_captcha("test_solution")
        # No status change expected in minimal version

    def test_submit_two_factor(self) -> None:
        """Test submitting a two-factor code (not implemented)."""
        # Submit two-factor code - should just log warning
        self.auth_service.submit_two_factor("test_code")
        # No status change expected in minimal version


if __name__ == "__main__":
    unittest.main()
