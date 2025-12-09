#!/usr/bin/env python3
"""
Универсальный анализатор трафика для анализа ВСЕХ доменов и ресурсов
Включая аудио CDN, авторизацию и все типы запросов
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

try:
    from mitmproxy.io import FlowReader
    from mitmproxy import http
except ImportError as e:
    print(f"Ошибка импорта mitmproxy: {e}")
    print("Установите mitmproxy: uv add mitmproxy")
    sys.exit(1)


def extract_all_requests(flow_file_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Извлекает ВСЕ запросы без фильтрации по доменам
    """
    categories = {
        "vk_api": [],  # API методы VK (/method/*)
        "vk_al": [],  # AL методы (al_audio.php, al_bookmarks.php)
        "auth": [],  # Авторизация и токены
        "audio_files": [],  # Аудио файлы
        "video_files": [],  # Видео файлы
        "images": [],  # Изображения
        "scripts": [],  # JavaScript/CSS
        "cdn": [],  # CDN запросы
        "other": [],  # Остальные запросы
    }

    domain_stats = defaultdict(int)
    content_type_stats = defaultdict(int)

    try:
        with open(flow_file_path, "rb") as f:
            reader = FlowReader(f)

            for flow in reader.stream():
                try:
                    if isinstance(flow, http.HTTPFlow) and flow.request:
                        request_info = analyze_request(flow)
                        if request_info:
                            category = categorize_request(request_info)
                            categories[category].append(request_info)

                            # Собираем статистику
                            domain_stats[request_info["domain"]] += 1
                            if request_info["content_type"]:
                                content_type_stats[request_info["content_type"]] += 1
                except Exception as e:
                    print(f"Ошибка при обработке flow: {e}")
                    continue

    except Exception as e:
        print(f"Ошибка при чтении flow файла: {e}")
        import traceback

        traceback.print_exc()
        return {}

    # Добавляем статистику
    result = {
        "categories": categories,
        "domain_stats": dict(domain_stats),
        "content_type_stats": dict(content_type_stats),
    }

    return result


def analyze_request(flow: http.HTTPFlow) -> Optional[Dict[str, Any]]:
    """Анализирует отдельный запрос"""
    if not flow.request:
        return None

    url = flow.request.pretty_url
    if not url:
        return None

    try:
        parsed_url = urlparse(url)
    except Exception:
        return None

    request_info = {
        "url": url,
        "method": flow.request.method or "GET",
        "domain": parsed_url.netloc or "",
        "path": parsed_url.path or "",
        "query_params": dict(flow.request.query) if flow.request.query else {},
        "timestamp": getattr(flow, "timestamp_start", None),
        "request_headers": dict(flow.request.headers) if flow.request.headers else {},
        "response_status": getattr(flow.response, "status_code", None)
        if flow.response
        else None,
        "response_headers": dict(getattr(flow.response, "headers", {}))
        if flow.response
        else {},
        "content_type": None,
        "content_length": 0,
        "form_data": {},
    }

    # Извлекаем Content-Type и Content-Length
    if flow.response:
        request_info["content_type"] = flow.response.headers.get(
            "content-type", ""
        ).split(";")[0]
        request_info["content_length"] = flow.response.headers.get(
            "content-length", "0"
        )

    # Извлекаем form данные
    try:
        if flow.request.content:
            content_type = flow.request.headers.get("content-type", "")
            if "application/x-www-form-urlencoded" in content_type:
                form_data = parse_qs(
                    flow.request.content.decode("utf-8", errors="ignore")
                )
                request_info["form_data"] = {
                    k: v[0] if v else "" for k, v in form_data.items()
                }
            elif "application/json" in content_type:
                request_info["form_data"] = json.loads(
                    flow.request.content.decode("utf-8", errors="ignore")
                )
    except Exception:
        pass

    return request_info


