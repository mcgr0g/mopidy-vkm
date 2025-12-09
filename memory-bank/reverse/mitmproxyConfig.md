# Конфигурационный файл mitmproxy

## Файл: config/mitmproxy.yaml

```yaml
# Конфигурация mitmdump для анализа API
# Сохраняет логи в директорию проекта logs/

# Сетевые настройки
listen_port: 6680
listen_host: 0.0.0.0

# Настройки сертификатов (используются стандартные ~/.mitmproxy)
certs: ["~/.mitmproxy/mitmproxy-ca-cert.pem"]

# Настройки логирования
save_stream_file: false  # Отключаем stream лог, используем flow файлы
stream_large_bodies: 1048576  # 1MB

# Настройки сохранения flow файлов
save_flow_file: true
flow_detail: 3  # Максимальный уровень детализации
flow_store: disk

# Настройки логирования
termlog_verbosity: info
eventlog_verbosity: info

# Настройки фильтрации
showhost: true
mode: regular

# Отключаем веб-интерфейс (не нужен для mitmdump)
web_open_browser: false
web_port: 0  # Отключаем
```

## Инструкции по созданию

1. Создайте файл `config/mitmproxy.yaml`
2. Скопируйте содержимое выше в этот файл
3. Убедитесь что права доступа позволяют чтение файла

## Проверка конфигурации

```bash
# Проверка синтаксиса конфигурации
mitmdump --options
```

---
*Создано: 2025-12-07*
*Статус: Готово к копированию*
