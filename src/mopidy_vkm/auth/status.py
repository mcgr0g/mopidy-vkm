"""Authentication status definitions."""

from enum import Enum


class AuthStatus(Enum):
    """Authentication status enum."""

    PROCESSING = "processing"
    CAPTCHA_REQUIRED = "captcha_required"
    TWO_FACTOR_REQUIRED = "2fa_required"
    SUCCESS = "success"
    ERROR = "error"
