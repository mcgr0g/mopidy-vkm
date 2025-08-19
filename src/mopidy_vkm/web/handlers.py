"""VKM web request handlers."""

import json
import logging
from typing import Any, cast

from tornado.web import RequestHandler

from mopidy_vkm.auth import AuthStatus
from mopidy_vkm.auth.service import VKMAuthService

logger = logging.getLogger(__name__)


class BaseHandler(RequestHandler):
    """Base handler for VKM web requests."""

    def initialize(self, config: dict[str, Any], core: object) -> None:
        """Initialize the handler.

        Args:
            config: The Mopidy configuration.
            core: The Mopidy core API.
        """
        self.config = config
        self.core = core

    def get_auth_service(self) -> VKMAuthService | None:
        """Get the VKMAuthService instance from the backend.

        Returns:
            The VKMAuthService instance or None if not available.
        """
        # Import here to avoid circular imports
        from mopidy_vkm.backend import VKMBackend

        # Use cast to tell type checker that core has backends attribute
        core = cast("Any", self.core)
        for backend in core.backends.backends:
            if isinstance(backend, VKMBackend):
                return cast("VKMBackend", backend).auth_service
        return None


class MainHandler(BaseHandler):
    """Handler for the main VKM page."""

    def get(self) -> None:
        """Handle GET request for the main page."""
        # Serve the main HTML page
        self.render("vkm/index.html")


class AuthStatusHandler(BaseHandler):
    """Handler for authentication status requests."""

    def get(self) -> None:
        """Handle GET request for authentication status."""
        auth_service = self.get_auth_service()
        if not auth_service:
            self.set_status(503)  # Service Unavailable
            self.write({"status": "error", "error": "VKM backend not available"})
            return

        status = auth_service.get_status()
        self.set_header("Content-Type", "application/json")
        self.write(status)


class AuthLoginHandler(BaseHandler):
    """Handler for authentication login requests."""

    def post(self) -> None:
        """Handle POST request for authentication login."""
        auth_service = self.get_auth_service()
        if not auth_service:
            self.set_status(503)  # Service Unavailable
            self.write({"status": "error", "error": "VKM backend not available"})
            return

        try:
            data = json.loads(self.request.body)
            login = data.get("login")
            password = data.get("password")

            if not login or not password:
                self.set_status(400)  # Bad Request
                self.write(
                    {"status": "error", "error": "Login and password are required"}
                )
                return

            # Start the authentication process
            auth_service.start_auth(login, password)

            # Return the current status
            status = auth_service.get_status()
            self.set_header("Content-Type", "application/json")
            self.write(status)

        except json.JSONDecodeError:
            self.set_status(400)  # Bad Request
            self.write({"status": "error", "error": "Invalid JSON"})
        except Exception as e:
            logger.exception("Error during authentication")
            self.set_status(500)  # Internal Server Error
            self.write({"status": "error", "error": str(e)})


class AuthVerifyHandler(BaseHandler):
    """Handler for authentication verification requests."""

    def post(self) -> None:
        """Handle POST request for authentication verification."""
        auth_service = self.get_auth_service()
        if not auth_service:
            self.set_status(503)  # Service Unavailable
            self.write({"status": "error", "error": "VKM backend not available"})
            return

        try:
            data = json.loads(self.request.body)
            captcha_solution = data.get("captcha")
            two_factor_code = data.get("code")

            current_status = auth_service.get_status()
            status_value = current_status.get("status")

            if status_value == AuthStatus.CAPTCHA_REQUIRED.value and captcha_solution:
                # Submit captcha solution
                auth_service.submit_captcha(captcha_solution)
            elif (
                status_value == AuthStatus.TWO_FACTOR_REQUIRED.value and two_factor_code
            ):
                # Submit two-factor code
                auth_service.submit_two_factor(two_factor_code)
            else:
                self.set_status(400)  # Bad Request
                self.write(
                    {
                        "status": "error",
                        "error": "Invalid verification data for current status",
                    }
                )
                return

            # Return the current status
            status = auth_service.get_status()
            self.set_header("Content-Type", "application/json")
            self.write(status)

        except json.JSONDecodeError:
            self.set_status(400)  # Bad Request
            self.write({"status": "error", "error": "Invalid JSON"})
        except Exception as e:
            logger.exception("Error during verification")
            self.set_status(500)  # Internal Server Error
            self.write({"status": "error", "error": str(e)})


class AuthCancelHandler(BaseHandler):
    """Handler for authentication cancellation requests."""

    def post(self) -> None:
        """Handle POST request for authentication cancellation."""
        auth_service = self.get_auth_service()
        if not auth_service:
            self.set_status(503)  # Service Unavailable
            self.write({"status": "error", "error": "VKM backend not available"})
            return

        try:
            # Cancel the authentication process
            auth_service.cancel_auth()

            # Return the current status
            status = auth_service.get_status()
            self.set_header("Content-Type", "application/json")
            self.write(status)

        except Exception as e:
            logger.exception("Error during cancellation")
            self.set_status(500)  # Internal Server Error
            self.write({"status": "error", "error": str(e)})
