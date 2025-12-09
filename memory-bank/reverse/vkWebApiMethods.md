# VK Web API Methods - Результаты анализа трафика

## Обзор

На основе анализа трафика через mitmproxy с Firefox + uBlock были определены актуальные веб-методы VK API, которые используются для работы с аудио и плейлистами.

## Ключевые находки

### 1. Аудио CDN домены
- `cs1-82v4.vkuseraudio.net`
- `cs9-20v4.vkuseraudio.net`
- `cs1-63v4.vkuseraudio.net`

Эти домены используются для доставки аудио файлов. URL имеют формат:
```
https://cs1-82v4.vkuseraudio.net/s/v1/ac/[encoded_path]
```

### 2. Основные API методы

#### Авторизация
- `POST /method/auth.validateAccount` - валидация аккаунта
- `POST /method/auth.getAuthCode` - получение auth кода
- `POST /method/auth.checkAuthCode` - проверка auth кода
- `GET /auth` - базовая авторизация
- `POST /method/eventHub.getToken` - получение токена для событий

#### Аудио и плейлисты
- `POST /method/audio.getIdsBySource` - получение ID аудио по источнику
- `POST /method/audio.getPlaylistById` - получение плейлиста по ID
- `POST /method/audio.getById` - получение аудио по ID
- `POST /method/audio.getEditableGroups` - получение редактируемых групп

#### AL методы (внутренние)
- `POST /al_audio.php?act=reload_audios` - перезагрузка аудио
- `POST /al_audio.php?act=get_audio_ids_by_source` - получение ID аудио из источника
- `POST /al_audio.php?act=status_tt` - статус аудио сервиса
- `POST /al_audio.php?act=queue_params` - параметры очереди
- `POST /al_audio.php?act=start_playback` - начало воспроизведения
- `POST /al_audio.php?act=audio_status` - статус аудио
- `POST /al_audio.php?act=ad_event` - события рекламы
- `POST /al_audio.php?act=listened_data` - статистика прослушивания

#### Закладки
- `POST /al_bookmarks.php` - работа с закладками

### 3. Паттерны использования

#### Последовательность воспроизведения
1. `al_audio.php?act=reload_audios` → получение аудио данных
2. `al_audio.php?act=queue_params` → параметры очереди воспроизведения
3. `al_audio.php?act=start_playback` → начало воспроизведения
4. Запрос к `vkuseraudio.net` → загрузка аудио файла
5. `al_audio.php?act=audio_status` → обновление статуса
6. `al_audio.php?act=listened_data` → статистика прослушивания

#### Авторизация
1. `GET /auth` → начальная страница авторизации
2. `GET /vkid/1.1.1269/auth.css` и `/auth.js` → загрузка UI
3. `POST /method/auth.validateAccount` → валидация
4. `POST /method/auth.getAuthCode` → получение кода
5. `POST /method/auth.checkAuthCode` → проверка кода (множественные вызовы)

### 4. Параметры для реверс-инжиниринга

#### Client ID
- `6287487` - для основных API методов
- `7913379` - для авторизации

#### Версии API
- `5.268` - основная версия
- `5.267` - для execute методов
- `5.258` - для авторизации

#### Ключевые параметры
- `access_token` - веб-токен
- `client_id` - ID клиента
- `v` - версия API
- `act` - действие для AL методов
- `owner_id` - ID владельца
- `playlist_id` - ID плейлиста
- `audio_ids` - ID аудио
- `hash` - хеш для валидации

### 5. Токены аутентификации

#### Веб-токен
```
auth_token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzaWQiOiJNR...
```

#### Вспомогательные токены
```
anonymous_token: anonym.eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhbm...
auth_hash: 3eef78ba140211d6319e55e06a51a48648b1
web_auth: 1
```

### 6. WebSocket соединения
- `eh.vk.com:443/?v=1.000&format=json&app_id=6287487`
- Используется для реального времени событий

## Реализация для mopidy_vkm

### 1. Валидация токена
```python
async def validate_web_token(token: str) -> bool:
    """Валидация веб-токена через audio.getById"""
    params = {
        'access_token': token,
        'audios': '1_1',  # тестовый аудио
        'v': '5.268',
        'client_id': '6287487'
    }

    response = await make_request('POST', '/method/audio.getById', params)
    return response.get('response') is not None
```

### 2. Получение информации о профиле
```python
async def get_profile_info(token: str) -> dict:
    """Информация о профиле через execute"""
    code = '''
    var res1 = API.users.get({"fields": "id,first_name,last_name,photo_100"});
    var res2 = API.account.getProfileInfo({});
    return [res1, res2];
    '''

    params = {
        'access_token': token,
        'code': code,
        'v': '5.267',
        'client_id': '6287487'
    }

    response = await make_request('POST', '/method/execute', params)
    return response.get('response', [])
```

### 3. Получение плейлиста
```python
async def get_playlist_by_id(token: str, owner_id: str, playlist_id: str) -> dict:
    """Получение плейлиста по ID"""
    params = {
        'access_token': token,
        'owner_id': owner_id,
        'playlist_id': playlist_id,
        'extra_fields': 'count,description,is_following',
        'v': '5.268',
        'client_id': '6287487'
    }

    response = await make_request('POST', '/method/audio.getPlaylistById', params)
    return response.get('response', {})
```

### 4. Получение аудио из закладок
```python
async def get_bookmark_audio(token: str) -> list:
    """Получение аудио из закладок через AL метод"""
    params = {
        'act': 'get_audio_ids_by_source',
        'al': '1',
        'block_id': 'bookmarks_audio',  # нужно уточнить
        'access_token': token,
        'v': '5.268'
    }

    response = await make_request('POST', '/al_audio.php', params)
    return response.get('payload', {}).get('list', [])
```

### 5. Воспроизведение аудио
```python
async def start_playback(token: str, owner_id: str, audio_id: str) -> dict:
    """Начало воспроизведения аудио"""
    # Сначала получаем параметры очереди
    queue_params = await get_queue_params(token, owner_id, audio_id)

    # Затем начинаем воспроизведение
    params = {
        'act': 'start_playback',
        'al': '1',
        'audio_id': f'{owner_id}_{audio_id}',
        'owner_id': owner_id,
        'hash': queue_params.get('hash'),
        'uuid': generate_uuid(),
        'access_token': token
    }

    response = await make_request('POST', '/al_audio.php', params)
    return response.get('payload', {})
```

## Следующие шаги

### 1. Тестирование методов
- Реализовать базовые функции
- Протестировать с найденным токеном
- Проверить работу с разными типами контента

### 2. Обработка ошибок
- Обработка истечения токена
- Обработка недостатка прав
- Обработка блокировок

### 3. Интеграция с mopidy_vkm
- Адаптация существующей архитектуры
- Замена vkpymusic на веб-методы
- Тестирование в реальном окружении

## Выводы

1. **Веб-токены работают** с актуальными методами API
2. **Аудио CDN** используют временные URL с хешами
3. **AL методы** предоставляют больше функциональности чем старые API
4. **Авторизация** требует несколько шагов с разными токенами
5. **WebSocket** используется для реального времени

Это подтверждает гипотезу о том, что vkpymusic использует устаревшие методы, а веб-интерфейс использует новые API, которые работают с веб-токенами.

---
*Анализ выполнен на основе трафика от 2025-12-08*
*Статус: Методы определены, требуется реализация*
