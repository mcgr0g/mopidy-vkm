"""VKM backend."""

import logging
from typing import Any

from mopidy import backend

from mopidy_vkm.auth import CredentialsManager
from mopidy_vkm.auth.service import VKMAuthService

logger = logging.getLogger(__name__)


class VKMBackend(backend.Backend):
    """VKM backend with TokenReceiver authentication."""

    def __init__(self, config: dict[str, Any], audio: object) -> None:
        """Initialize VKM backend."""
        super().__init__()
        self.uri_schemes = ["vkm"]
        self.config = config["vkm"]
        self.audio = audio

        # Initialize credentials manager
        sensitive_cache_path = self.config["sensitive_cache_path"]
        self.credentials_manager = CredentialsManager(sensitive_cache_path)

        # Initialize auth service
        self.auth_service = VKMAuthService(self.credentials_manager, self.config)

        # TODO: Initialize library and playback provider  # noqa: FIX002
