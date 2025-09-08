FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && \
    apt-get install -yqq --no-install-recommends \
    # base tools
    locales \
    curl \
    jq \
    unzip \
    git \
    build-essential \
    software-properties-common \
    ca-certificates \
    gnupg \
    lsb-release \
    sudo \
    zsh \
    # Python deps
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    llvm \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    # mopidy deps
    python3-dev \
    python3-pip \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-pulseaudio \
    python3-gst-1.0 \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    # audio deps
    pulseaudio \
    alsa-utils

RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=en_US.UTF-8

ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8

ARG GO_VERSION=1.24.4
ARG GO_ARCH=amd64

RUN curl -OL https://dl.google.com/go/go${GO_VERSION}.linux-${GO_ARCH}.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-${GO_ARCH}.tar.gz && \
    rm go${GO_VERSION}.linux-${GO_ARCH}.tar.gz

ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd --gid $USER_GID mopidy && \
    useradd --uid $USER_UID --gid $USER_GID -m -s /bin/bash mopidy && \
    echo "mopidy ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    mkdir -p /var/lib/mopidy \
        /workspace \
        /tmp/egg_info \
        /commandhistory \
        /home/mopidy/.mcp-servers \
        /home/mopidy/.mcp-data/memory && \
    chown -R mopidy:mopidy /var/lib/mopidy \
        /workspace \
        /tmp/egg_info \
        /commandhistory \
        /home/mopidy/.mcp-servers \
        /home/mopidy/.mcp-data && \
    touch /commandhistory/.bash_history && \
    git config --global --add safe.directory /workspace

USER mopidy
WORKDIR /home/mopidy

# asdf instal & tuning
ENV PATH="/home/mopidy/.asdf/bin:/home/mopidy/.asdf/shims:/usr/local/go/bin:/home/mopidy/go/bin:${PATH}" \
    GOPATH=/home/mopidy/go \
    ASDF_DIR=/home/mopidy/.asdf \
    ASDF_DATA_DIR=/home/mopidy/.asdf \
    HISTFILE=/commandhistory/.bash_history \
    HISTSIZE=10000 \
    HISTFILESIZE=20000 \
    PROMPT_COMMAND="history -a; history -c; history -r" \
    ZSH_ALREADY_INSTALLED=true

RUN go version && \
    go install github.com/asdf-vm/asdf/cmd/asdf@v0.18.0 && \
    echo 'export PATH="${ASDF_DATA_DIR:-$HOME/.asdf}/shims:$PATH"' >> ~/.profile && \
    echo 'export PATH="/home/mopidy/go/bin:$PATH"' >> ~/.profile && \
    echo 'export PROMPT_COMMAND="history -a"' >> ~/.bashrc && \
    echo 'export HISTFILE=/commandhistory/.bash_history' >> ~/.bashrc && \
    echo 'export HISTSIZE=10000' >> ~/.bashrc && \
    echo 'export HISTFILESIZE=10000' >> ~/.bashrc

# asdf plugins
COPY --chown=${USER_UID}:${USER_GID} .tool-versions /home/mopidy/.tool-versions
RUN asdf plugin add uv && \
    asdf plugin add nodejs && \
    asdf plugin add just && \
    asdf install && \
    asdf reshim && \
    echo "=== ASDF Current ===" && \
    asdf current && \
    echo "=== PATH ===" && \
    echo $PATH && \
    echo "=== Which npm ===" && \
    which npm && \
    echo "=== npm version ===" && \
    npm --version

# nodejs packages, mcp servers
COPY --chown=${USER_UID}:${USER_GID} package.json /home/mopidy/package.json
RUN ([ -f package-lock.json ] && npm ci || npm install) && \
    asdf reshim nodejs

# browsers
RUN npm run playwright:install && asdf reshim nodejs

ARG WEB_SEARCH_VERSION
# web-search-mcp version resolve
RUN mkdir -p /home/mopidy/.mcp-servers && \
    cd /home/mopidy/.mcp-servers && \
    if [ "$WEB_SEARCH_VERSION" = "latest" ]; then \
        echo "🔍 Fetching latest release..."; \
        RELEASE_DATA=$(curl -s https://api.github.com/repos/mrkrsl/web-search-mcp/releases/latest); \
        VERSION=$(echo "$RELEASE_DATA" | jq -r '.tag_name'); \
        DOWNLOAD_URL=$(echo "$RELEASE_DATA" | jq -r '.assets[] | select(.name | endswith(".zip")) | .browser_download_url'); \
        echo "VERSION=$VERSION" > /tmp/web-search-version; \
        echo "DOWNLOAD_URL=$DOWNLOAD_URL" > /tmp/web-search-url; \
    else \
        VERSION="$WEB_SEARCH_VERSION"; \
        DOWNLOAD_URL="https://github.com/mrkrsl/web-search-mcp/releases/download/${VERSION}/web-search-mcp-${VERSION}.zip"; \
        echo "VERSION=$VERSION" > /tmp/web-search-version; \
        echo "DOWNLOAD_URL=$DOWNLOAD_URL" > /tmp/web-search-url; \
    fi

# web-search-mcp install
RUN cd /home/mopidy/.mcp-servers && \
    VERSION=$(cat /tmp/web-search-version | cut -d= -f2) && \
    DOWNLOAD_URL=$(cat /tmp/web-search-url | cut -d= -f2) && \
    echo "📦 Downloading web-search-mcp version: $VERSION" && \
    curl -L -o web-search-mcp.zip "$DOWNLOAD_URL" && \
    unzip web-search-mcp.zip -d web-search-mcp && \
    rm web-search-mcp.zip && \
    cd /home/mopidy/.mcp-servers/web-search-mcp && \
    echo "📂 Contents:" && ls -la dist && \
    echo "✅ web-search-mcp ready"

# special check
RUN python3 -c "import gi; gi.require_version('Gst', '1.0'); from gi.repository import Gst; print(Gst.init(None))" \
    && echo "if you see '[]' - GStreamer and gi are properly installed"

# uv tune and run
ENV PATH="/home/mopidy/.venv/bin:/home/mopidy/.local/bin:$HOME/.local/share/uv/tools/bin:$PATH" \
    VIRTUAL_ENV="/home/mopidy/.venv" \
    PYTHONPATH="/usr/lib/python3/dist-packages:${PYTHONPATH}" \
    UV_LINK_MODE="copy" \
    UV_PROJECT_ENVIRONMENT="/home/mopidy/.venv" \
    ZSH_ALREADY_INSTALLED=true

WORKDIR /workspace

RUN --mount=type=bind,source=.,target=/workspace,rw \
    uv venv /home/mopidy/.venv --system-site-packages && \
    ls -la && \
    ls -la /home/mopidy && \
    uv pip install -e ".[dev]" && \
    asdf reshim && \
    touch /home/mopidy/.gitconfig && \
    echo 'source /home/mopidy/.venv/bin/activate' >> ~/.bashrc

COPY --chown=${USER_UID}:${USER_GID} .devcontainer/project.zshrc /home/mopidy/.zshrc

CMD ["sleep", "infinity"]