def categorize_request(request_info: Dict[str, Any]) -> str:
    """Классифицирует запрос по типу"""
    domain = request_info.get("domain", "").lower()
    path = request_info.get("path", "").lower()
    url = request_info.get("url", "").lower()
    content_type = request_info.get("content_type", "").lower()

    # Авторизация
    if any(keyword in path for keyword in ["auth", "login", "token", "oauth"]) or any(
        keyword in url for keyword in ["access_token", "auth_hash", "sid="]
    ):
        return "auth"

    # VK API методы
    if "vk.com" in domain and "/method/" in path:
        return "vk_api"

    # VK AL методы
    if "vk.com" in domain and any(
        keyword in path for keyword in ["al_audio.php", "al_bookmarks.php"]
    ):
        return "vk_al"

    # Аудио файлы
    if any(keyword in domain for keyword in ["audio", "vkuseraudio"]) or any(
        keyword in content_type for keyword in ["audio/", "mpeg", "mp3", "m4a", "ogg"]
    ):
        return "audio_files"

    # Видео файлы
    if any(keyword in domain for keyword in ["video", "vkuservideo"]) or any(
        keyword in content_type for keyword in ["video/", "mp4", "webm"]
    ):
        return "video_files"

    # CDN запросы
    if any(keyword in domain for keyword in ["cdn", "userapi", "vk-cdn"]) or any(
        keyword in domain for keyword in ["cs", "static"]
    ):
        return "cdn"

    # Изображения
    if any(
        keyword in content_type
        for keyword in ["image/", "jpeg", "jpg", "png", "gif", "webp"]
    ):
        return "images"

    # JavaScript/CSS
    if any(keyword in content_type for keyword in ["javascript", "css"]) or any(
        keyword in path for keyword in [".js", ".css"]
    ):
        return "scripts"

    return "other"


def analyze_auth_flow(requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Анализирует поток авторизации"""
    auth_requests = [
        req
        for req in requests
        if "auth" in req.get("url", "").lower()
        or "access_token" in req.get("form_data", {})
    ]

    auth_flow = {
        "total_auth_requests": len(auth_requests),
        "auth_domains": set(),
        "auth_methods": set(),
        "token_sources": [],
        "auth_sequence": [],
    }

    for req in auth_requests:
        auth_flow["auth_domains"].add(req["domain"])
        auth_flow["auth_methods"].add(f"{req['method']} {req['path']}")

        # Ищем токены в параметрах
        for param_name, param_value in req["form_data"].items():
            if "token" in param_name.lower() or "auth" in param_name.lower():
                auth_flow["token_sources"].append(
                    {
                        "url": req["url"],
                        "param": param_name,
                        "value_preview": str(param_value)[:50] + "..."
                        if len(str(param_value)) > 50
                        else str(param_value),
                    }
                )

        auth_flow["auth_sequence"].append(
            {
                "timestamp": req["timestamp"],
                "method": req["method"],
                "path": req["path"],
                "domain": req["domain"],
            }
        )

    # Сортируем по времени
    auth_flow["auth_sequence"].sort(key=lambda x: x["timestamp"] or 0)

    return {
        "total_auth_requests": auth_flow["total_auth_requests"],
        "auth_domains": list(auth_flow["auth_domains"]),
        "auth_methods": list(auth_flow["auth_methods"]),
        "token_sources": auth_flow["token_sources"],
        "auth_sequence": auth_flow["auth_sequence"][:10],  # Первые 10 шагов
    }


def analyze_audio_domains(requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Анализирует запросы к аудио доменам"""
    audio_domains = [
        req
        for req in requests
        if any(keyword in req["domain"] for keyword in ["audio", "vkuseraudio"])
        or req.get("content_type", "").startswith("audio/")
    ]

    # Исправляем структуру данных
    domain_analysis: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "requests": [],
            "file_types": set(),
            "total_size": 0,
            "status_codes": set(),
        }
    )

    for req in audio_domains:
        domain = req["domain"]
        domain_analysis[domain]["requests"].append(req)

        # Определяем тип файла
        path = req["path"].lower()
        if any(ext in path for ext in [".mp3", "mp3"]):
            domain_analysis[domain]["file_types"].add("mp3")
        elif any(ext in path for ext in [".m4a", "m4a"]):
            domain_analysis[domain]["file_types"].add("m4a")
        elif any(ext in path for ext in [".ogg", "ogg"]):
            domain_analysis[domain]["file_types"].add("ogg")

        # Размер
        try:
            size = int(req.get("content_length", 0))
            domain_analysis[domain]["total_size"] += size
        except:
            pass

        # Статусы
        if req["response_status"]:
            domain_analysis[domain]["status_codes"].add(req["response_status"])

    # Конвертируем sets в lists
    result = {}
    for domain, data in domain_analysis.items():
        result[domain] = {
            "request_count": len(data["requests"]),
            "file_types": list(data["file_types"]),
            "total_size_bytes": data["total_size"],
            "total_size_mb": round(data["total_size"] / (1024 * 1024), 2),
            "status_codes": list(data["status_codes"]),
            "sample_urls": [req["url"] for req in data["requests"][:3]],
        }

    return result


