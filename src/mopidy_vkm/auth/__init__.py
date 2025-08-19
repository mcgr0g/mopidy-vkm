"""VK authentication module."""

from mopidy_vkm.auth.credentials import CredentialsManager
from mopidy_vkm.auth.handlers import AuthHandlers, get_handler_methods
from mopidy_vkm.auth.service import VKMAuthService
from mopidy_vkm.auth.status import AuthStatus
from mopidy_vkm.auth.token import Service, TokenReceiver

__all__ = [
    "AuthHandlers",
    "AuthStatus",
    "CredentialsManager",
    "Service",
    "TokenReceiver",
    "VKMAuthService",
    "get_handler_methods",
]
