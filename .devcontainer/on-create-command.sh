#!/bin/bash

set -e

echo "🔧 Current user: $(whoami)"
echo "🔧 Current UID: $(id -u)"
echo "🔧 Current GID: $(id -g)"


# crutch for persistent volumes
mkdir -p \
    /home/mopidy/.vscode-server/data/User/globalStorage \
    /home/mopidy/.vscode-server/data/Machine \
    /home/mopidy/.vscode-server/bin \
    /home/mopidy/.playwright \
    /workspace/.browsers \
    /workspace/.recordings \
    /home/mopidy/.cache/just-tmp \
    /tmp/.X11-unix \
    /tmp/egg_info

chmod 1777 /tmp/.X11-unix
# chown root:root /tmp/.X11-unix

chown -R mopidy:mopidy \
    /home/mopidy/.vscode-server \
    /home/mopidy/.playwright \
    /home/mopidy/.cache \
    /tmp/egg_info

echo "✅ Directories created"

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
