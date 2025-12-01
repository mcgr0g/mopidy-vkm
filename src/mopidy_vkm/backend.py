"""VKM backend."""

import logging
from typing import Any

import pykka
from mopidy import backend

from mopidy_vkm.auth import VKMAuthService

logger = logging.getLogger(__name__)


class VKMBackend(pykka.ThreadingActor, backend.Backend):
    """VKM backend with TokenReceiver authentication."""

    def __init__(self, config: dict[str, Any], audio: object) -> None:
        """Initialize VKM backend."""
        super().__init__()
        self.uri_schemes = ["vkm"]
        self.config = config["vkm"]
        self.audio = audio

        # Initialize unified auth service
        sensitive_cache_path = self.config["sensitive_cache_path"]
        self.auth_service = VKMAuthService(sensitive_cache_path, self.config)

        # TODO: Initialize library and playback provider  # noqa: FIX002

    @property
    def library(self) -> object:
        """Get the library provider (placeholder)."""
        return None

    @property
    def playback(self) -> object:
        """Get the playback provider (placeholder)."""
        return None

    @property
    def playlists(self) -> object:
        """Get the playlists provider (placeholder)."""
        return None
