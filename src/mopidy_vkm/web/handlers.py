"""VKM web request handlers."""

import json
import logging
import re
from typing import Any, cast

import tornado.web
from tornado.web import RequestHandler

from mopidy_vkm.auth import AuthStatus
from mopidy_vkm.auth.service import VKMAuthService

logger = logging.getLogger(__name__)

# Security patterns for input validation
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_PATTERN = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")
MIN_PASSWORD_LENGTH = 4


def validate_login_password(login: str, password: str) -> tuple[bool, str]:
    """Validate login and password for security."""
    if not login or not login.strip():
        return False, "Login is required"

    if not password or len(password) < 1:
        return False, "Password is required"

    login = login.strip()

    # Check if login is email or phone format
    is_email = bool(EMAIL_PATTERN.match(login))
    is_phone = bool(PHONE_PATTERN.match(login))

    if not (is_email or is_phone):
        return False, "Login must be valid email or phone number"

    # Password length validation (basic security)
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, "Password is too short"

    return True, ""


def validate_captcha_solution(captcha_solution: str) -> tuple[bool, str]:
    """Validate captcha solution for security."""
    if not captcha_solution or not captcha_solution.strip():
        return False, "Captcha solution is required"

    captcha_solution = captcha_solution.strip()
    if len(captcha_solution) < 4:
        return False, "Captcha solution is too short"
    if len(captcha_solution) > 10:
        return False, "Captcha solution is too long"

    return True, ""


def validate_two_factor_code(two_factor_code: str) -> tuple[bool, str]:
    """Validate two-factor authentication code for security."""
    if not two_factor_code or not two_factor_code.strip():
        return False, "Two-factor code is required"

    two_factor_code = two_factor_code.strip()
    if len(two_factor_code) < 4:
        return False, "Two-factor code is too short"
    if len(two_factor_code) > 10:
        return False, "Two-factor code is too long"
    if not two_factor_code.isdigit():
        return False, "Two-factor code must contain only digits"

    return True, ""


class BaseHandler(RequestHandler):
    """Base handler for VKM web requests."""

    def initialize(self, config: dict[str, Any], core: object) -> None:
        """Initialize handler."""
        self.config = config
        self.core = core
        self.logger = logging.getLogger(self.__class__.__name__)

        # Set template path for Tornado
        import pathlib

        current_dir = pathlib.Path(__file__).parent
        template_dir = str(current_dir / "templates")
        self.application.settings.setdefault("template_path", template_dir)

    def get_auth_service(self) -> VKMAuthService | None:
        """Get VKMAuthService instance from backend using Mopidy pattern."""
        from mopidy_vkm.backend import VKMBackend

        # Official Mopidy pattern: access backends through core
        core = cast("Any", self.core)
        try:
            backends_attr = getattr(core, "backends", None)

            if backends_attr and hasattr(backends_attr, "get"):
                backends = backends_attr.get()

                for backend_proxy in backends:
                    try:
                        # Try to access the actor directly through proxy
                        if hasattr(backend_proxy, "_actor"):
                            actor_ref = backend_proxy._actor

                            # Try to get the actual class in different ways
                            try:
                                # Method 1: Check if class name matches
                                if actor_ref.__class__.__name__ == "VKMBackend":
                                    auth_service = backend_proxy.auth_service
                                    # Pykka proxy returns a Future, we need to .get() the actual object
                                    if hasattr(auth_service, "get"):
                                        auth_service = auth_service.get()
                                    return auth_service

                                # Method 2: Check uri_schemes
                                if hasattr(actor_ref, "uri_schemes"):
                                    uri_schemes = actor_ref.uri_schemes
                                    if "vkm" in uri_schemes:
                                        auth_service = backend_proxy.auth_service
                                        # Pykka proxy returns a Future, we need to .get() the actual object
                                        if hasattr(auth_service, "get"):
                                            auth_service = auth_service.get()
                                        return auth_service
                            except Exception:
                                # Continue to next backend if this one fails
                                continue

                            # Method 3: Check if actor_ref has actor_class
                            if hasattr(actor_ref, "actor_class"):
                                actor_class = actor_ref.actor_class

                                if actor_class is VKMBackend:
                                    # Access auth_service through proxy attribute access
                                    auth_service = backend_proxy.auth_service
                                    return auth_service
                        else:
                            # Try direct attribute access - Pykka proxies should forward attribute access
                            try:
                                # Check if this is VKMBackend by checking uri_schemes
                                uri_schemes = backend_proxy.uri_schemes

                                if "vkm" in uri_schemes:
                                    auth_service = backend_proxy.auth_service
                                    return auth_service
                            except Exception:
                                # Continue to next backend if direct access fails
                                continue

                    except Exception:
                        # Continue to next backend if this one fails
                        continue
            else:
                self.logger.warning("No backends.get() method available")
        except Exception as e:
            self.logger.warning(f"Failed to access backends: {e}")

        self.logger.warning("VKMBackend not found in available backends")
        return None

    def _parse_json_body(self) -> dict[str, Any]:
        """Parse JSON request body with UTF-8 encoding."""
        try:
            if isinstance(self.request.body, bytes):
                body_str = self.request.body.decode("utf-8")
            else:
                body_str = self.request.body
            return json.loads(body_str)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid JSON data: {e}") from e

    def _write_error_response(self, status_code: int, error_message: str) -> None:
        """Write standardized error response."""
        self.set_status(status_code)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write({"status": "error", "error": error_message})

    def _write_status_response(self, status: dict[str, Any]) -> None:
        """Write standardized status response."""
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(status)

    def _validate_auth_service(self) -> VKMAuthService:
        """Validate auth service is available."""
        auth_service = self.get_auth_service()
        if not auth_service:
            self._write_error_response(503, "VKM backend not available")
            raise tornado.web.HTTPError(503)
        return auth_service