def find_request_patterns(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Находит паттерны в последовательности запросов"""
    # Сортируем по времени
    sorted_requests = sorted(
        [req for req in requests if req["timestamp"]], key=lambda x: x["timestamp"]
    )

    patterns = []

    # Ищем последовательности: API -> аудио URL
    for i, req in enumerate(sorted_requests):
        if req["response_status"] == 200:
            # Если это API запрос, ищем следующие аудио запросы
            if "/method/" in req["path"] or "al_audio.php" in req["path"]:
                next_requests = sorted_requests[i + 1 : i + 6]  # Следующие 5 запросов
                audio_after_api = [
                    r
                    for r in next_requests
                    if r["domain"] != req["domain"]
                    and (
                        r.get("content_type", "").startswith("audio/")
                        or "audio" in r["domain"]
                    )
                ]

                if audio_after_api:
                    patterns.append(
                        {
                            "type": "api_to_audio",
                            "api_request": {
                                "url": req["url"],
                                "method": req["method"],
                                "timestamp": req["timestamp"],
                            },
                            "audio_requests": [
                                {
                                    "url": r["url"],
                                    "domain": r["domain"],
                                    "delay_ms": int(
                                        (r["timestamp"] - req["timestamp"]) * 1000
                                    )
                                    if r["timestamp"] and req["timestamp"]
                                    else 0,
                                }
                                for r in audio_after_api[:3]
                            ],
                        }
                    )

    return patterns[:10]  # Возвращаем первые 10 паттернов


def print_domain_analysis(analysis_result: Dict[str, Any]):
    """Выводит анализ по доменам"""
    print("\n" + "=" * 80)
    print("АНАЛИЗ ДОМЕНОВ И ТИПОВ ЗАПРОСОВ")
    print("=" * 80)

    categories = analysis_result["categories"]
    domain_stats = analysis_result["domain_stats"]
    content_type_stats = analysis_result["content_type_stats"]

    # По категориям
    print(f"\nЗАПРОСЫ ПО КАТЕГОРИЯМ:")
    print("-" * 40)
    for category, requests in categories.items():
        if requests:
            print(f"{category.upper()}: {len(requests)} запросов")

    # Топ доменов
    print(f"\nТОП-15 ДОМЕНОВ ПО КОЛИЧЕСТВУ ЗАПРОСОВ:")
    print("-" * 40)
    sorted_domains = sorted(domain_stats.items(), key=lambda x: x[1], reverse=True)[:15]
    for domain, count in sorted_domains:
        print(f"{domain:<40} {count:>5}")

    # Content-Type
    print(f"\nТОП-10 CONTENT-TYPE:")
    print("-" * 40)
    sorted_ct = sorted(content_type_stats.items(), key=lambda x: x[1], reverse=True)[
        :10
    ]
    for ct, count in sorted_ct:
        print(f"{ct:<40} {count:>5}")


def print_auth_analysis(analysis_result: Dict[str, Any]):
    """Выводит анализ авторизации"""
    auth_requests = analysis_result["categories"]["auth"]
    if not auth_requests:
        print("\n❌ Запросы авторизации не найдены")
        return

    auth_analysis = analyze_auth_flow(auth_requests)

    print("\n" + "=" * 80)
    print("АНАЛИЗ АВТОРИЗАЦИИ")
    print("=" * 80)

    print(f"\nВсего запросов авторизации: {auth_analysis['total_auth_requests']}")
    print(f"Домены авторизации: {', '.join(auth_analysis['auth_domains'])}")

    if auth_analysis["auth_methods"]:
        print(f"\nМетоды авторизации:")
        for method in auth_analysis["auth_methods"]:
            print(f"  - {method}")

    if auth_analysis["token_sources"]:
        print(f"\nИсточники токенов:")
        for source in auth_analysis["token_sources"][:5]:
            print(f"  - {source['param']}: {source['value_preview']}")

    if auth_analysis["auth_sequence"]:
        print(f"\nПоследовательность авторизации (первые 10 шагов):")
        for i, step in enumerate(auth_analysis["auth_sequence"]):
            print(f"  {i+1}. {step['method']} {step['path']} ({step['domain']})")


def print_audio_analysis(analysis_result: Dict[str, Any]):
    """Выводит анализ аудио доменов"""
    all_requests = []
    for requests in analysis_result["categories"].values():
        all_requests.extend(requests)

    audio_analysis = analyze_audio_domains(all_requests)

    if not audio_analysis:
        print("\n❌ Аудио домены не найдены")
        return

    print("\n" + "=" * 80)
    print("АНАЛИЗ АУДИО ДОМЕНОВ")
    print("=" * 80)

    for domain, data in audio_analysis.items():
        print(f"\n{domain}:")
        print(f"  Запросов: {data['request_count']}")
        print(f"  Типы файлов: {', '.join(data['file_types'])}")
        print(f"  Общий размер: {data['total_size_mb']} MB")
        print(f"  Статусы: {', '.join(map(str, data['status_codes']))}")

        if data["sample_urls"]:
            print(f"  Примеры URL:")
            for url in data["sample_urls"][:2]:
                print(f"    - {url[:100]}...")


def print_patterns_analysis(analysis_result: Dict[str, Any]):
    """Выводит анализ паттернов"""
    all_requests = []
    for requests in analysis_result["categories"].values():
        all_requests.extend(requests)

    patterns = find_request_patterns(all_requests)

    if not patterns:
        print("\n❌ Паттерны не найдены")
        return

    print("\n" + "=" * 80)
    print("АНАЛИЗ ПАТТЕРНОВ ЗАПРОСОВ")
    print("=" * 80)

    for i, pattern in enumerate(patterns[:5]):
        print(f"\nПаттерн {i+1}: {pattern['type']}")
        print(
            f"  API запрос: {pattern['api_request']['method']} {pattern['api_request']['url']}"
        )
        print(f"  Последующие аудио запросы:")
        for audio in pattern["audio_requests"]:
            print(f"    - {audio['domain']} (задержка: {audio['delay_ms']}мс)")


def main():
    parser = argparse.ArgumentParser(description="Универсальный анализатор трафика")
    parser.add_argument("flow_file", help="Путь к flow файлу")
    parser.add_argument("--output", "-o", help="Сохранить результаты в JSON файл")
    parser.add_argument(
        "--auth", "-a", action="store_true", help="Показать анализ авторизации"
    )
    parser.add_argument(
        "--audio", "-s", action="store_true", help="Показать анализ аудио"
    )
    parser.add_argument(
        "--patterns", "-p", action="store_true", help="Показать анализ паттернов"
    )
    parser.add_argument("--all", "-l", action="store_true", help="Показать весь анализ")

    args = parser.parse_args()

    flow_file = Path(args.flow_file)
    if not flow_file.exists():
        print(f"Файл не найден: {flow_file}")
        sys.exit(1)

    print(f"🌍 Универсальный анализ трафика из flow файла: {flow_file}")

    analysis_result = extract_all_requests(str(flow_file))

    if not analysis_result:
        print("❌ Не найдено запросов")
        sys.exit(1)

    # Базовый анализ
    print_domain_analysis(analysis_result)

    # Детальный анализ по флагам
    if args.auth or args.all:
        print_auth_analysis(analysis_result)

    if args.audio or args.all:
        print_audio_analysis(analysis_result)

    if args.patterns or args.all:
        print_patterns_analysis(analysis_result)

    # Сохраняем результаты если указан выходной файл
    if args.output:
        output_file = Path(args.output)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n💾 Результаты сохранены в: {output_file}")


if __name__ == "__main__":
    main()
