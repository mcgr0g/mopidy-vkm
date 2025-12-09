"""
VK Cookie-based API
Имперсонация браузера VK с использованием cookies вместо access_token
"""

import asyncio
import aiohttp
import json
import urllib.parse
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class VKCookies:
    """Контейнер для VK cookies"""

    # Критические токены (используются везде)
    httoken: str
    remixsid: str
    remixuas: str
    remixuacck: str
    remixdmgr: str
    remixdmgr_tmp: str

    # Специализированные токены
    remixnsid: Optional[str] = None  # Для vk.com/al_* запросов
    domain_sid: Optional[str] = None  # Для vk.com запросов
    remixnreg_sid: Optional[str] = None  # Для API анонимных запросов

    @classmethod
    def from_cookie_string(cls, cookie_string: str) -> "VKCookies":
        """Создает VKCookies из строки cookies"""
        cookies = {}
        for cookie in cookie_string.split(", "):
            if "=" in cookie:
                key, value = cookie.split("=", 1)
                cookies[key.strip()] = value.strip()

        return cls(
            httoken=cookies.get("httoken", ""),
            remixsid=cookies.get("remixsid", ""),
            remixuas=cookies.get("remixuas", ""),
            remixuacck=cookies.get("remixuacck", ""),
            remixdmgr=cookies.get("remixdmgr", ""),
            remixdmgr_tmp=cookies.get("remixdmgr_tmp", ""),
            remixnsid=cookies.get("remixnsid"),
            domain_sid=cookies.get("domain_sid"),
            remixnreg_sid=cookies.get("remixnreg_sid"),
        )

    def to_cookie_string(self) -> str:
        """Преобразует в строку cookies для HTTP заголовка"""
        cookies = []

        # Критические токены
        if self.httoken:
            cookies.append(f"httoken={self.httoken}")
        if self.remixsid:
            cookies.append(f"remixsid={self.remixsid}")
        if self.remixuas:
            cookies.append(f"remixuas={self.remixuas}")
        if self.remixuacck:
            cookies.append(f"remixuacck={self.remixuacck}")
        if self.remixdmgr:
            cookies.append(f"remixdmgr={self.remixdmgr}")
        if self.remixdmgr_tmp:
            cookies.append(f"remixdmgr_tmp={self.remixdmgr_tmp}")

        # Специализированные токены
        if self.remixnsid:
            cookies.append(f"remixnsid={self.remixnsid}")
        if self.domain_sid:
            cookies.append(f"domain_sid={self.domain_sid}")
        if self.remixnreg_sid:
            cookies.append(f"remixnreg_sid={self.remixnreg_sid}")

        return ", ".join(cookies)

    def get_api_cookies(self) -> str:
        """Возвращает cookies для API.vk.com запросов"""
        cookies = []

        # Для API не нужны remixnsid и domain_sid
        if self.httoken:
            cookies.append(f"httoken={self.httoken}")
        if self.remixsid:
            cookies.append(f"remixsid={self.remixsid}")
        if self.remixuas:
            cookies.append(f"remixuas={self.remixuas}")
        if self.remixuacck:
            cookies.append(f"remixuacck={self.remixuacck}")
        if self.remixdmgr:
            cookies.append(f"remixdmgr={self.remixdmgr}")
        if self.remixdmgr_tmp:
            cookies.append(f"remixdmgr_tmp={self.remixdmgr_tmp}")
        if self.remixnreg_sid:
            cookies.append(f"remixnreg_sid={self.remixnreg_sid}")

        return ", ".join(cookies)

    def get_al_cookies(self) -> str:
        """Возвращает cookies для vk.com/al_* запросов"""
        cookies = []

        # Для AL запросов нужен remixnsid
        if self.httoken:
            cookies.append(f"httoken={self.httoken}")
        if self.remixsid:
            cookies.append(f"remixsid={self.remixsid}")
        if self.remixuas:
            cookies.append(f"remixuas={self.remixuas}")
        if self.remixuacck:
            cookies.append(f"remixuacck={self.remixuacck}")
        if self.remixdmgr:
            cookies.append(f"remixdmgr={self.remixdmgr}")
        if self.remixdmgr_tmp:
            cookies.append(f"remixdmgr_tmp={self.remixdmgr_tmp}")
        if self.remixnsid:
            cookies.append(f"remixnsid={self.remixnsid}")
        if self.domain_sid:
            cookies.append(f"domain_sid={self.domain_sid}")

        return ", ".join(cookies)


