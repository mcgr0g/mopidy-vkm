# VK Reverse Engineering Documentation

## Overview

Этот раздел содержит документацию и анализ реверс-инжиниринга веб API VK для понимания того, как правильно аутентифицироваться и получать доступ к музыкальным функциям без использования устаревших библиотек вроде vkpymusic.

## Ключевые находки

### 🎯 Основная гипотеза
VK использует разные механизмы аутентификации для разных типов запросов:
- **API запросы** (api.vk.com/method/*) используют access tokens
- **Web запросы** (vk.com/al_*) используют cookie-based аутентификацию
- **Audio CDN** (*.vkuseraudio.net) используют временные подписанные URL

### 📊 Результаты анализа

#### Захват трафика
- **Инструмент**: mitmproxy с Firefox + uBlock Origin
- **Длительность**: Полная сессия пользователя от логина до воспроизведения музыки
- **Захваченные домены**: api.vk.com, vk.com, *.vkuseraudio.net

#### Ключевые обнаруженные API методы
- **Авторизация**: `auth.validateAccount`, `auth.getAuthCode`, `auth.checkAuthCode`
- **Аудио/Плейлисты**: `audio.getIdsBySource`, `audio.getPlaylistById`, `audio.getById`
- **AL методы**: `al_audio.php` с различными параметрами `act`
- **Закладки**: `al_bookmarks.php`

## Структура документации

### 📋 Планирование и настройка
- [`mitmproxyConfig.md`](mitmproxyConfig.md) - Конфигурация прокси для захвата трафика
- [`testRun.md`](testRun.md) - Процедуры и результаты тестовых запусков
- [`troubleshooting.md`](troubleshooting.md) - Частые проблемы и решения

### 🔍 Анализ и результаты
- [`vkWebApiMethods.md`](vkWebApiMethods.md) - Полная документация обнаруженных API методов
- [`tokenTracingResults.md`](tokenTracingResults.md) - Анализ cookie токенов и паттернов

### 📈 Следующие шаги
- [`nextSteps.md`](nextSteps.md) - План реализации и оставшиеся задачи

## Статус реализации

### ✅ Завершено
1. **Настройка захвата трафика**
   - Сконфигурирован mitmproxy для комплексного логирования
   - Успешно захвачен полный трафик сессии VK
   - Идентифицированы все релевантные домены и эндпоинты

2. **Обнаружение API методов**
   - Сопоставлен поток аутентификации
   - Документированы методы аудио/плейлистов
   - Идентифицированы эндпоинты обработки закладок

3. **Анализ токенов**
   - Обнаружена cookie-based аутентификация
   - Сопоставлены зависимости токенов
   - Идентифицированы критические и опциональные токены

### 🔄 В процессе
1. **Реализация Cookie-based API**
   - Создание класса VKCookieAPI
   - Реализация правильного управления токенами
   - Тестирование с захваченными токенами

### ⏳ Ожидается
1. **Интеграция с mopidy_vkm**
   - Замена зависимостей vkpymusic
   - Реализация web-based аутентификации
   - Тестирование полного рабочего процесса воспроизведения музыки

## Техническая архитектура

### Поток аутентификации
```
1. Первоначальный визит → Базовые cookies (remixuas, remixuacck)
2. Процесс логина → Сессионные токены (remixsid, remixnsid)
3. Доступ к API → HTTP токены (httoken)
4. Воспроизведение аудио → CDN URL с подписями
```

### Типы токенов
- **httoken**: Основной HTTP токен для всех запросов
- **remixsid**: ID сессии (может обновляться в процессе сессии)
- **remixnsid**: ID навигационной сессии (только vk.com)
- **remixuas**: Пользовательская сессия (стабильный)
- **remixuacck**: Аккаунт cookie (стабильный)
- **remixdmgr**: Токены управления устройствами

## Примеры использования

### Использование Cookie-based API
```python
from src.mopidy_vkm.auth.cookie_api import VKCookieAPI, VKCookies

# Извлечение cookies из захваченного трафика
cookies = VKCookies.from_cookie_string(captured_cookie_string)

# Использование cookie-based API
async with VKCookieAPI(cookies) as api:
    # Получение профиля пользователя
    profile = await api.get_profile_info()

    # Получение закладок
    bookmarks = await api.get_bookmarks()

    # Получение плейлиста
    playlist = await api.get_playlist_by_id(playlist_id)
```

## Инструменты и утилиты

### Инструменты анализа
- `utils/universal_traffic_analyzer.py` - Комплексный анализ трафика
- `utils/token_analyzer.py` - Трассировка и анализ cookie токенов

### Файлы конфигурации
- `utils/mitmproxy_config.json` - Конфигурация mitmproxy
- `logs/vk_universal_analysis.json` - Данные захваченного трафика

### Основные компоненты
- `src/mopidy_vkm/auth/cookie_api.py` - VK Cookie API реализация
- `test_cookie_api.py` - Тестовый скрипт для проверки функциональности

## 📚 Детальная документация

| Документ | Назначение | Статус |
|----------|------------|--------|
| [`mitmproxyConfig.md`](./mitmproxyConfig.md) | Конфигурация прокси | ✅ Готов |
| [`testRun.md`](./testRun.md) | Тестовый запуск прокси | ✅ Готов |
| [`troubleshooting.md`](./troubleshooting.md) | Устранение проблем | ✅ Готов |
| [`vkWebApiMethods.md`](./vkWebApiMethods.md) | API методы VK | ✅ Готов |
| [`tokenTracingResults.md`](./tokenTracingResults.md) | Анализ токенов | ✅ Готов |
| [`nextSteps.md`](./nextSteps.md) | Следующие шаги | ✅ Готов |

## 🔗 Связанные документы

- [`../hypothesisSession.md`](../hypothesisSession.md) - Исходная гипотеза
- [`../activeContext.ad`](../activeContext.ad) - Текущий контекст проекта
- [`../techContext.ad`](../techContext.ad) - Технический контекст

## 📂 Структура файлов

```
memory-bank/reverse/
├── README.md                    # ← Этот файл (точка входа)
├── mitmproxyConfig.md          # Конфигурация
├── testRun.md                 # Тестовый запуск
├── troubleshooting.md         # Устранение проблем
├── vkWebApiMethods.md        # API методы
├── tokenTracingResults.md    # Анализ токенов
└── nextSteps.md               # Следующие шаги

utils/
├── universal_traffic_analyzer.py  # Анализатор трафика
├── token_analyzer.py           # Анализатор токенов
└── mitmproxy_config.json      # Конфигурация mitmproxy

src/
└── mopidy_vkm/auth/
    └── cookie_api.py           # VK Cookie API реализация

logs/
└── vk_universal_analysis.json   # Захваченные данные
```

## ⚠️ Важные замечания

- **Порт прокси:** 8080 (стандартный для mitmproxy)
- **Директория логов:** `logs/`
- **Инструмент:** mitmproxy (с интерфейсом)
- **Сертификаты:** Используются стандартные `~/.mitmproxy`

## 🔄 Текущий статус

- **Этап 1:** Подготовка инфраструктуры - ✅ Завершен
- **Этап 2:** Захват трафика - ✅ Завершен
- **Этап 3:** Анализ API вызовов - ✅ Завершен
- **Этап 4:** Реализация - 🔄 В процессе (требует доработки)

## 🎯 Что делать прямо сейчас

1. **Изучить:** [`tokenTracingResults.md`](./tokenTracingResults.md) - результаты анализа токенов
2. **Использовать:** `utils/token_analyzer.py` для анализа новых сессий
3. **Реализовать:** Cookie-based API на основе найденных паттернов
4. **Тестировать:** `utils/test_cookie_api.py` для проверки функциональности

---
*Последнее обновление: 2025-12-08*
*Статус: Анализ завершен, реализация в процессе*
