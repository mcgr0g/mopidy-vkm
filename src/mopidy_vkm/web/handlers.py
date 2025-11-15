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
        """Initialize() handler.

        Args:
            config: The Mopidy configuration.
            core: The Mopidy core API.
        """
        self.config = config
        self.core = core

        # Set template path for Tornado
        import pathlib

        current_dir = pathlib.Path(__file__).parent
        template_dir = str(current_dir / "templates")
        self.application.settings.setdefault("template_path", template_dir)

    def get_auth_service(self) -> VKMAuthService | None:
        """Get the VKMAuthService instance from the backend.

        Returns:
            The VKMAuthService instance or None if not available.
        """
        # Import here to avoid circular imports
        from mopidy_vkm.backend import VKMBackend

        # self.core is a Pykka proxy - need to access backends correctly
        core = cast("Any", self.core)

        # Try different approaches to access backends
        try:
            # First try: core.backends.backends.get()
            backends_proxy = core.backends.backends.get()
            logger.debug("Found %d backends using .get() method", len(backends_proxy))
            for i, backend in enumerate(backends_proxy):
                logger.debug(
                    "Backend %d: %s (%s)",
                    i,
                    type(backend).__name__,
                    getattr(backend, "uri_schemes", []),
                )
                if isinstance(backend, VKMBackend):
                    return backend.auth_service
        except Exception as e1:
            logger.debug("First approach failed: %s", e1)
            try:
                # Second try: core.backends.get() - Backends object itself
                backends_obj = core.backends.get()
                logger.debug("Found backends object: %s", type(backends_obj).__name__)
                # Backends is iterable and contains the backend instances
                for i, backend_proxy in enumerate(backends_obj):
                    # Try to identify the backend by checking uri_schemes through proxy
                    try:
                        uri_schemes_future = cast("Any", backend_proxy).uri_schemes
                        logger.debug(
                            "Backend %d: %s (schemes future: %s)",
                            i,
                            type(backend_proxy).__name__,
                            type(uri_schemes_future).__name__,
                        )

                        # uri_schemes is also a Future - get its value
                        uri_schemes = uri_schemes_future.get()
                        logger.debug(
                            "Backend %d: %s (schemes: %s)",
                            i,
                            type(backend_proxy).__name__,
                            uri_schemes,
                        )

                        # VKM backend should have 'vkm' in its uri_schemes
                        if (
                            hasattr(uri_schemes, "__contains__")
                            and "vkm" in uri_schemes
                        ):
                            logger.debug(
                                "Found VKM backend at index %d by uri_schemes", i
                            )
                            # Try to access auth_service through proxy
                            try:
                                auth_service_future = cast(
                                    "Any", backend_proxy
                                ).auth_service
                                logger.debug(
                                    "Auth service future type: %s",
                                    type(auth_service_future).__name__,
                                )
                                if hasattr(auth_service_future, "get"):
                                    auth_service = auth_service_future.get()
                                    logger.debug(
                                        "Got auth_service: %s",
                                        type(auth_service).__name__,
                                    )
                                    return auth_service
                                else:
                                    return auth_service_future
                            except Exception as e:
                                logger.debug(
                                    "Failed to access auth_service through proxy: %s", e
                                )
                                # Try getting the real backend
                                try:
                                    backend = backend_proxy.get()
                                    return backend.auth_service
                                except Exception as e2:
                                    logger.debug("Failed to get real backend: %s", e2)
                    except Exception as e:
                        logger.debug(
                            "Backend %d: %s (failed to get schemes: %s)",
                            i,
                            type(backend_proxy).__name__,
                            e,
                        )
            except Exception as e2:
                logger.debug("Second approach failed: %s", e2)
                try:
                    # Third try: core.backends.backends (direct proxy access)
                    backends_list = core.backends.backends
                    logger.debug(
                        "Found %d backends using direct proxy access",
                        len(backends_list),
                    )
                    for i, backend_proxy in enumerate(backends_list):
                        backend_name = getattr(backend_proxy, "__class__", {}).get(
                            "__name__", "Unknown"
                        )
                        logger.debug("Backend %d proxy: %s", i, backend_name)
                        if (
                            hasattr(backend_proxy, "__class__")
                            and backend_proxy.__class__.__name__ == "VKMBackend"
                        ):
                            # Access auth_service through the proxy
                            return cast("Any", backend_proxy).auth_service
                except Exception as e3:
                    logger.debug("Third approach failed: %s", e3)
                    logger.exception("All approaches failed to access VKM backend")
                    return None

        logger.warning("VKMBackend not found in any available backends")
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
