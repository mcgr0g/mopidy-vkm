#!/usr/bin/env python3
"""
Простой диагностический скрипт для vkpymusic API
Использует встроенное логирование vkpymusic для анализа запросов
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# Добавляем путь к vkpymusic для импорта
sys.path.insert(0, "/home/mopidy/.venv/lib/python3.11/site-packages")

from vkpymusic import TokenReceiver
from vkpymusic.client import clients


def setup_logging():
    """Настройка детального логирования для vkpymusic"""
    # Настраиваем root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("debug_vk_simple.log", mode="w"),
            logging.StreamHandler(),
        ],
    )

    # Включаем логирование для httpx
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.DEBUG)

    # Включаем логирование для vkpymusic
    vkpymusic_logger = logging.getLogger("vkpymusic")
    vkpymusic_logger.setLevel(logging.DEBUG)


def log_system_info():
    """Логирование системной информации"""
    print("=" * 60)
    print("VK API Diagnostic Tool (Simple Version)")
    print("=" * 60)

    # Информация о библиотеке
    print(f"vkpymusic version: 3.5.1")
    print(f"VK API version: 5.131")

    # Информация о клиенте
    client = clients["Kate"]
    print(f"Client: Kate Mobile")
    print(f"User-Agent: {client.user_agent}")
    print(f"Client ID: {client.client_id}")
    print(f"Client Secret: {client.client_secret[:10]}...")

    print("=" * 60)


def analyze_vk_response(response_data: dict):
    """Анализ ответа от VK API"""
    print("\n" + "=" * 60)
    print("VK API RESPONSE ANALYSIS:")
    print("=" * 60)

    if not response_data:
        print("❌ No response data received")
        return

    # Проверяем наличие ошибок
    if "error" in response_data:
        error = response_data["error"]
        print(f"❌ VK API Error: {error}")

        if "error_type" in response_data:
            error_type = response_data["error_type"]
            print(f"Error Type: {error_type}")

            # Специальная обработка для нашей проблемы
            if error_type == "password_bruteforce_attempt":
                print("🔍 FOUND: 'password_bruteforce_attempt' error!")
                print("This is the error we're investigating!")

        if "error_description" in response_data:
            print(f"Description: {response_data['error_description']}")

        if "captcha_sid" in response_data:
            print(f"Captcha SID: {response_data['captcha_sid']}")
            print("📸 Captcha required")

        if "sid" in response_data:
            print(f"2FA SID: {response_data['sid']}")
            print("📱 2FA required")

    # Проверяем наличие токена
    elif "access_token" in response_data:
        token = response_data["access_token"]
        print(f"✅ Access Token received: {token[:20]}...")

        if "expires_in" in response_data:
            print(f"Expires in: {response_data['expires_in']} seconds")

        if "user_id" in response_data:
            print(f"User ID: {response_data['user_id']}")

    else:
        print("⚠️ Unknown response format")
        print("Full response:")
        print(json.dumps(response_data, indent=2, ensure_ascii=False))

    print("=" * 60)


def on_captcha_handler(url: str) -> str:
    """Handler для captcha"""
    print(f"\n📸 Captcha required!")
    print(f"Captcha URL: {url}")
    captcha_key = input("Enter captcha text: ")
    return captcha_key


def on_2fa_handler() -> str:
    """Handler для 2FA"""
    code = input("Enter 2FA code from SMS/app: ")
    return code


def main():
    """Основная функция диагностики"""
    log_system_info()
    setup_logging()

    print("\n" + "=" * 60)
    print("Starting VK API diagnostics...")
    print("All requests will be logged to debug_vk_simple.log")
    print("=" * 60)

    # Получаем учетные данные
    login = input("\nEnter VK login: ")
    password = input("Enter VK password: ")

    print("\nAttempting authentication...")
    print("Watch the console and log file for detailed information...")

    try:
        # Создаем receiver с логированием
        receiver = TokenReceiver(login, password)

        # Включаем внутреннее логирование
        receiver._logger.setLevel(logging.DEBUG)

        # Пытаемся аутентифицироваться
        success = receiver.auth(on_captcha=on_captcha_handler, on_2fa=on_2fa_handler)

        print(f"\n" + "=" * 60)
        print("AUTHENTICATION RESULT:")
        print("=" * 60)

        if success:
            token = receiver.get_token()
            if token:
                print(f"✅ Authentication reported SUCCESS!")
                print(f"Token: {token[:20]}...")

                # Сохраняем токен для анализа
                with open("debug_token_simple.txt", "w") as f:
                    f.write(f"Full token: {token}\n")
                    f.write(f"Login: {login}\n")
            else:
                print("❌ Authentication reported success but NO TOKEN received!")
        else:
            print("❌ Authentication FAILED!")
            print("Check debug_vk_simple.log for detailed request/response information")

        # Анализируем возможные причины
        print(f"\n" + "=" * 60)
        print("DIAGNOSTIC SUMMARY:")
        print("=" * 60)
        print("Check the log file debug_vk_simple.log for:")
        print("1. HTTP request details (URL, headers, parameters)")
        print("2. HTTP response details (status, headers, body)")
        print("3. VK API error messages")
        print("4. Any 'password_bruteforce_attempt' errors")
        print("=" * 60)

    except Exception as e:
        print(f"\n💥 Exception occurred during authentication: {e}")
        print("This might be the root cause of the problem!")
        print("Check debug_vk_simple.log for detailed error trace")

        import traceback

        traceback.print_exc()

    print(f"\n📄 Detailed log saved to: debug_vk_simple.log")
    print("📄 Token saved to: debug_token_simple.txt (if successful)")


if __name__ == "__main__":
    main()
