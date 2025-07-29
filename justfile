set dotenv-load := true
project_name := "mopidy-vkm"
dev_compose_file := ".devcontainer/docker-compose.yml"

# Show all available commands
default:
    @just --list

# === DevContainer build ===

# Fast build DevContainer with cache usage
devc-build:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🔨 Fast DevContainer build..."
    docker compose -f {{dev_compose_file}} build --progress=plain
    echo "✅ Build completed"

# Full rebuild DevContainer without cache
devc-rebuild:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🔨 Full DevContainer rebuild..."
    docker compose -f {{dev_compose_file}} build --no-cache --progress=plain
    echo "✅ Rebuild completed"

# === Cache Management ===

# Show cache information
cache-info:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "📊 Project cache information:"
    echo "================================"

    # Find all project volumes
    volumes=$(docker volume ls -q | grep -E "({{project_name}}|devcontainer)" | sort || echo "")

    if [ -z "$volumes" ]; then
        echo "❌ No project volumes found"
        return 0
    fi

    echo "✅ Found volumes:"
    echo "$volumes" | while read volume; do
        if [ ! -z "$volume" ]; then
            size=$(docker run --rm -v "$volume":/data alpine du -sh /data 2>/dev/null | cut -f1 || echo "N/A")
            printf "  📁 %-40s %s\n" "$volume:" "$size"
        fi
    done

    echo ""
    echo "💾 Total cache size in system:"
    if [ ! -z "$VOLUME_ROOT" ] && [ -d "$VOLUME_ROOT" ]; then
        du -sh "$VOLUME_ROOT"/* 2>/dev/null || echo "  Caches not yet created"
    else
        echo "  VOLUME_ROOT is not set or does not exist"
    fi

# Clear caches safety
cache-clean:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "⚠️  WARNING: This will remove ALL project caches!"
    echo "All dependencies will have to be re-downloaded."
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 Stopping containers..."
        docker compose -f {{dev_compose_file}} down || true

        echo "🗑️  Removing caches..."
        # Find cache volumes only, excluding command history and important data
        cache_volumes=$(docker volume ls -q | grep -E "({{project_name}}|devcontainer)" | grep -E "(cache|asdf)" | grep -v -E "(commandhistory|mcp-data)" || echo "")
        volumes_to_delete=$(docker volume ls -q | grep -E "({{project_name}}.*cache|{{project_name}}.*data)" || true)

        if [ -z "$cache_volumes" ]; then
            echo "ℹ️  No caches found to delete"
        else
            echo "🔍 Volumes found for removal:"
            echo "$cache_volumes" | while read vol; do
                if [ ! -z "$vol" ]; then
                    echo "  🗑️  $vol"
                fi
            done
            echo ""

            # Remove volumes
            echo "$cache_volumes" | xargs -r docker volume rm
            echo "✅ Caches cleared"
        fi
    else
        echo "❌ Operation canceled"
    fi

# Remove all data including command history
cache-nuclear:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "☢️  DANGER: ALL project data will be deleted!"
    echo "Including command history and MCP data!"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 Stopping containers..."
        docker compose -f {{dev_compose_file}} down --remove-orphans --volumes || true
        docker ps -q --filter "name={{project_name}}" | xargs -r docker stop
        docker ps -aq --filter "name={{project_name}}" | xargs -r docker rm

        echo "🗑️  Removing all volumes..."
        all_volumes=$(docker volume ls -q | grep -E "({{project_name}}|devcontainer)" || echo "")

        if [ ! -z "$all_volumes" ]; then
            echo "$all_volumes" | xargs -r docker volume rm
            echo "✅ All volumes deleted"
        fi

        # Also clear local caches
        if [ ! -z "$VOLUME_ROOT" ] && [ -d "$VOLUME_ROOT" ]; then
            echo "🗑️  Clearing local caches..."
            rm -rf "$VOLUME_ROOT"/*
            echo "✅ Local caches cleared"
        fi
    else
        echo "❌ Operation canceled"
    fi

# === Development ===

# Установить зависимости Python
view-deps:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "📦 review python deps..."
    uv pip install -e ".[dev]"
    uv tree
    uv tool install tox --with tox-uv
    tox --version
    uv run tox list -q
    echo "✅ deps printed"

# Run tests
test:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🧪 Running tests..."
    uv run pytest tests/ -v
    echo "✅ Tests completed"

# Run tests with tox
test-tox:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🧪 Running tests..."
    tox
    echo "✅ Tests completed"

# Code lint check
lint:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🔍 Code linting..."
    uv run ruff check src/ tests/
    echo "✅ Lint check passed"

# Format code
fmt:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🎨 Code formatting..."
    uv run ruff format src/ tests/
    uv run ruff check --fix src/ tests/
    echo "✅ Code formatted"

# === Mopidy commands ===

# Run Mopidy in development mode
mopidy-dev:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🎵 Running Mopidy in development mode..."
    mopidy --config /workspace/mopidy.conf --verbose
