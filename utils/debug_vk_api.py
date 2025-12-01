#!/usr/bin/env python3
"""
Диагностический скрипт для vkpymusic API
Собирает полную информацию о запросах и ответах VK API
"""

import os
import sys
import json
import logging
from typing import Dict, Any
import httpx
from unittest.mock import patch

# Добавляем путь к vkpymusic для импорта
sys.path.insert(0, "/home/mopidy/.venv/lib/python3.11/site-packages")

from vkpymusic import TokenReceiver
from vkpymusic.vk_api.vk_api_request import VkApiRequest


class DebugTokenReceiver(TokenReceiver):
    """Расширенный TokenReceiver с детальным логированием"""

    def __init__(self, login: str, password: str):
        super().__init__(login, password)
        self._setup_debug_logging()

    def _setup_debug_logging(self):
        """Настройка детального логирования"""
        # Создаем logger для диагностики
        self.debug_logger = logging.getLogger("vk_debug")
        self.debug_logger.setLevel(logging.DEBUG)

        # Handler для вывода в файл
        handler = logging.FileHandler("debug_vk_api.log", mode="w")
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.debug_logger.addHandler(handler)

        # Handler для консоли
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("DEBUG: %(message)s")
        console_handler.setFormatter(console_formatter)
        self.debug_logger.addHandler(console_handler)

    def log_request_details(
        self, method: str, url: str, headers: Dict[str, str], params: Dict[str, Any]
    ):
        """Логирование деталей запроса"""
        self.debug_logger.info("=" * 60)
        self.debug_logger.info("REQUEST DETAILS:")
        self.debug_logger.info(f"Method: {method}")
        self.debug_logger.info(f"URL: {url}")
        self.debug_logger.info("Headers:")
        for k, v in headers.items():
            self.debug_logger.info(f"  {k}: {v}")
        self.debug_logger.info("Parameters:")
        for k, v in params.items():
            # Маскируем чувствительные данные
            if "password" in k.lower() or "secret" in k.lower():
                self.debug_logger.info(f"  {k}: ***MASKED***")
            else:
                self.debug_logger.info(f"  {k}: {v}")
        self.debug_logger.info("=" * 60)

    def log_response_details(
        self, status_code: int, response_headers: Dict[str, str], response_body: str
    ):
        """Логирование деталей ответа"""
        self.debug_logger.info("RESPONSE DETAILS:")
        self.debug_logger.info(f"Status Code: {status_code}")
        self.debug_logger.info("Response Headers:")
        for k, v in response_headers.items():
            self.debug_logger.info(f"  {k}: {v}")
        self.debug_logger.info("Response Body:")
        try:
            # Пытаемся красиво отформатировать JSON
            parsed = json.loads(response_body)
            self.debug_logger.info(json.dumps(parsed, indent=2, ensure_ascii=False))
        except:
            self.debug_logger.info(response_body)
        self.debug_logger.info("=" * 60)

    def log_library_info(self):
        """Логирование информации о библиотеках"""
        self.debug_logger.info("LIBRARY INFO:")
        self.debug_logger.info(f"vkpymusic version: 3.5.1")
        self.debug_logger.info(f"VK API version: 5.131")

        # Информация о клиенте
        self.debug_logger.info("Client Info:")
        self.debug_logger.info(f"  User-Agent: {self.client.user_agent}")
        self.debug_logger.info(f"  Client ID: {self.client.client_id}")
        self.debug_logger.info(f"  Client Secret: {self.client.client_secret[:10]}...")
        self.debug_logger.info("=" * 60)


def on_captcha_handler(url: str) -> str:
    """Handler для captcha"""
    print(f"Captcha URL: {url}")
    captcha_key = input("Captcha: ")
    return captcha_key


def on_2fa_handler() -> str:
    """Handler для 2FA"""
    code = input("2FA Code: ")
    return code


def main():
    """Основная функция диагностики"""
    print("VK API Diagnostic Tool")
    print("=" * 40)

    # Получаем учетные данные
    login = input("Enter VK login: ")
    password = input("Enter VK password: ")

    print("\nStarting VK API diagnostics...")

    # Создаем диагностический receiver
    receiver = DebugTokenReceiver(login, password)
    receiver.log_library_info()

    try:
        # Пытаемся аутентифицироваться
        print("\nAttempting authentication...")
        success = receiver.auth(on_captcha=on_captcha_handler, on_2fa=on_2fa_handler)

        if success:
            token = receiver.get_token()
            if token:
                print(f"\n✅ Authentication successful!")
                print(f"Token: {token[:20]}...")

                # Сохраняем токен для анализа
                with open("debug_token.txt", "w") as f:
                    f.write(f"Full token: {token}")
            else:
                print(f"\n❌ Authentication reported success but no token received!")

        else:
            print(f"\n❌ Authentication failed!")
            print("Check debug_vk_api.log for detailed information")

    except Exception as e:
        print(f"\n💥 Exception occurred: {e}")
        print("Check debug_vk_api.log for detailed information")
        import traceback

        traceback.print_exc()

    print(f"\nDebug log saved to: debug_vk_api.log")
    print(f"Token saved to: debug_token.txt (if successful)")


if __name__ == "__main__":
    main()
