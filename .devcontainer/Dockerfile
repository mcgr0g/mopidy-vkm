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
    ssh \
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
    # debug tools
    net-tools \
    lsof \
    iproute2 \
    psmisc \
    # audio deps
    pulseaudio \
    alsa-utils \
    # X11 and display deps for Playwright UI mode
    ffmpeg \
    xvfb \
    x11vnc \
    x11-xserver-utils \
    xauth \
    x11-apps \
    # Playwright browser dependencies
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    fonts-noto-color-emoji \
    fonts-wqy-zenhei \
    fonts-freefont-ttf \
    fonts-tlwg-loma-otf \
    xfonts-encodings \
    fonts-ipafont-gothic \
    fonts-unifont \
    xfonts-utils \
    xfonts-scalable \
    # Additional libs for browsers
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgcc1 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcursor1 \
    libxfixes3 \
    libxi6 \
    libxrender1 \
    libxext6 \
    libxft2 \
    libxinerama1 \
    libxtst6

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
    useradd --uid $USER_UID --gid $USER_GID -m -s /bin/zsh mopidy && \
    echo "mopidy ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    mkdir -p \
        /var/lib/mopidy \
        /workspace/.mcp-data/memory \
        /workspace/.browsers \
        /workspace/.recordings \
        /tmp/egg_info \
        /home/mopidy/.vscode-server/data/Machine \
        /home/mopidy/.vscode-server/bin \
        /commandhistory && \
    chown -R mopidy:mopidy \
        /var/lib/mopidy \
        /workspace \
        /tmp/egg_info \
        /home/mopidy/.vscode-server \
        /commandhistory && \
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
    ZSH_ALREADY_INSTALLED=true \
    # Playwright environment variables
    PLAYWRIGHT_BROWSERS_PATH=/workspace/.browsers \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0 \
    # Display configuration
    DISPLAY=:99 \
    XVFB_WHD=1920x1080x24

RUN curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh | \
    sh -s -- --unattended --keep-zshrc || true

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
WORKDIR /workspace/js-tools
COPY --chown=${USER_UID}:${USER_GID} js-tools/package*.json ./
# install strategy: from lock if exist, otherwise from package
RUN ([ -f package-lock.json ] && npm ci || npm install) && \
    echo "🔄 Reshimming asdf..." && \
    asdf reshim nodejs && \
    echo "✅ Reshim complete" && \
    ln -sf /workspace/js-tools/node_modules /workspace/node_modules

# browsers
RUN npm run playwright:install-deps && \
    echo "=== Playwright browsers installed ===" && \
    npm playwright --version && \
    asdf reshim nodejs && \
    ls -la /workspace/.browsers

# special check
RUN python3 -c "import gi; gi.require_version('Gst', '1.0'); from gi.repository import Gst; print(Gst.init(None))" \
    && echo "if you see '[]' - GStreamer and gi are properly installed"

# uv tune and run
ENV PATH="/home/mopidy/.venv/bin:/home/mopidy/.local/bin:$HOME/.local/share/uv/tools/bin:$PATH" \
    VIRTUAL_ENV="/home/mopidy/.venv" \
    PYTHONPATH="/usr/lib/python3/dist-packages:${PYTHONPATH}" \
    UV_LINK_MODE="copy" \
    UV_PROJECT_ENVIRONMENT="/home/mopidy/.venv" \
    ZSH_ALREADY_INSTALLED=true \
    JUST_TEMPDIR="/home/mopidy/.cache/just-tmp"

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

COPY . .

CMD ["sleep", "infinity"]
