"""Authentication handlers for captcha and two-factor authentication."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

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

    def captcha_handler(self, *args: object, **kwargs: object) -> str:
        """Handle captcha request from TokenReceiver.

        Args can be positional or keyword arguments depending on the library
        implementation.
        Common patterns:
        - (captcha_sid, captcha_img)
        - (captcha_data) where captcha_data has sid and img attributes
        - captcha_sid=sid, captcha_img=img as kwargs

        Returns:
            The captcha solution (will be provided by user).
        """
        # Try to extract captcha details from various argument patterns
        captcha_sid = None
        captcha_img = None

        # Check kwargs first
        if "captcha_sid" in kwargs:
            captcha_sid = kwargs["captcha_sid"]
        if "captcha_img" in kwargs:
            captcha_img = kwargs["captcha_img"]

        # If not in kwargs, check positional args
        if captcha_sid is None and len(args) > 0:
            if isinstance(args[0], str):
                captcha_sid = args[0]
            elif hasattr(args[0], "sid") and not isinstance(args[0], str):
                # Access attribute directly
                captcha_sid = args[0].sid  # type: ignore[attr-defined]

        if captcha_img is None and len(args) > 1:
            captcha_img = args[1]
        elif (
            captcha_img is None
            and len(args) > 0
            and hasattr(args[0], "img")
            and not isinstance(args[0], str)
        ):
            # Access the attribute directly
            captcha_img = args[0].img  # type: ignore[attr-defined]

        with self._auth_lock:
            self.status = AuthStatus.CAPTCHA_REQUIRED
            self.captcha_sid = str(captcha_sid) if captcha_sid else None
            self.captcha_img = str(captcha_img) if captcha_img else None
            logger.info("Captcha required: %s", self.captcha_img)

        # Wait for the captcha solution using the persistent event
        while self.status == AuthStatus.CAPTCHA_REQUIRED:
            self._wait_event.wait(0.5)

        # Return the solution or raise an exception if authentication was cancelled
        auth_cancelled_msg = "Authentication cancelled"
        if self.status == AuthStatus.ERROR:
            raise RuntimeError(auth_cancelled_msg)

        return self._captcha_solution

    def two_factor_handler(self, *_args: object, **_kwargs: object) -> str:
        """Handle two-factor authentication request from TokenReceiver.

        Returns:
            The two-factor code (will be provided by the user).
        """
        with self._auth_lock:
            self.status = AuthStatus.TWO_FACTOR_REQUIRED
            logger.info("Two-factor authentication required")

        # Wait for the two-factor code using the persistent event
        while self.status == AuthStatus.TWO_FACTOR_REQUIRED:
            self._wait_event.wait(0.5)

        # Return the code or raise an exception if authentication was cancelled
        auth_cancelled_msg = "Authentication cancelled"
        if self.status == AuthStatus.ERROR:
            raise RuntimeError(auth_cancelled_msg)

        return self._two_factor_code

    def submit_captcha(self, captcha_solution: str) -> None:
        """Submit the captcha solution.

        Args:
            captcha_solution: The captcha solution.
        """
        with self._auth_lock:
            if self.status != AuthStatus.CAPTCHA_REQUIRED:
                logger.warning("Captcha solution submitted but not required")
                return

            self._captcha_solution = captcha_solution
            self.status = AuthStatus.PROCESSING
            # Wake up any waiting threads
            self._wait_event.set()
            logger.info("Captcha solution submitted")

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
