"""Authentication handlers for captcha and two-factor authentication."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

from mopidy_vkm.auth.exceptions import (
    CaptchaRequiredError,
    TwoFactorRequiredError,
)
from mopidy_vkm.auth.status import AuthStatus

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class AuthHandlers:
    """Handlers for authentication challenges like captcha and 2FA."""

    def __init__(self) -> None:
        """Initialize the authentication handlers."""
        self.status = AuthStatus.ERROR
        self.error_message: str | None = None
        self.captcha_sid: str | None = None
        self.captcha_img: str | None = None
        self._captcha_solution: str = ""
        self._two_factor_code: str = ""
        self._auth_lock = threading.Lock()
        self._wait_event = threading.Event()  # Persistent event for waiting

    def captcha_handler(self, captcha_url: str) -> str:
        """Handle captcha request from TokenReceiver using exception flow.

        Args:
            captcha_url: URL to captcha image from vkpymusic.

        Returns:
            The captcha solution (will be provided by user).

        Raises:
            CaptchaRequiredError: Always raised to redirect to web UI.
        """
        with self._auth_lock:
            self.status = AuthStatus.CAPTCHA_REQUIRED
            self.captcha_img = captcha_url
            logger.info("Captcha required: %s", captcha_url)

        # Always raise exception to redirect to web UI
        raise CaptchaRequiredError(captcha_url, self)

    def two_factor_handler(self) -> str:
        """Handle two-factor authentication request from TokenReceiver using exception
        flow.

        Returns:
            The two-factor code (will be provided by user).

        Raises:
            TwoFactorRequiredError: Always raised to redirect to web UI.
        """
        with self._auth_lock:
            self.status = AuthStatus.TWO_FACTOR_REQUIRED
            logger.info("Two-factor authentication required")

        # Always raise exception to redirect to web UI
        raise TwoFactorRequiredError(self)

    def _set_challenge_response(self, response_value: str, challenge_type: str) -> None:
        """Set challenge response and update status.

        Args:
            response_value: The captcha solution or 2FA code.
            challenge_type: Type of challenge ('captcha' or '2fa').
        """
        with self._auth_lock:
            if (
                challenge_type == "captcha"
                and self.status != AuthStatus.CAPTCHA_REQUIRED
            ):
                logger.warning("Captcha solution submitted but not required")
                return
            elif (
                challenge_type == "2fa"
                and self.status != AuthStatus.TWO_FACTOR_REQUIRED
            ):
                logger.warning("Two-factor code submitted but not required")
                return

            if challenge_type == "captcha":
                self._captcha_solution = response_value
            else:  # 2fa
                self._two_factor_code = response_value

            self.status = AuthStatus.PROCESSING
            # Wake up any waiting threads
            self._wait_event.set()
            logger.info("%s submitted successfully", challenge_type.title())

    def submit_captcha(self, captcha_solution: str) -> None:
        """Submit the captcha solution.

        Args:
            captcha_solution: The captcha solution.
        """
        self._set_challenge_response(captcha_solution, "captcha")

    def submit_two_factor(self, two_factor_code: str) -> None:
        """Submit the two-factor authentication code.

        Args:
            two_factor_code: The two-factor code.
        """
        with self._auth_lock:
            if self.status != AuthStatus.TWO_FACTOR_REQUIRED:
                logger.warning("Two-factor code submitted but not required")
                return

            self._two_factor_code = two_factor_code
            self.status = AuthStatus.PROCESSING
            # Wake up any waiting threads
            self._wait_event.set()
            logger.info("Two-factor code submitted")

    def cancel_auth(self) -> None:
        """Cancel the authentication process."""
        with self._auth_lock:
            if self.status in (
                AuthStatus.CAPTCHA_REQUIRED,
                AuthStatus.TWO_FACTOR_REQUIRED,
                AuthStatus.PROCESSING,
            ):
                self.status = AuthStatus.ERROR
                self.error_message = "Authentication cancelled by user"
                # Wake up any waiting threads
                self._wait_event.set()
                logger.info("Authentication cancelled by user")

    def resume_after_captcha(self) -> str:
        """Resume authentication after captcha has been submitted.

        Returns:
            The captcha solution.
        """
        return self._captcha_solution

    def resume_after_two_factor(self) -> str:
        """Resume authentication after 2FA has been submitted.

        Returns:
            The two-factor code.
        """
        return self._two_factor_code


# Global instance for web integration
_global_auth_handlers: AuthHandlers | None = None


def get_global_auth_handlers() -> AuthHandlers:
    """Get the global AuthHandlers instance.

    Returns:
        The global AuthHandlers instance.
    """
    global _global_auth_handlers
    if _global_auth_handlers is None:
        _global_auth_handlers = AuthHandlers()
    return _global_auth_handlers


def reset_global_auth_handlers() -> None:
    """Reset the global AuthHandlers instance."""
    global _global_auth_handlers
    _global_auth_handlers = None


def get_handler_methods(
    handlers: AuthHandlers,
) -> tuple[Callable[..., str], Callable[..., str]]:
    """Get handler methods from the AuthHandlers instance.

    Args:
        handlers: The AuthHandlers instance.

    Returns:
        A tuple of (captcha_handler, two_factor_handler).
    """
    return handlers.captcha_handler, handlers.two_factor_handler