class MainHandler(BaseHandler):
    """Handler for the main VKM page."""

    def get(self) -> None:
        """Handle GET request for the main page."""
        self.render("vkm/index.html")


class AuthStatusHandler(BaseHandler):
    """Handler for authentication status requests."""

    def get(self) -> None:
        """Handle GET request for authentication status."""
        try:
            auth_service = self._validate_auth_service()
            status = auth_service.get_status()
            self._write_status_response(status)
        except tornado.web.HTTPError:
            pass
        except Exception as e:
            self.logger.exception("Error getting auth status")
            self._write_error_response(500, str(e))


class AuthLoginHandler(BaseHandler):
    """Handler for authentication login requests."""

    def post(self) -> None:
        """Handle POST request for authentication login."""
        try:
            auth_service = self._validate_auth_service()

            data = self._parse_json_body()
            login = data.get("login")
            password = data.get("password")

            if not login or not password:
                self._write_error_response(400, "Login and password are required")
                return

            # Validate input for security
            is_valid, error_msg = validate_login_password(login, password)
            if not is_valid:
                self._write_error_response(400, error_msg)
                return

            # Start the authentication process
            auth_service.start_auth(login, password)

            # Return the current status
            status = auth_service.get_status()
            self._write_status_response(status)

        except ValueError as e:
            self._write_error_response(400, str(e))
        except tornado.web.HTTPError:
            pass
        except Exception as e:
            self.logger.exception("Error during authentication")
            self._write_error_response(500, str(e))


class AuthVerifyHandler(BaseHandler):
    """Handler for authentication verification requests."""

    def post(self) -> None:
        """Handle POST request for authentication verification."""
        try:
            auth_service = self._validate_auth_service()

            data = self._parse_json_body()
            captcha_solution = data.get("captcha")
            two_factor_code = data.get("code")

            current_status = auth_service.get_status()
            status_value = current_status.get("status")

            if status_value == AuthStatus.CAPTCHA_REQUIRED.value and captcha_solution:
                # Validate captcha solution for security
                is_valid, error_msg = validate_captcha_solution(captcha_solution)
                if not is_valid:
                    self._write_error_response(400, error_msg)
                    return

                # Submit captcha solution
                auth_service.submit_captcha(captcha_solution)
            elif (
                status_value == AuthStatus.TWO_FACTOR_REQUIRED.value and two_factor_code
            ):
                # Validate two-factor code for security
                is_valid, error_msg = validate_two_factor_code(two_factor_code)
                if not is_valid:
                    self._write_error_response(400, error_msg)
                    return

                # Submit two-factor code
                auth_service.submit_two_factor(two_factor_code)
            else:
                self._write_error_response(
                    400, "Invalid verification data for current status"
                )
                return

            # Return the current status
            status = auth_service.get_status()
            self._write_status_response(status)

        except ValueError as e:
            self._write_error_response(400, str(e))
        except tornado.web.HTTPError:
            pass
        except Exception as e:
            self.logger.exception("Error during verification")
            self._write_error_response(500, str(e))


