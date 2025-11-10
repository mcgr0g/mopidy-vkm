# in devcontainer
just run 'Reopen in container'

# on debian based os
there are some prereq:
  - golang https://go.dev/doc/install
  - asdf https://asdf-vm.com/

## after clone
```sh
# for local development
asdf current
asdf install
# for tox-uv usage
asdf list all python | grep 3.13
asdf install python 3.13.5
asdf list all python | grep 3.12
asdf install python 3.12.11
# for direct usage
uv sync --upgrade-package pyright
just --completions zsh > .just.zsh-completion
```

add in `~/.zshrc`
```
fpath+=("$PWD")
autoload -Uz compinit
compinit
if [[ -f "$PWD/.just.zsh-completion" ]]; then
  . "$PWD/.just.zsh-completion"
fi
```

## tox
https://github.com/tox-dev/tox-uv

```sh
uv tool install tox --with tox-uv
uv sync
tox --version
uv tree
uv run tox list -q
tox
uv tree
```

## after changes
```sh
uv run ruff format .
uv run ruff check . --fix
uv run pyright src/

uv run pytest tests/web/base/ -v
uv run pytest tests/web/auth/ -v
uv run pytest tests/web/ -v
uv run pytest tests/ -v
```
