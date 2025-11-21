#!/bin/bash
set -euo pipefail

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

# 🖥️ Setup Xvfb (VIRTUAL X SERVER), prereq for playwright-mcp
echo "🖥️ Setting up display server..."
if ! pgrep -x "Xvfb" > /dev/null; then
    echo "Starting Xvfb virtual display server on :99..."
    Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset -nolisten tcp &
    export DISPLAY=:99
    sleep 2
    echo "✅ Xvfb started on display :99"
else
    echo "✅ Xvfb already running"
fi

# Test display
echo "🧪 Testing virtual display..."
if DISPLAY=:99 xdpyinfo > /dev/null 2>&1; then
    echo "✅ Display :99 is working"
else
    echo "⚠️ Warning: Display test failed"
fi

# Проверяем установку браузеров
if [ -d "/workspace/.browsers" ] && [ "$(ls -A /workspace/.browsers 2>/dev/null)" ]; then
    echo "✅ Playwright browsers are installed"

    # Создаем симлинк на последнюю версию Chromium
    LATEST_CHROMIUM=$(ls -1 /workspace/.browsers/ | grep '^chromium-' | grep -v '_headless' | sort -V | tail -1)
    if [ -n "$LATEST_CHROMIUM" ]; then
        echo "Creating symlink for latest Chromium: $LATEST_CHROMIUM"
        ln -sfn "/workspace/.browsers/$LATEST_CHROMIUM" "/workspace/.browsers/chromium-latest"
        echo "✅ Chromium symlink created"
    fi
else
    echo "⚠️ Playwright browsers not found - will be installed on first test run"
fi

echo "🎭 Playwright environment ready!"
echo "🤖 With Cline MCP you can now use commands like:"
echo "  'Cline, run VK authentication test in headed mode'"
echo "  'Cline, take a screenshot of the login page'"
echo ""

exit 0
