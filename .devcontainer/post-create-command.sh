#!/bin/bash

set -e

echo "🚀 Setting up mopidy-vkm development environment with MCP support..."

echo "🔧 Current user: $(whoami)"
echo "🔧 Current UID: $(id -u)"
echo "🔧 Current GID: $(id -g)"
echo "🔧 Current dir: $(pwd)"

echo "📦 Check asdf..."
if asdf --version > /dev/null 2>&1; then
    echo "✅ asdf installed: $(asdf --version)"
    asdf current
else
    echo "❌ asdf not found"
    exit 1
fi

echo "📦 Check UV..."
if uv --version > /dev/null 2>&1; then
    echo "✅ UV installed: $(uv --version)"
else
    echo "❌ UV not found"
    exit 1
fi

echo "📦 Check Python..."
if python --version > /dev/null 2>&1; then
    echo "✅ Python installed: $(python --version)"
else
    echo "❌ Python not found"
    exit 1
fi

echo "🎵 Check Mopidy..."
if /home/mopidy/.venv/bin/python -c "import mopidy; print('Mopidy:', mopidy.__version__)" 2>/dev/null; then
    echo "✅ Mopidy installed"
else
    echo "⚠️ Mopidy not found"
fi

echo "🎬 Check GStreamer..."
if python3 -c "import gi; gi.require_version('Gst', '1.0'); from gi.repository import Gst; print(Gst.init(None)); print('GStreamer:', Gst.version_string())" 2>/dev/null; then
    echo "✅ GStreamer installed"
else
    echo "⚠️ GStreamer not found"
fi

echo "📦 Check Node.js..."
cd /workspace/js-tools
echo "📦 Node.js environment:"
node --version
npm --version
npm root

echo "🎭 Check Playwright..."
npx playwright --version || echo "⚠️ Playwright not found"

echo "📦 Synchronizing Python dependencies..."
uv sync || {
    echo "⚠️  Warning: uv sync failed"
}

echo "✅ Development environment setup completed!"
echo ""

exit 0
