# Результаты трассировки токенов VK

## Ключевые находки

### Обнаруженные токены и их характеристики

| Токен | Длина | Использований | Уникальных значений | Изменяется | Домены |
|-------|-------|--------------|-------------------|-----------|--------|
| **httoken** | 132 | 306 | 1 | Нет | api.vk.com, vk.com, id.vk.com, login.vk.com |
| **remixsid** | 88 | 263 | 3 | Да | api.vk.com, vk.com, login.vk.com |
| **remixnsid** | 198 | 122 | 1 | Нет | vk.com |
| **remixdmgr** | 64 | 258 | 2 | Да | api.vk.com, vk.com, login.vk.com |
| **remixdmgr_tmp** | 64 | 262 | 1 | Нет | api.vk.com, vk.com, login.vk.com |
| **remixuas** | 32 | 307 | 1 | Нет | api.vk.com, vk.com, id.vk.com, login.vk.com |
| **remixuacck** | 18 | 306 | 1 | Нет | api.vk.com, vk.com, id.vk.com, login.vk.com |
| **domain_sid** | 37 | 130 | 1 | Нет | vk.com |
| **remixnreg_sid** | 32 | 29 | 1 | Нет | api.vk.com, login.vk.com |

### Паттерны использования токенов

#### Для API запросов (api.vk.com/method/*):
- **Обязательные**: httoken, remixdmgr, remixdmgr_tmp, remixsid, remixuacck, remixuas
- **Опциональные**: remixnreg_sid
- **Не используются**: domain_sid, remixnsid

#### Для AL запросов (vk.com/al_*):
- **Обязательные**: httoken, remixdmgr, remixdmgr_tmp, remixnsid, remixsid, remixuacck, remixuas
- **Опциональные**: domain_sid
- **Не используются**: remixnreg_sid

#### Критические токены (используются везде):
- **httoken** - основной токен для всех запросов
- **remixdmgr** - управление устройствами
- **remixdmgr_tmp** - временное управление устройствами
- **remixsid** - сессионный идентификатор
- **remixuacck** - аккаунт cookie
- **remixuas** - пользовательская сессия

### Временная линия появления токенов

1. **19:44:51** - Первые токены при загрузке usefull.php:
   - httoken
   - remixuas
   - remixuacck
   - domain_sid

2. **19:45:17** - Аутентификация API:
   - remixnreg_sid (только для API)

3. **19:45:55-56** - Полная аутентификация:
   - remixsid (меняется 3 раза за сессию)
   - remixnsid (только для vk.com)
   - remixdmgr (меняется 2 раза за сессию)
   - remixdmgr_tmp

## Гипотеза по назначению токенов

### Основная группа (критические):
- **httoken**: HTTP токен для всех запросов, аналог access_token
- **remixsid**: Сессионный ID, может обновляться в процессе сессии
- **remixuas**: Пользовательская сессия, стабильная
- **remixuacck**: Аккаунт cookie, стабильная

### Управление устройствами:
- **remixdmgr**: Основной токен управления устройствами, обновляется
- **remixdmgr_tmp**: Временный токен управления устройствами, стабильный

### Специализированные:
- **remixnsid**: Навигационный сессионный ID (только vk.com)
- **domain_sid**: Доменный сессионный ID (только vk.com)
- **remixnreg_sid**: Токен для регистрации/анонимных запросов API

## Минимальные наборы токенов

### Для API.vk.com запросов:
```
httoken + remixsid + remixuas + remixuacck + remixdmgr + remixdmgr_tmp
```

### Для vk.com/al_* запросов:
```
httoken + remixsid + remixuas + remixuacck + remixdmgr + remixdmgr_tmp + remixnsid
```

### Универсальный набор (для всего):
```
httoken + remixsid + remixuas + remixuacck + remixdmgr + remixdmgr_tmp + remixnsid + domain_sid
```

## Стратегия имперсонации браузера

### Шаг 1: Получение базовых токенов
- httoken, remixuas, remixuacck, domain_sid появляются при первом визите

### Шаг 2: Аутентификация
- remixnreg_sid для API анонимных запросов
- remixsid, remixnsid, remixdmgr, remixdmgr_tmp после логина

### Шаг 3: Выбор правильного набора
- Для API методов: набор без remixnsid
- Для AL методов: набор с remixnsid
- Для универсальности: полный набор

## Практическое применение

### Cookie-based API класс:
```python
class VKCookieAPI:
    def __init__(self, cookies):
        self.httoken = cookies.get('httoken')
        self.remixsid = cookies.get('remixsid')
        self.remixuas = cookies.get('remixuas')
        self.remixuacck = cookies.get('remixuacck')
        self.remixdmgr = cookies.get('remixdmgr')
        self.remixdmgr_tmp = cookies.get('remixdmgr_tmp')
        self.remixnsid = cookies.get('remixnsid')
```

### Методы для разных типов запросов:
- `api_request()` - использует токены для API.vk.com
- `al_request()` - использует токены для vk.com/al_*
- `universal_request()` - автоматически выбирает нужный набор

## Следующие шаги

1. **Создать CookieAPI класс** с правильными наборами токенов
2. **Тестировать с реальными токенами** из захваченной сессии
3. **Реализовать обновление токенов** (remixsid, remixdmgr меняются)
4. **Создать unified интерфейс** который выбирает правильный метод
5. **Интегрировать с existing mopidy_vkm** архитектурой

## Выводы

VK использует сложную систему cookie-based аутентификации с несколькими уровнями токенов. Ключевое понимание:

- **httoken** - это основной токен, аналог access_token
- **remixsid** - сессионный ID, может обновляться
- **Разные наборы токенов** для разных типов эндпоинтов
- **6 критических токенов** необходимы для полной функциональности

Это полностью меняет подход к имперсонации браузера - нужно работать с cookies, а не с одиночным access_token.
