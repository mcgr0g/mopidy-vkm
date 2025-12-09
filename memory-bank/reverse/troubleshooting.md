# Устранение проблем с mitmproxy

## 🐛 Обнаруженные проблемы

1. **Неправильный порт:** mitmdump запустился на 8080 вместо 6800
2. **Ошибка сертификата:** PR_END_OF_FILE_ERROR в Firefox
3. **Конфигурация не применяется:** mitmdump игнорирует YAML файл

## 🔧 Решения

### Проблема 1: Неправильный порт

**Причина:** mitmdump не читает конфигурационный файл правильно

**Решение:** Явно указать порт в командной строке:

```bash
# Правильная команда с явным указанием порта
mitmdump \
  --set confdir=config/mitmproxy \
  --set listen_port=6680 \
  --set listen_host=0.0.0.0 \
  --set flow_detail=3 \
  -w logs/test_run_$(date +%Y%m%d_%H%M%S).flow
```

### Проблема 2: Ошибка сертификата в Firefox

**Причина:** Сертификат mitmproxy не правильно установлен или не доверенный

**Решение:**

1. **Проверить установку сертификата:**
   ```bash
   # Проверить что сертификат существует
   ls -la ~/.mitmproxy/mitmproxy-ca-cert.pem

   # Проверить что сертификат в конфиге
   cat config/mitmproxy.yaml | grep certs
   ```

2. **Переустановить сертификат в Firefox:**
   - Открыть Firefox → Настройки → Приватность и защита → Сертификаты
   - Просмотр сертификатов → Центры сертификации → Импортировать
   - Выбрать файл: `~/.mitmproxy/mitmproxy-ca-cert.pem`
   - Отметить "Доверять при идентификации веб-сайтов"

3. **Альтернативный способ через http://mitm.it:**
   - Запустить mitmdump с веб-интерфейсом:
   ```bash
   mitmdump \
     --set confdir=config/mitmproxy \
     --set listen_port=6800 \
     --set web_port=6801 \
     --set web_open_browser=false
   ```
   - Открыть в Firefox: http://127.0.0.1:6801
   - Скачать и установить сертификат для Firefox

### Проблема 3: Конфигурация не применяется

**Причина:** mitmdump может не находить конфигурационный файл

**Решение 1: Проверить структуру директорий**

```bash
# Должна быть такая структура:
config/
└── mitmproxy.yaml

# А не:
config/
└── mitmproxy/
    └── mitmproxy.yaml
```

**Решение 2: Использовать правильный confdir**

```bash
# Если конфиг в config/mitmproxy.yaml
mitmdump --set confdir=config

# Если нужно создать отдельную директорию
mkdir -p config/mitmproxy
mv config/mitmproxy.yaml config/mitmproxy/
mitmdump --set confdir=config/mitmproxy
```

## 🧪 Тестовая последовательность

### Шаг 1: Проверить конфигурацию

```bash
# Проверить что файл существует
ls -la config/mitmproxy.yaml

# Проверить синтаксис YAML
python -c "import yaml; yaml.safe_load(open('config/mitmproxy.yaml'))"
```

### Шаг 2: Создать правильную структуру

```bash
# Создать правильную структуру директорий
mkdir -p config/mitmproxy
mv config/mitmproxy.yaml config/mitmproxy/
```

### Шаг 3: Запустить с явными параметрами

```bash
# Тестовый запуск с явными параметрами
mitmdump \
  --set confdir=config/mitmproxy \
  --set listen_port=6680 \
  --set listen_host=0.0.0.0 \
  --set flow_detail=3 \
  -w logs/test_run_$(date +%Y%m%d_%H%M%S).flow
```

### Шаг 4: Проверить запуск

```bash
# Должен увидеть:
[HH:MM:SS.mmm] HTTP(S) proxy listening at *:6680.
```

### Шаг 5: Настроить Firefox

1. **Настройки прокси:**
   - Firefox → Настройки → Сеть → Настройки сети
   - Ручная настройка прокси
   - HTTP прокси: 127.0.0.1:6680
   - HTTPS прокси: 127.0.0.1:6680

2. **Установить сертификат:**
   - Открыть http://127.0.0.1:6801 (если включен веб-интерфейс)
   - Или установить вручную из `~/.mitmproxy/mitmproxy-ca-cert.pem`

## 🔄 Переключение в режим Code

Для выполнения этих команд нужно переключиться в режим **Code**.

---
*Создано: 2025-12-07*
*Статус: Решения подготовлены*
