#!/usr/bin/env python3
"""
Анализатор токенов VK из захваченного трафика
Извлекает и трассирует токены из cookies для понимания структуры аутентификации
"""

import json
import sys
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any, Set, Tuple


def extract_tokens_from_cookies(cookie_string: str) -> Dict[str, str]:
    """Извлекает все потенциальные токены из строки cookies"""
    tokens = {}
    if not cookie_string:
        return tokens

    for cookie in cookie_string.split(", "):
        if "=" in cookie:
            key, value = cookie.split("=", 1)
            # Ищем ключевые слова в названиях cookies
            if any(
                keyword in key.lower()
                for keyword in ["token", "sid", "nsid", "dmgr", "uas", "uacck"]
            ):
                tokens[key.strip()] = value.strip()
    return tokens


def analyze_token_timeline(log_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Анализирует когда появляются какие токены"""
    timeline = []

    # Проходим по всем категориям в логах
    for category, requests in log_data.get("categories", {}).items():
        for entry in requests:
            if "request_headers" in entry and "cookie" in entry["request_headers"]:
                cookies = entry["request_headers"]["cookie"]
                tokens = extract_tokens_from_cookies(cookies)

                if tokens:  # Только если есть токены
                    timeline.append(
                        {
                            "timestamp": entry.get("timestamp", 0),
                            "url": entry.get("url", ""),
                            "method": entry.get("method", "GET"),
                            "domain": entry.get("domain", ""),
                            "path": entry.get("path", ""),
                            "category": category,
                            "tokens": tokens,
                            "all_cookies": cookies[:100] + "..."
                            if len(cookies) > 100
                            else cookies,
                        }
                    )

    # Сортируем по времени
    timeline.sort(key=lambda x: x["timestamp"])
    return timeline


def analyze_token_appearance(timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Анализирует порядок появления токенов"""
    token_first_seen = {}
    token_usage_counter = Counter()
    token_domains = defaultdict(set)
    token_categories = defaultdict(set)

    for entry in timeline:
        for token_name, token_value in entry["tokens"].items():
            # Первое появление токена
            if token_name not in token_first_seen:
                token_first_seen[token_name] = {
                    "timestamp": entry["timestamp"],
                    "url": entry["url"],
                    "domain": entry["domain"],
                    "category": entry["category"],
                }

            # Счетчик использования
            token_usage_counter[token_name] += 1

            # Домены и категории использования
            token_domains[token_name].add(entry["domain"])
            token_categories[token_name].add(entry["category"])

    return {
        "first_seen": token_first_seen,
        "usage_count": dict(token_usage_counter),
        "domains": {k: list(v) for k, v in token_domains.items()},
        "categories": {k: list(v) for k, v in token_categories.items()},
    }


def analyze_token_dependencies(timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Определяет зависимости между токенами и типами запросов"""
    dependencies = {}

    for entry in timeline:
        url = entry["url"]
        tokens = list(entry["tokens"].keys())

        # Классифицируем тип запроса
        if "api.vk.com/method" in url:
            request_type = "api_method"
        elif "vk.com/al_" in url:
            request_type = "al_endpoint"
        elif "oauth.vk.com" in url:
            request_type = "oauth"
        elif "id.vk.com" in url:
            request_type = "auth"
        else:
            request_type = "other"

        dependencies[url] = {
            "required_tokens": tokens,
            "token_count": len(tokens),
            "request_type": request_type,
            "domain": entry["domain"],
            "category": entry["category"],
            "timestamp": entry["timestamp"],
        }

    return dependencies


def find_token_patterns(timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Ищет паттерны в использовании токенов"""
    patterns = {"api_requests": [], "al_requests": [], "auth_requests": []}

    for entry in timeline:
        tokens = entry["tokens"]
        url = entry["url"]

        if "api.vk.com/method" in url:
            patterns["api_requests"].append(
                {
                    "url": url,
                    "tokens": list(tokens.keys()),
                    "timestamp": entry["timestamp"],
                }
            )
        elif "vk.com/al_" in url:
            patterns["al_requests"].append(
                {
                    "url": url,
                    "tokens": list(tokens.keys()),
                    "timestamp": entry["timestamp"],
                }
            )
        elif any(auth_domain in url for auth_domain in ["oauth.vk.com", "id.vk.com"]):
            patterns["auth_requests"].append(
                {
                    "url": url,
                    "tokens": list(tokens.keys()),
                    "timestamp": entry["timestamp"],
                }
            )

    return patterns


def analyze_token_values(timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Анализирует значения токенов для поиска паттернов"""
    token_values = defaultdict(list)

    for entry in timeline:
        for token_name, token_value in entry["tokens"].items():
            token_values[token_name].append(
                {
                    "value": token_value,
                    "timestamp": entry["timestamp"],
                    "url": entry["url"],
                }
            )

    # Ищем уникальные значения и паттерны
    analysis = {}
    for token_name, values in token_values.items():
        unique_values = set(v["value"] for v in values)
        analysis[token_name] = {
            "total_usages": len(values),
            "unique_values": len(unique_values),
            "value_changes": len(unique_values) > 1,
            "first_value": values[0]["value"] if values else None,
            "value_length": len(values[0]["value"]) if values else 0,
            "value_prefix": values[0]["value"][:20] + "..."
            if values and len(values[0]["value"]) > 20
            else values[0]["value"]
            if values
            else None,
        }

    return analysis


def main():
    if len(sys.argv) != 2:
        print("Usage: python token_analyzer.py <log_file.json>")
        sys.exit(1)

    log_file = sys.argv[1]

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            log_data = json.load(f)
    except Exception as e:
        print(f"Error loading log file: {e}")
        sys.exit(1)

    print("🔍 Analyzing VK tokens from captured traffic...")

    # Анализ временной линии
    timeline = analyze_token_timeline(log_data)
    print(f"📊 Found {len(timeline)} requests with tokens")

    # Анализ появления токенов
    appearance = analyze_token_appearance(timeline)
    print(f"\n🎯 Token appearance analysis:")
    for token_name, info in sorted(appearance["first_seen"].items()):
        print(f"  {token_name}:")
        print(f"    First seen: {datetime.fromtimestamp(info['timestamp'])}")
        print(f"    URL: {info['url']}")
        print(f"    Usage count: {appearance['usage_count'][token_name]}")
        print(f"    Domains: {', '.join(appearance['domains'][token_name])}")
        print(f"    Categories: {', '.join(appearance['categories'][token_name])}")
        print()

    # Анализ зависимостей
    dependencies = analyze_token_dependencies(timeline)

    # Анализ паттернов
    patterns = find_token_patterns(timeline)
    print(f"🔗 Request patterns:")
    print(f"  API requests: {len(patterns['api_requests'])}")
    print(f"  AL requests: {len(patterns['al_requests'])}")
    print(f"  Auth requests: {len(patterns['auth_requests'])}")

    # Показываем примеры для каждого типа
    if patterns["api_requests"]:
        print(f"\n  API request example:")
        example = patterns["api_requests"][0]
        print(f"    URL: {example['url']}")
        print(f"    Tokens: {', '.join(example['tokens'])}")

    if patterns["al_requests"]:
        print(f"\n  AL request example:")
        example = patterns["al_requests"][0]
        print(f"    URL: {example['url']}")
        print(f"    Tokens: {', '.join(example['tokens'])}")

    # Анализ значений токенов
    value_analysis = analyze_token_values(timeline)
    print(f"\n💎 Token value analysis:")
    for token_name, info in value_analysis.items():
        print(f"  {token_name}:")
        print(f"    Total usages: {info['total_usages']}")
        print(f"    Unique values: {info['unique_values']}")
        print(f"    Changes over time: {info['value_changes']}")
        print(f"    Value length: {info['value_length']}")
        print(f"    Value prefix: {info['value_prefix']}")
        print()

    # Сохраняем детальный анализ
    output_file = log_file.replace(".json", "_token_analysis.json")
    analysis_result = {
        "timeline": timeline,
        "appearance": appearance,
        "dependencies": dependencies,
        "patterns": patterns,
        "value_analysis": value_analysis,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, indent=2, ensure_ascii=False)

    print(f"📁 Detailed analysis saved to: {output_file}")

    # Ключевые выводы
    print(f"\n🎯 Key findings:")

    # Какие токены нужны для разных типов запросов
    api_tokens = set()
    al_tokens = set()

    for req in patterns["api_requests"]:
        api_tokens.update(req["tokens"])

    for req in patterns["al_requests"]:
        al_tokens.update(req["tokens"])

    print(f"  Tokens used in API requests: {', '.join(sorted(api_tokens))}")
    print(f"  Tokens used in AL requests: {', '.join(sorted(al_tokens))}")

    # Критические токены (используются в обоих типах)
    critical_tokens = api_tokens.intersection(al_tokens)
    print(f"  Critical tokens (both API and AL): {', '.join(sorted(critical_tokens))}")


if __name__ == "__main__":
    main()
