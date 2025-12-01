"""Unified VK authentication service with credentials management."""

from __future__ import annotations

import logging
import pathlib
import threading
from typing import Any

from mopidy_vkm.auth.exceptions import (
    AuthCancelledError,
    AuthFailedError,
    CaptchaRequiredError,
    TwoFactorRequiredError,
)
from mopidy_vkm.auth.handlers import get_global_auth_handlers
from mopidy_vkm.auth.status import AuthStatus

logger = logging.getLogger(__name__)


class VKMAuthService:
    """Unified VK authentication service using vkpymusic."""

    def __init__(self, config_path: str | pathlib.Path, config: dict[str, Any]) -> None:
        """Initialize unified auth service.

        Args:
            config_path: Path to vkpymusic configuration file.
            config: The extension configuration.
        """
        self.config_path = pathlib.Path(config_path)
        self.config = config
        self.status = AuthStatus.NOT_AUTHENTICATED
        self.error_message: str | None = None
        self.captcha_sid: str | None = None
        self.captcha_img: str | None = None
        self.vk_service = None
        self._auth_lock = threading.Lock()
        self._auth_thread: threading.Thread | None = None

        # Try to initialize service with existing credentials
        self._initialize_service()

    # Credentials management methods (from old credentials.py)
    def has_credentials(self) -> bool:
        """Check if credentials are available.

        Returns:
            True if vkpymusic service can be loaded, False otherwise.
        """
        return self.load_service() is not None

    def load_service(self) -> Any | None:
        """Load vkpymusic Service from native config.

        Returns:
            The vkpymusic Service instance or None if failed.
        """
        try:
            import vkpymusic

            return vkpymusic.Service.parse_config(str(self.config_path))
        except Exception as e:
            logger.debug("Failed to load vkpymusic service: %s", e)
            return None

    def save_token(self, token_receiver: Any) -> None:
        """Save token using vkpymusic native method.

        Args:
            token_receiver: Authenticated TokenReceiver instance.
        """
        try:
            token_receiver.save_to_config(str(self.config_path))
            logger.info("Token saved to vkpymusic config")
        except Exception as e:
            logger.warning("Failed to save token: %s", e)

    def clear_credentials(self) -> None:
        """Clear stored credentials."""
        try:
            if self.config_path.exists():
                self.config_path.unlink()
                logger.info("Credentials cleared")
        except OSError as e:
            logger.warning("Failed to clear credentials: %s", e)

    # Service management methods (from old service.py)
    def _initialize_service(self) -> None:
        """Initialize VK service with existing credentials if available."""
        try:
            self.vk_service = self.load_service()
            if self.vk_service:
                self.status = AuthStatus.SUCCESS
                logger.info("VK service initialized with existing credentials")
            else:
                self.status = AuthStatus.NOT_AUTHENTICATED
                logger.info("No VK service available, authentication needed")
        except Exception:
            logger.exception("Failed to initialize VK service")
            self.status = AuthStatus.ERROR
            self.error_message = "Failed to initialize VK service"

    def start_auth(self, login: str, password: str) -> None:
        """Start authentication process in a separate thread.

        Args:
            login: The VK login (email or phone).
            password: The VK password.
        """
        logger.debug(
            "Starting authentication for login: %s",
            login[:3] + "***" if len(login) > 3 else "***",
        )

        if self._auth_thread and self._auth_thread.is_alive():
            logger.warning("Authentication already in progress")
            return

        with self._auth_lock:
            self.status = AuthStatus.PROCESSING
            self.error_message = None
            self.captcha_sid = None
            self.captcha_img = None

            self._auth_thread = threading.Thread(
                target=self._auth_thread_func,
                args=(login, password),
                daemon=True,
            )
            self._auth_thread.start()
            logger.debug("Authentication thread started")

    def _setup_auth_handlers(self):
        """Set up auth handlers for exception flow.

        Returns:
            Tuple of (auth_handlers, original_captcha_handler, original_2fa_handler)
        """
        auth_handlers = get_global_auth_handlers()
        original_captcha_handler = auth_handlers.captcha_handler
        original_2fa_handler = auth_handlers.two_factor_handler
        return auth_handlers, original_captcha_handler, original_2fa_handler

    def _restore_auth_handlers(
        self, auth_handlers, original_captcha_handler, original_2fa_handler
    ):
        """Restore original auth handlers."""
        auth_handlers.captcha_handler = original_captcha_handler
        auth_handlers.two_factor_handler = original_2fa_handler

    def _create_token_receiver(self, login: str, password: str):
        """Create vkpymusic TokenReceiver instance."""
        import vkpymusic

        logger.debug("Creating TokenReceiver for vkpymusic")
        return vkpymusic.TokenReceiver(login, password)

    def _perform_authentication(self, token_receiver):
        """Perform the actual authentication.

        Args:
            token_receiver: The vkpymusic TokenReceiver instance.

        Raises:
            ValueError: If authentication fails.
        """
        logger.debug("Attempting authentication with vkpymusic")
        try:
            # Get global auth handlers for callback integration
            auth_handlers = get_global_auth_handlers()

            # Pass handlers to auth method as callbacks
            auth_result = token_receiver.auth(
                on_captcha=auth_handlers.captcha_handler,
                on_2fa=auth_handlers.two_factor_handler,
            )
            logger.debug("Authentication result: %s", auth_result)
            if not auth_result:
                raise ValueError("Authentication failed")
            logger.debug("Authentication successful")
        except Exception as e:
            logger.debug("Authentication exception: %s", type(e).__name__)
            raise

    def _finalize_authentication(self, token_receiver):
        """Save token and load service after successful auth.

        Args:
            token_receiver: The authenticated TokenReceiver instance.

        Raises:
            ValueError: If service loading fails.
        """
        logger.debug("Finalizing authentication - saving token")
        # Save token using vkpymusic's built-in method
        self.save_token(token_receiver)

        # Load service
        logger.debug("Loading service after token save")
        self.vk_service = self.load_service()
        if self.vk_service:
            with self._auth_lock:
                self.status = AuthStatus.SUCCESS
            logger.info("Authentication successful")
        else:
            raise ValueError("Failed to load service after authentication")

    def _handle_captcha_required(self, e):
        """Handle captcha required exception."""
        logger.debug("Captcha required exception received: %s", e)
        with self._auth_lock:
            self.status = AuthStatus.CAPTCHA_REQUIRED
            self.captcha_img = e.captcha_url
        logger.info("Captcha required, redirecting to web UI")

    def _handle_2fa_required(self):
        """Handle two-factor authentication required exception."""
        logger.debug("Two-factor authentication required")
        with self._auth_lock:
            self.status = AuthStatus.TWO_FACTOR_REQUIRED
        logger.info("Two-factor authentication required, redirecting to web UI")

    def _handle_auth_cancelled(self):
        """Handle authentication cancelled exception."""
        logger.debug("Authentication cancelled")
        with self._auth_lock:
            self.status = AuthStatus.ERROR
            self.error_message = "Authentication cancelled by user"
        logger.info("Authentication cancelled by user")

    def _handle_auth_failed(self, e):
        """Handle authentication failed exception."""
        logger.debug(
            "Authentication failed exception: %s - %s", type(e).__name__, e.message
        )
        with self._auth_lock:
            self.status = AuthStatus.ERROR
            self.error_message = e.message
        logger.warning("Authentication failed: %s", e.message)

    def _auth_thread_func(self, login: str, password: str) -> None:
        """Enhanced authentication thread function with exception flow support.

        Args:
            login: The VK login (email or phone).
            password: The VK password.
        """
        logger.debug("Authentication thread started for login: %s", login[:3] + "***")
        try:
            # Set up auth handlers
            (
                auth_handlers,
                original_captcha_handler,
                original_2fa_handler,
            ) = self._setup_auth_handlers()

            try:
                # Create token receiver
                logger.debug("Step 1: Creating token receiver")
                token_receiver = self._create_token_receiver(login, password)

                # Try to authenticate - this may raise exceptions
                logger.debug("Step 2: Attempting authentication")
                self._perform_authentication(token_receiver)

                # Finalize authentication (save token, load service)
                logger.debug("Step 3: Finalizing authentication")
                self._finalize_authentication(token_receiver)

            except Exception as e:
                # Check if this is one of our custom auth exceptions
                auth_handlers = get_global_auth_handlers()
                current_status = auth_handlers.status

                if current_status == AuthStatus.CAPTCHA_REQUIRED:
                    logger.debug("Captcha required during authentication")
                    self._handle_captcha_required(e)
                    return
                elif current_status == AuthStatus.TWO_FACTOR_REQUIRED:
                    logger.debug("Two-factor required during authentication")
                    self._handle_2fa_required()
                    return
                elif isinstance(e, AuthCancelledError):
                    logger.debug("Authentication cancelled")
                    self._handle_auth_cancelled()
                    return
                elif isinstance(e, AuthFailedError):
                    logger.debug("Authentication failed with custom exception")
                    self._handle_auth_failed(e)
                    return
                else:
                    # Re-raise the exception to be handled by the outer catch block
                    raise

            finally:
                # Restore original handlers
                logger.debug("Restoring original auth handlers")
                self._restore_auth_handlers(
                    auth_handlers, original_captcha_handler, original_2fa_handler
                )

        except Exception as e:
            logger.debug(
                "Unexpected authentication error: %s - %s", type(e).__name__, e
            )
            with self._auth_lock:
                self.status = AuthStatus.ERROR
                self.error_message = f"Authentication failed: {e!s}"
            logger.exception("Unexpected authentication error")

    def cancel_auth(self) -> None:
        """Cancel the authentication process."""
        logger.debug("Cancelling authentication")
        with self._auth_lock:
            self.status = AuthStatus.ERROR
            self.error_message = "Authentication cancelled by user"
            logger.info("Authentication cancelled")

    def _build_status_base(self) -> dict[str, Any]:
        """Build base status dictionary."""
        return {"status": self.status.value}

    def _add_error_info(self, result: dict[str, Any]) -> None:
        """Add error information to status result."""
        if self.status == AuthStatus.ERROR and self.error_message:
            result["error"] = self.error_message

    def _add_captcha_info(self, result: dict[str, Any]) -> None:
        """Add captcha information to status result."""
        if self.status == AuthStatus.CAPTCHA_REQUIRED:
            result["captcha_sid"] = self.captcha_sid or ""
            result["captcha_img"] = self.captcha_img or ""

    def _add_user_info(self, result: dict[str, Any]) -> None:
        """Add user information to status result."""
        if self.status == AuthStatus.SUCCESS and self.vk_service:
            # Get user info from vkpymusic service if available
            try:
                if hasattr(self.vk_service, "get_user_info"):
                    user_info = self.vk_service.get_user_info()
                    if user_info:
                        if isinstance(user_info, dict):
                            result["user_id"] = user_info.get("id", "unknown")
                            if "first_name" in user_info and "last_name" in user_info:
                                result["profile_name"] = (
                                    f"{user_info['first_name']} "
                                    f"{user_info['last_name']}"
                                )
                        elif hasattr(user_info, "id"):
                            result["user_id"] = getattr(user_info, "id", "unknown")
                            if hasattr(user_info, "first_name") and hasattr(
                                user_info, "last_name"
                            ):
                                first_name = getattr(user_info, "first_name", "")
                                last_name = getattr(user_info, "last_name", "")
                                result[
                                    "profile_name"
                                ] = f"{first_name} {last_name}".strip()
            except Exception as e:
                logger.debug("Failed to get user info: %s", e)

    def get_status(self) -> dict[str, Any]:
        """Get current authentication status.

        Returns:
            A dictionary with status and additional information.
        """
        with self._auth_lock:
            result = self._build_status_base()
            self._add_error_info(result)
            self._add_captcha_info(result)
            self._add_user_info(result)
            return result

    def _submit_challenge(self, solution: str, challenge_type: str) -> None:
        """Unified method for submitting challenges (captcha or 2FA).

        Args:
            solution: The challenge solution.
            challenge_type: Type of challenge ('captcha' or '2fa').
        """
        logger.debug("Submitting %s solution", challenge_type)
        try:
            auth_handlers = get_global_auth_handlers()

            if challenge_type == "captcha":
                auth_handlers.submit_captcha(solution)
                solution_value = auth_handlers.resume_after_captcha()
                logger.info("Captcha submitted successfully: %s", solution_value)
            else:  # 2FA
                auth_handlers.submit_two_factor(solution)
                code_value = auth_handlers.resume_after_two_factor()
                logger.info("Two-factor code submitted successfully: %s", code_value)

        except Exception as e:
            logger.exception("Failed to submit %s", challenge_type)
            with self._auth_lock:
                self.status = AuthStatus.ERROR
                self.error_message = (
                    f"{challenge_type.title()} submission failed: {e!s}"
                )

    def submit_captcha(self, captcha_solution: str) -> None:
        """Submit captcha solution using global auth handlers.

        Args:
            captcha_solution: The captcha solution.
        """
        self._submit_challenge(captcha_solution, "captcha")

    def submit_two_factor(self, two_factor_code: str) -> None:
        """Submit two-factor authentication code using global auth handlers.

        Args:
            two_factor_code: The two-factor code.
        """
        self._submit_challenge(two_factor_code, "2fa")
