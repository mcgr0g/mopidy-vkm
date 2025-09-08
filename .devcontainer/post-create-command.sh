#!/bin/bash

set -e

echo "🚀 Setting up mopidy-vkm development environment with MCP support..."

# crutch for assembling with setuptools
mkdir -p /tmp/egg_info

mkdir -p $HOME/.oh-my-zsh/custom/plugins

# for your alias and configs
if [ -f "/workspace/.devcontainer/user.zsh" ]; then
  cp /workspace/.devcontainer/user.zsh "$HOME/.oh-my-zsh/custom/devcontainer.zsh"
fi

if [ ! -d "/home/mopidy/.oh-my-zsh/custom/plugins/zsh-autosuggestions" ]; then
    git clone https://github.com/zsh-users/zsh-autosuggestions \
        ~/.oh-my-zsh/custom/plugins/zsh-autosuggestions
else
    echo "⚠️ zsh-autosuggestions already installed, skipping..."
fi


if [ ! -d "/home/mopidy/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting" ]; then
    git clone https://github.com/zsh-users/zsh-syntax-highlighting.git \
        ~/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting
else
    echo "⚠️ zsh-syntax-highlighting already installed, skipping..."
fi

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

echo "📦 Check Node.js..."
if node --version > /dev/null 2>&1; then
    echo "✅ Node.js installed: $(node --version)"
    echo "✅ npm installed: $(npm --version)"
else
    echo "❌ Node.js not found"
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


echo "📦 Synchronizing Python dependencies..."
uv sync || {
    echo "⚠️  Warning: uv sync failed"
}

echo "✅ Development environment setup completed!"
echo ""

exit 0
