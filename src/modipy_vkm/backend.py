"""VKM backend"""

import logging
from typing import Any

from mopidy import backend

logger = logging.getLogger(__name__)


class VKMBackend(backend.Backend):
    """VKM backend with TokenReceiver authentication."""

    def __init__(self, config: dict[str, Any], audio: object) -> None:
        """Initialize VKM backend."""
        super().__init__()
        self.uri_schemes = ["vkm"]
        self.config = config["vkm"]
        self.audio = audio

        # TODO: Initialize credentials manager
        # TODO: Initialize auth service
        # TODO: Initialize library and playback provider