class AuthCancelHandler(BaseHandler):
    """Handler for authentication cancellation requests."""

    def post(self) -> None:
        """Handle POST request for authentication cancellation."""
        try:
            auth_service = self._validate_auth_service()

            # Cancel the authentication process
            auth_service.cancel_auth()

            # Return the current status
            status = auth_service.get_status()
            self._write_status_response(status)

        except tornado.web.HTTPError:
            pass
        except Exception as e:
            self.logger.exception("Error during cancellation")
            self._write_error_response(500, str(e))


class CaptchaPageHandler(BaseHandler):
    """Handler for captcha page."""

    def get(self) -> None:
        """Handle GET request for captcha page."""
        auth_service = self.get_auth_service()
        if not auth_service:
            self.redirect("/vkm/")
            return

        current_status = auth_service.get_status()
        if current_status.get("status") != AuthStatus.CAPTCHA_REQUIRED.value:
            self.redirect("/vkm/")
            return

        captcha_url = current_status.get("captcha_url")
        if not captcha_url:
            self._write_error_response(500, "Captcha URL not available")
            return

        self.render("vkm/captcha.html", captcha_url=captcha_url)


class TwoFactorPageHandler(BaseHandler):
    """Handler for two-factor authentication page."""

    def get(self) -> None:
        """Handle GET request for two-factor page."""
        auth_service = self.get_auth_service()
        if not auth_service:
            self.redirect("/vkm/")
            return

        current_status = auth_service.get_status()
        if current_status.get("status") != AuthStatus.TWO_FACTOR_REQUIRED.value:
            self.redirect("/vkm/")
            return

        self.render("vkm/twofactor.html")


class ChallengeSubmitHandler(BaseHandler):
    """Unified handler for captcha and two-factor authentication submission."""

    def post(self) -> None:
        """Handle POST request for challenge submission."""
        try:
            auth_service = self._validate_auth_service()

            data = self._parse_json_body()
            current_status = auth_service.get_status()
            status_value = current_status.get("status")

            if status_value == AuthStatus.CAPTCHA_REQUIRED.value:
                captcha_solution = data.get("captcha_solution")
                if not captcha_solution:
                    self._write_error_response(400, "Captcha solution is required")
                    return

                # Validate captcha solution for security
                is_valid, error_msg = validate_captcha_solution(captcha_solution)
                if not is_valid:
                    self._write_error_response(400, error_msg)
                    return

                # Submit captcha solution
                auth_service.submit_captcha(captcha_solution)

            elif status_value == AuthStatus.TWO_FACTOR_REQUIRED.value:
                two_factor_code = data.get("twofactor_code")
                if not two_factor_code:
                    self._write_error_response(400, "Two-factor code is required")
                    return

                # Validate two-factor code for security
                is_valid, error_msg = validate_two_factor_code(two_factor_code)
                if not is_valid:
                    self._write_error_response(400, error_msg)
                    return

                # Submit two-factor code
                auth_service.submit_two_factor(two_factor_code)

            else:
                self._write_error_response(400, "No challenge required")
                return

            # Return the current status
            status = auth_service.get_status()
            self._write_status_response(status)

        except ValueError as e:
            self._write_error_response(400, str(e))
        except tornado.web.HTTPError:
            pass
        except Exception as e:
            self.logger.exception("Error during challenge submission")
            self._write_error_response(500, str(e))
