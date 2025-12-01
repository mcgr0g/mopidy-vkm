"""Authentication flow exceptions for web integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mopidy_vkm.auth.handlers import AuthHandlers


class AuthFlowError(Exception):
    """Base exception for authentication flow control."""


class CaptchaRequiredError(AuthFlowError):
    """Raised when captcha is required during authentication."""

    def __init__(self, captcha_url: str, handlers: AuthHandlers) -> None:
        """Initialize captcha required exception.

        Args:
            captcha_url: URL to captcha image.
            handlers: AuthHandlers instance for state management.
        """
        self.captcha_url = captcha_url
        self.handlers = handlers
        super().__init__(f"Captcha required: {captcha_url}")


class TwoFactorRequiredError(AuthFlowError):
    """Raised when two-factor authentication is required."""

    def __init__(self, handlers: AuthHandlers) -> None:
        """Initialize 2FA required exception.

        Args:
            handlers: AuthHandlers instance for state management.
        """
        self.handlers = handlers
        super().__init__("Two-factor authentication required")


class AuthCancelledError(AuthFlowError):
    """Raised when authentication is cancelled by user."""


class AuthFailedError(AuthFlowError):
    """Raised when authentication fails."""

    def __init__(self, message: str) -> None:
        """Initialize auth failed exception.

        Args:
            message: Error message.
        """
        self.message = message
        super().__init__(f"Authentication failed: {message}")
