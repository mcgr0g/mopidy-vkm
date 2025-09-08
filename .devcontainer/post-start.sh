#!/bin/bash
set -euo pipefail

# crutch for assembling with setuptools
mkdir -p /tmp/egg_info

echo "🔄 Syncing cline mcp settigns from devcontainer settings"

# SOURCE: файл с твоими серверами
SOURCE_JSON=".devcontainer/devcontainer.json"

# Проверить, что SOURCE_JSON существует
if [ ! -f "$SOURCE_JSON" ]; then
    echo "❌ Source file $SOURCE_JSON not found"
    exit 1
fi

# TARGET: файл MCP серверов Cline
CLINE_JSON="/home/mopidy/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"

# Создать директорию, если не существует
mkdir -p "$(dirname "$CLINE_JSON")"

# Создать пустой MCP файл, если не существует
if [ ! -f "$CLINE_JSON" ]; then
    echo '{"mcpServers": {}}' > "$CLINE_JSON"
    echo "Created empty cline_mcp_settings.json"
fi

# Создать бекап только если файл существует и не пустой
if [ -s "$CLINE_JSON" ]; then
    cp "$CLINE_JSON" "${CLINE_JSON}.bak"
    echo "☑️ Backup created"
fi

# Краткая проверка, что jq установлен
if ! command -v jq > /dev/null; then
  echo "jq is required, install with: sudo apt-get install jq"
  exit 1
fi

echo "🔍 Extracting MCP servers via jq..."
temp_source=$(mktemp)
jq '.customizations.vscode.mcp.servers // {} | { mcpServers: . }' "$SOURCE_JSON" > "$temp_source"
echo "📋 Extracted content:"
jq '.' "$temp_source"

# Проверить, что временный файл создался корректно
if [ ! -s "$temp_source" ]; then
    echo "❌ Failed to extract MCP servers from $SOURCE_JSON"
    rm -f "$temp_source"
    exit 1
fi

# Мержим mcpServers из SOURCE_JSON в CLINE_JSON
jq -s '
  (.[0].mcpServers // {}) as $cline |
  (.[1].mcpServers // {}) as $src |
  .[0] + { mcpServers: ($cline + $src) }
' "$CLINE_JSON" "$temp_source" > "${CLINE_JSON}.new"


# Проверить, что мерж прошёл успешно
if [ -s "${CLINE_JSON}.new" ]; then
    mv "${CLINE_JSON}.new" "$CLINE_JSON"
    echo "✅ MCP servers merged and synced"
else
    echo "❌ Failed to merge MCP settings"
    rm -f "${CLINE_JSON}.new"
fi

# Очистка
rm -f "$temp_source"
exit 0
