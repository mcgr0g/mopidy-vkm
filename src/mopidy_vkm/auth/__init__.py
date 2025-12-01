"""VK authentication module."""

from mopidy_vkm.auth.service import VKMAuthService
from mopidy_vkm.auth.status import AuthStatus

__all__ = [
    "AuthStatus",
    "VKMAuthService",
]
