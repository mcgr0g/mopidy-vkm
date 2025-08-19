"""Secure storage and retrieval of VK credentials."""

from __future__ import annotations

import json
import logging
import pathlib
import secrets
from typing import Any

logger = logging.getLogger(__name__)


class CredentialsManager:
    """Secure storage and retrieval of VK credentials."""

    def __init__(self, sensitive_cache_path: str | pathlib.Path) -> None:
        """Initialize the credentials manager.

        Args:
            sensitive_cache_path: Path to the credentials file.
        """
        self.sensitive_cache_path = pathlib.Path(sensitive_cache_path)
        self._credentials: dict[str, Any] = {}
        self._user_agent_presets = self._load_user_agent_presets()
        self._load_credentials()

    def _load_user_agent_presets(self) -> list[str]:
        """Load user agent presets from the JSON file.

        Returns:
            A list of user agent strings.
        """
        user_agents_path = pathlib.Path(__file__).parent / "data" / "user_agents.json"
        try:
            with user_agents_path.open(encoding="utf-8") as f:
                user_agents_data = json.load(f)
            # Flatten the nested structure into a single list
            all_agents = []
            for browser_agents in user_agents_data.values():
                if isinstance(browser_agents, list):
                    all_agents.extend(browser_agents)
            if not all_agents:
                logger.warning("No user agents found in %s", user_agents_path)
                return []
            return all_agents  # noqa: TRY300
        except (OSError, json.JSONDecodeError):
            logger.exception(
                "Failed to load user agent presets from %s", user_agents_path
            )
            return []

    def _load_credentials(self) -> None:
        """Load credentials from the file if it exists."""
        if not self.sensitive_cache_path.exists():
            logger.info(
                "Credentials file does not exist at %s", self.sensitive_cache_path
            )
            self._credentials = {}
            return

        try:
            with self.sensitive_cache_path.open(encoding="utf-8") as f:
                self._credentials = json.load(f)
            logger.info("Loaded credentials from %s", self.sensitive_cache_path)
        except (OSError, json.JSONDecodeError):
            logger.exception("Failed to load credentials")
            self._credentials = {}

    def _save_credentials(self) -> None:
        """Save credentials to the file with secure permissions."""
        # Ensure the directory exists
        self.sensitive_cache_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Write to a temporary file first
            temp_path = self.sensitive_cache_path.with_suffix(".tmp")
            with temp_path.open("w", encoding="utf-8") as f:
                json.dump(self._credentials, f, indent=2)

            # Set secure permissions (read/write only for owner)
            temp_path.chmod(0o600)  # Same as os.chmod but using pathlib

            # Rename to the actual file (atomic operation)
            temp_path.rename(self.sensitive_cache_path)
            logger.info("Saved credentials to %s", self.sensitive_cache_path)
        except OSError:
            logger.exception("Failed to save credentials")

    def get_access_token(self) -> str | None:
        """Get the access token if available.

        Returns:
            The access token or None if not available.
        """
        return self._credentials.get("access_token")

    def get_refresh_token(self) -> str | None:
        """Get the refresh token if available.

        Returns:
            The refresh token or None if not available.
        """
        return self._credentials.get("refresh_token")

    def get_client_user_id(self) -> str | None:
        """Get the client user ID if available.

        Returns:
            The client user ID or None if not available.
        """
        return self._credentials.get("client_user_id")

    def get_user_profile(self) -> dict[str, Any] | None:
        """Get the user profile if available.

        Returns:
            The user profile or None if not available.
        """
        return self._credentials.get("user_profile")

    def get_user_agent(self, configured_user_agent: str | None = None) -> str:
        """Get the user agent string based on the selection strategy.

        Args:
            configured_user_agent: User agent from the configuration.

        Returns:
            The user agent string to use.
        """
        # 1. Use the cached value if available
        if "user_agent" in self._credentials:
            return self._credentials["user_agent"]

        # 2. Use the configured value if available
        if configured_user_agent:
            return configured_user_agent

        # 3. Randomly select from preset
        if self._user_agent_presets:
            return secrets.choice(self._user_agent_presets)
        # 4. Fallback to a default user agent if no presets are available
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    def update_credentials(
        self,
        access_token: str | None = None,
        refresh_token: str | None = None,
        client_user_id: str | None = None,
        user_agent: str | None = None,
        user_profile: dict[str, Any] | None = None,
    ) -> None:
        """Update the credentials with new values.

        Args:
            access_token: The access token.
            refresh_token: The refresh token.
            client_user_id: The client user ID.
            user_agent: The user agent string.
            user_profile: The user profile.
        """
        if access_token is not None:
            self._credentials["access_token"] = access_token
        if refresh_token is not None:
            self._credentials["refresh_token"] = refresh_token
        if client_user_id is not None:
            self._credentials["client_user_id"] = client_user_id
        if user_agent is not None:
            self._credentials["user_agent"] = user_agent
        if user_profile is not None:
            self._credentials["user_profile"] = user_profile

        self._save_credentials()

    def clear_credentials(self) -> None:
        """Clear all credentials."""
        self._credentials = {}
        self._save_credentials()

    def has_credentials(self) -> bool:
        """Check if credentials are available.

        Returns:
            True if credentials are available, False otherwise.
        """
        return bool(self.get_access_token())
