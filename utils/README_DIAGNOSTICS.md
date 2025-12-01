# VK API Diagnostics Usage Guide

## Краткая инструкция по диагностике проблемы аутентификации VK

### 🚨 Текущий статус: ТЕНЕВОЙ БАН VK

**Проблема**: VK заблокировал сочетание IP + client ID/secret
**Статус**: HTTP 401 Unauthorized + "Password bruteforce attempt!"
**Решение**: Ожидание разбана (от часов до дней) или смена IP/VPN

---

## 📋 Как использовать диагностический скрипт

### Шаг 1: Запуск диагностики
```bash
cd /workspace
python utils/debug_vk_simple.py
```

### Шаг 2: Ввод учетных данных
- Ввести VK login при запросе
- Ввести VK password при запросе
- Дождаться завершения скрипта

### Шаг 3: Анализ результатов
- Проверить статус аутентификации в консоли
- Открыть `debug_vk_simple.log` для детальной информации

---

## 🔍 Интерпретация результатов

### ✅ Успешная аутентификация
```
HTTP Request: POST https://oauth.vk.com/token "HTTP/1.1 200 OK"
✅ Authentication reported SUCCESS!
Token: vk1.a....
```

### ❌ Теневой бан (текущая проблема)
```
HTTP Request: POST https://oauth.vk.com/token "HTTP/1.1 401 Unauthorized"
❌ Authentication FAILED!
Password bruteforce attempt!
```

### 📸 Требуется капча
```
📸 Captcha required!
Captcha URL: https://api.vk.com/captcha.php?sid=...
```

### 📱 Требуется 2FA
```
Enter 2FA code from SMS/app:
```

---

## 📊 Анализ логов (debug_vk_simple.log)

### Ключевые маркеры:
- **HTTP Status**: 200 = успех, 401 = бан, 400 = ошибка параметров
- **Server**: kittenx = стандартная VK инфраструктура
- **X-Powered-By**: KPHP/7.4.* = VK backend
- **X-Frontend**: frontXXXXXX = конкретный сервер VK
- **Set-Cookie remixir=DELETED**: попытка сброса сессии

---

## ⏰ План действий

### Во время бана:
1. **Периодически проверять**: запускать скрипт каждые 2-4 часа
2. **Следить за статусом**: ждать смены 401 на 200
3. **Альтернативы**: VPN, смена IP, ожидание

### После разбана:
1. **Проверить аутентификацию**: запустить `debug_vk_simple.py`
2. **Протестировать интеграцию**: `python utils/test_vk_correct_integration.py`
3. **Проверить web интерфейс**: http://localhost:6680/vkm/
4. **Адаптировать тесты**: обновить unit тесты
5. **Удалить утилиты**: очистить `utils/` папку

---

## 📁 Файлы диагностики

- `utils/debug_vk_simple.py` - основной диагностический скрипт
- `debug_vk_simple.log` - лог последнего запуска
- `debug_token_simple.txt` - сохраненный токен (если успех)
- `utils/debug_analysis.md` - полный анализ проблемы
- `utils/README_DIAGNOSTICS.md` - эта инструкция

---

## 🆘 Частые вопросы

**Q: Как долго длится бан?**
A: От нескольких часов до нескольких дней, зависит от VK

**Q: Поможет ли VPN?**
A: Да, смена IP может обойти бан, но может сработать fingerprint detection

**Q: Можно ли использовать другой client?**
A: Теоретически да, но нужно найти рабочий client ID/secret

**Q: Как проверить что бан снят?**
A: Запустить `debug_vk_simple.py` и посмотреть на HTTP статус
