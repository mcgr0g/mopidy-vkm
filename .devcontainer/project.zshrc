HISTFILE=/commandhistory/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt inc_append_history
setopt share_history

export VIRTUAL_ENV_DISABLE_PROMPT=1
ZSH_THEME="robbyrussell"
plugins=(git zsh-syntax-highlighting zsh-autosuggestions virtualenv)

fpath+=("$PWD")

autoload -Uz compinit && compinit
export PATH="${ASDF_DATA_DIR:-$HOME/.asdf}/shims:$PATH"
fpath=(${ASDF_DATA_DIR:-$HOME/.asdf}/completions $fpath)

if [[ -f "$PWD/.just.zsh-completion" ]]; then
  . "$PWD/.just.zsh-completion"
fi

[ -f $ZSH/custom/devcontainer.zsh ] && source $ZSH/custom/devcontainer.zsh

if [[ -f "~/.venv/bin/activate" && -z "$VIRTUAL_ENV" ]]; then
  source ~/.venv/bin/activate
fi

# Ensure oh-my-zsh is always loaded in interactive shells
export ZSH="$HOME/.oh-my-zsh"
source $ZSH/oh-my-zsh.sh
