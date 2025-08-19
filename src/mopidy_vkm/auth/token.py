"""VK token and service classes."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


logger = logging.getLogger(__name__)


# Define placeholder classes first
class Service:
    """VK music service."""

    def __init__(self, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize the service."""

    def get_user_info(self) -> dict[str, Any]:
        """Get user information."""
        return {}


class TokenReceiver:
    """VK token receiver."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize the token receiver."""

    def get_token(self) -> None:
        """Get the token."""


# Import with try/except to handle potential import errors
try:
    from vkpymusic import service, token_receiver

    # Override with actual implementations
    Service = service.Service  # type: ignore[assignment]
    TokenReceiver = token_receiver.TokenReceiver  # type: ignore[assignment]
except ImportError:
    logger.exception("Failed to import vkpymusic. Make sure it's installed.")
    # We'll use the placeholder classes defined above
