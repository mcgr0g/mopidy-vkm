
# Tech Context

- **Language:** Python ≥ 3.11
- **Runtime:** Mopidy ≥ 4.0.0a4 (actor system, GStreamer playback)
- **VK Library:** vkpymusic ≥ 3.5.0
- **Web Framework:** Tornado ≥ 6.2 (serves /vkm endpoints & static files)
- **Tooling:** uv, tox, pytest, Ruff 0.11.0, Pyright ≥ 1.1.394
- **Containerisation:** Docker Compose (build from official debian image + this extension)
- **CI:** GitHub Actions matrix (3.11-3.13) with artifact upload to Releases.
