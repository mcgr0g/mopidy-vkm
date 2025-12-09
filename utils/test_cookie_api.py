#!/usr/bin/env python3
"""
Тестирование VK Cookie API
Проверяет работоспособность cookie-based аутентификации
"""

import asyncio
import json
import sys
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.mopidy_vkm.auth.cookie_api import (
    VKCookieAPI,
    VKCookies,
    extract_cookies_from_log,
)


async def test_cookie_extraction():
    """Тестируем извлечение cookies из лога"""
    print("🔍 Testing cookie extraction from logs...")

    try:
        cookies = extract_cookies_from_log("logs/vk_universal_analysis.json")
        print(f"✅ Successfully extracted cookies:")
        print(f"   httoken: {cookies.httoken[:20]}...")
        print(f"   remixsid: {cookies.remixsid[:20]}...")
        print(f"   remixuas: {cookies.remixuas}")
        print(f"   remixuacck: {cookies.remixuacck}")
        print(
            f"   remixnsid: {cookies.remixnsid[:20]}..."
            if cookies.remixnsid
            else "   remixnsid: None"
        )
        return cookies
    except Exception as e:
        print(f"❌ Failed to extract cookies: {e}")
        return None


async def test_token_validation(api: VKCookieAPI):
    """Тестируем валидацию токена"""
    print("\n🧪 Testing token validation...")

    try:
        is_valid = await api.validate_token()
        if is_valid:
            print("✅ Token is valid")
        else:
            print("❌ Token is invalid")
        return is_valid
    except Exception as e:
        print(f"❌ Token validation failed: {e}")
        return False


async def test_profile_info(api: VKCookieAPI):
    """Тестируем получение информации о профиле"""
    print("\n👤 Testing profile info...")

    try:
        profile = await api.get_profile_info()
        print(f"✅ Profile info retrieved:")
        print(
            f"   Name: {profile.get('first_name', '')} {profile.get('last_name', '')}"
        )
        print(f"   ID: {profile.get('id', 'unknown')}")
        print(f"   Screen name: {profile.get('screen_name', 'none')}")
        return profile
    except Exception as e:
        print(f"❌ Profile info failed: {e}")
        return None


async def test_user_playlists(api: VKCookieAPI):
    """Тестируем получение плейлистов"""
    print("\n🎵 Testing user playlists...")

    try:
        playlists = await api.get_user_playlists(count=5)
        print(f"✅ Found {len(playlists)} playlists:")
        for i, playlist in enumerate(playlists[:3], 1):
            print(
                f"   {i}. {playlist.get('title', 'Untitled')} ({playlist.get('count', 0)} tracks)"
            )
        return playlists
    except Exception as e:
        print(f"❌ Playlists failed: {e}")
        return None


async def test_bookmarks(api: VKCookieAPI):
    """Тестируем получение закладок"""
    print("\n🔖 Testing bookmarks...")

    try:
        bookmarks = await api.get_bookmarks()
        print(f"✅ Bookmarks retrieved:")
        print(f"   Keys: {list(bookmarks.keys())}")
        if "audio" in bookmarks:
            audio_count = len(bookmarks["audio"])
            print(f"   Audio bookmarks: {audio_count}")
        if "playlist" in bookmarks:
            playlist_count = len(bookmarks["playlist"])
            print(f"   Playlist bookmarks: {playlist_count}")
        return bookmarks
    except Exception as e:
        print(f"❌ Bookmarks failed: {e}")
        return None


async def test_audio_search(api: VKCookieAPI):
    """Тестируем поиск аудио"""
    print("\n🔍 Testing audio search...")

    try:
        results = await api.search_audio("Queen", count=3)
        print(f"✅ Search completed:")
        for i, track in enumerate(results, 1):
            artist = track.get("artist", "Unknown")
            title = track.get("title", "Unknown")
            duration = track.get("duration", 0)
            print(f"   {i}. {artist} - {title} ({duration}s)")
        return results
    except Exception as e:
        print(f"❌ Audio search failed: {e}")
        return None


async def test_audio_status(api: VKCookieAPI):
    """Тестируем получение статуса аудио"""
    print("\n🎧 Testing audio status...")

    try:
        status = await api.get_audio_status()
        print(f"✅ Audio status retrieved:")
        print(f"   Status keys: {list(status.keys())}")
        return status
    except Exception as e:
        print(f"❌ Audio status failed: {e}")
        return None


async def main():
    """Основная функция тестирования"""
    print("🚀 Starting VK Cookie API tests")
    print("=" * 50)

    # Шаг 1: Извлечение cookies
    cookies = await test_cookie_extraction()
    if not cookies:
        print("❌ Cannot proceed without valid cookies")
        return

    # Шаг 2: Тестирование API
    async with VKCookieAPI(cookies) as api:
        tests = [
            ("Token Validation", test_token_validation),
            ("Profile Info", test_profile_info),
            ("User Playlists", test_user_playlists),
            ("Bookmarks", test_bookmarks),
            ("Audio Search", test_audio_search),
            ("Audio Status", test_audio_status),
        ]

        results = {}

        for test_name, test_func in tests:
            try:
                result = await test_func(api)
                results[test_name] = result is not None
            except Exception as e:
                print(f"❌ {test_name} crashed: {e}")
                results[test_name] = False

        # Итоги
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        print("=" * 50)

        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status:<8} {test_name}")

        total_tests = len(results)
        passed_tests = sum(results.values())
        print(f"\nTotal: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("🎉 All tests passed! Cookie API is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the implementation.")


if __name__ == "__main__":
    asyncio.run(main())
