"""
Кастомный валидатор VK токенов для mopidy-vkm
Использует базовые методы вместо vkpymusic для проверки валидности
"""

import logging
import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TokenInfo:
    """Информация о токене"""

    is_valid: bool
    user_id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    has_audio: bool = False
    has_account: bool = False
    error: Optional[str] = None


class VKTokenValidator:
    """Валидатор VK токенов через прямые API запросы"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def validate_token(self, token: str) -> TokenInfo:
        """
        Валидация токена через базовые VK API методы

        Args:
            token: VK токен для проверки

        Returns:
            TokenInfo: информация о токене
        """
        if not token:
            return TokenInfo(is_valid=False, error="Empty token")

        # Базовая проверка через users.get
        user_info = self._check_users_get(token)
        if not user_info:
            return TokenInfo(is_valid=False, error="Failed to get user info")

        # Проверка дополнительных прав
        has_audio = self._check_audio_access(token)
        has_account = self._check_account_access(token)

        return TokenInfo(
            is_valid=True,
            user_id=user_info.get("id"),
            first_name=user_info.get("first_name"),
            last_name=user_info.get("last_name"),
            has_audio=has_audio,
            has_account=has_account,
        )

    def _check_users_get(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверка токена через users.get"""
        try:
            url = f"https://api.vk.com/method/users.get?access_token={token}&v=5.199"
            response = self.client.get(url)

            if response.status_code != 200:
                logger.error(f"VK API HTTP error: {response.status_code}")
                return None

            data = response.json()

            if "error" in data:
                error = data["error"]
                logger.error(
                    f"VK API error: {error.get('error_code')} - {error.get('error_msg')}"
                )
                return None

            if "response" in data and data["response"]:
                user_data = data["response"][0]
                logger.info(
                    f"Token validation successful for user: {user_data.get('first_name')} {user_data.get('last_name')} (ID: {user_data.get('id')})"
                )
                return user_data

            return None

        except Exception as e:
            logger.error(f"Token validation exception: {e}")
            return None

    def _check_audio_access(self, token: str) -> bool:
        """Проверка доступа к аудио"""
        try:
            url = f"https://api.vk.com/method/audio.get?access_token={token}&v=5.199&count=1"
            response = self.client.get(url)

            if response.status_code != 200:
                return False

            data = response.json()

            # Если есть ответ без ошибки, значит доступ есть
            return "response" in data and "error" not in data

        except Exception as e:
            logger.debug(f"Audio access check failed: {e}")
            return False

    def _check_account_access(self, token: str) -> bool:
        """Проверка доступа к методам аккаунта"""
        try:
            url = f"https://api.vk.com/method/account.getProfileInfo?access_token={token}&v=5.199"
            response = self.client.get(url)

            if response.status_code != 200:
                return False

            data = response.json()

            # Если есть ответ без ошибки, значит доступ есть
            return "response" in data and "error" not in data

        except Exception as e:
            logger.debug(f"Account access check failed: {e}")
            return False

    def get_token_capabilities(self, token: str) -> Dict[str, bool]:
        """
        Получить детальную информацию о возможностях токена

        Returns:
            Dict с информацией о доступных методах
        """
        capabilities = {
            "users_get": False,
            "status_get": False,
            "audio_get": False,
            "account_info": False,
            "account_profile": False,
        }

        methods_to_check = [
            ("users.get", "users_get"),
            ("status.get", "status_get"),
            ("audio.get?count=1", "audio_get"),
            ("account.getInfo", "account_info"),
            ("account.getProfileInfo", "account_profile"),
        ]

        for method, key in methods_to_check:
            try:
                url = f"https://api.vk.com/method/{method}?access_token={token}&v=5.199"
                response = self.client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    capabilities[key] = "response" in data and "error" not in data

            except Exception as e:
                logger.debug(f"Capability check for {method} failed: {e}")

        return capabilities

    def close(self):
        """Закрыть HTTP клиент"""
        if self.client:
            self.client.close()

    def __del__(self):
        """Деструктор"""
        self.close()


# Глобальный экземпляр для использования
_validator_instance: Optional[VKTokenValidator] = None


def get_validator() -> VKTokenValidator:
    """Получить экземпляр валидатора"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = VKTokenValidator()
    return _validator_instance


def validate_vk_token(token: str) -> TokenInfo:
    """
    Удобная функция для валидации токена

    Args:
        token: VK токен

    Returns:
        TokenInfo: информация о валидности токена
    """
    validator = get_validator()
    return validator.validate_token(token)


def is_token_sufficient_for_vkpymusic(token: str) -> bool:
    """
    Проверка достаточности прав для vkpymusic

    Args:
        token: VK токен

    Returns:
        bool: True если токен подходит для vkpymusic
    """
    validator = get_validator()
    capabilities = validator.get_token_capabilities(token)

    # vkpymusic требует account.getProfileInfo
    return capabilities.get("account_profile", False)