class VKCookieAPI:
    """VK API работающий через cookies как браузер"""

    def __init__(self, cookies: Union[str, VKCookies]):
        """
        Инициализация API

        Args:
            cookies: Строка cookies или объект VKCookies
        """
        if isinstance(cookies, str):
            self.cookies = VKCookies.from_cookie_string(cookies)
        else:
            self.cookies = cookies

        self.session: Optional[aiohttp.ClientSession] = None
        self.base_api_url = "https://api.vk.com/method"
        self.base_vk_url = "https://vk.com"

        # Параметры API
        self.client_id = 6287487
        self.api_version = "5.268"

    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def _ensure_session(self):
        """Убеждается что сессия создана"""
        if self.session is None or self.session.closed:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://vk.com",
                "Referer": "https://vk.com/",
                "DNT": "1",
                "Sec-GPC": "1",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "Priority": "u=0",
                "TE": "trailers",
            }
            self.session = aiohttp.ClientSession(headers=headers)

    async def close(self):
        """Закрывает сессию"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _make_api_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Делает запрос к API.vk.com/method/*"""
        await self._ensure_session()

        if params is None:
            params = {}

        # Добавляем стандартные параметры
        params.update({"v": self.api_version})

        url = f"{self.base_api_url}/{method}"
        headers = {
            "Cookie": self.cookies.get_api_cookies(),
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            if self.session is None:
                raise Exception("Session not initialized")
            async with self.session.post(
                url, data=params or {}, headers=headers
            ) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            raise Exception(f"API request failed: {e}")

    async def _make_al_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Делает запрос к vk.com/al_*"""
        await self._ensure_session()

        if params is None:
            params = {}

        url = f"{self.base_vk_url}/{endpoint}"
        headers = {
            "Cookie": self.cookies.get_al_cookies(),
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            if self.session is None:
                raise Exception("Session not initialized")
            async with self.session.post(
                url, data=params or {}, headers=headers
            ) as response:
                response.raise_for_status()

                # AL запросы могут возвращать HTML, проверяем Content-Type
                content_type = response.headers.get("content-type", "").lower()
                if "application/json" in content_type:
                    return await response.json()
                else:
                    # Если не JSON, возвращаем сырой текст
                    text = await response.text()
                    # Пробуем извлечь JSON из HTML если возможно
                    if "payload" in text.lower():
                        # Ищем JSON в HTML
                        import re

                        json_match = re.search(
                            r"<script[^>]*>\s*var\s+payload\s*=\s*({.*?});\s*</script>",
                            text,
                        )
                        if json_match:
                            return json.loads(json_match.group(1))
                    return {"raw_html": text[:500]}  # Возвращаем начало для отладки
        except Exception as e:
            raise Exception(f"AL request failed: {e}")

    async def validate_token(self) -> bool:
        """Валидирует токен через users.get"""
        try:
            result = await self._make_api_request(
                "users.get", {"fields": "id,first_name,last_name"}
            )
            return "response" in result
        except:
            return False

    async def get_profile_info(self) -> Dict[str, Any]:
        """Получает информацию о профиле"""
        result = await self._make_api_request("account.getProfileInfo")

        if "response" in result:
            return result["response"]
        else:
            raise Exception(f"Failed to get profile info: {result}")

    async def get_user_playlists(
        self, owner_id: Optional[int] = None, count: int = 50
    ) -> List[Dict[str, Any]]:
        """Получает плейлисты пользователя"""
        if owner_id is None:
            # Получаем свой ID
            profile = await self.get_profile_info()
            owner_id = profile["id"]

        result = await self._make_api_request(
            "audio.getPlaylists", {"owner_id": owner_id, "count": count}
        )

        if "response" in result:
            return result["response"].get("items", [])
        else:
            raise Exception(f"Failed to get playlists: {result}")

    async def get_playlist_by_id(
        self, owner_id: int, playlist_id: int, access_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получает плейлист по ID"""
        params: Dict[str, Any] = {"owner_id": owner_id, "playlist_id": playlist_id}
        if access_key is not None:
            params["access_key"] = access_key

        result = await self._make_api_request("audio.getPlaylistById", params)

        if "response" in result:
            return result["response"]
        else:
            raise Exception(f"Failed to get playlist: {result}")

    async def get_bookmarks(self) -> Dict[str, Any]:
        """Получает закладки"""
        result = await self._make_al_request(
            "al_bookmarks.php", {"act": "get_bookmarks"}
        )

        if result.get("success", 0) == 1:
            return result.get("data", {})
        else:
            raise Exception(f"Failed to get bookmarks: {result}")

    async def get_audio_by_ids(
        self, owner_id: int, audio_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Получает аудио по ID"""
        # Форматируем аудио ID как owner_id_audio_id
        formatted_ids = [f"{owner_id}_{audio_id}" for audio_id in audio_ids]

        result = await self._make_api_request(
            "audio.getById", {"audios": ",".join(formatted_ids)}
        )

        if "response" in result:
            return result["response"]
        else:
            raise Exception(f"Failed to get audio: {result}")

    async def search_audio(self, q: str, count: int = 50) -> List[Dict[str, Any]]:
        """Ищет аудио"""
        result = await self._make_api_request(
            "audio.search", {"q": q, "count": count, "auto_complete": "1"}
        )

        if "response" in result:
            return result["response"].get("items", [])
        else:
            raise Exception(f"Failed to search audio: {result}")

    async def get_audio_status(self) -> Dict[str, Any]:
        """Получает статус аудио"""
        result = await self._make_al_request("al_audio.php", {"act": "audio_status"})

        if result.get("success", 0) == 1:
            return result.get("data", {})
        else:
            raise Exception(f"Failed to get audio status: {result}")


# Утилиты для работы с захваченными данными
def extract_cookies_from_log(log_file: str) -> VKCookies:
    """Извлекает cookies из лога захваченного трафика"""
    with open(log_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Ищем первый запрос с cookies
    for category, requests in data.get("categories", {}).items():
        for request in requests:
            if "request_headers" in request and "cookie" in request["request_headers"]:
                return VKCookies.from_cookie_string(
                    request["request_headers"]["cookie"]
                )

    raise ValueError("No cookies found in log file")


# Пример использования
async def test_cookie_api():
    """Тестирование cookie API"""
    # Извлекаем cookies из захваченного лога
    cookies = extract_cookies_from_log("logs/vk_universal_analysis.json")

    async with VKCookieAPI(cookies) as api:
        # Тестируем валидацию токена
        print("Token validation:", await api.validate_token())

        # Получаем профиль
        try:
            profile = await api.get_profile_info()
            print(f"Profile: {profile.get('first_name')} {profile.get('last_name')}")
        except Exception as e:
            print(f"Profile error: {e}")

        # Получаем плейлисты
        try:
            playlists = await api.get_user_playlists(count=5)
            print(f"Found {len(playlists)} playlists")
        except Exception as e:
            print(f"Playlists error: {e}")

        # Получаем закладки
        try:
            bookmarks = await api.get_bookmarks()
            print(f"Bookmarks keys: {list(bookmarks.keys())}")
        except Exception as e:
            print(f"Bookmarks error: {e}")


if __name__ == "__main__":
    asyncio.run(test_cookie_api())
