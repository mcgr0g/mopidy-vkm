
# Tech Context

- **Language:** Python ≥ 3.11
- **Runtime:** Mopidy ≥ 4.0.0a4 (actor system, GStreamer playback)
- **VK Library:** vkpymusic ≥ 3.5.0
- **Web Framework:** Tornado ≥ 6.2 (serves /vkm endpoints & static files)
- **Tooling:** uv, tox, pytest, Ruff 0.11.0, Pyright ≥ 1.1.394
- **Containerisation:** Docker Compose (build from official debian image + this extension)
- **CI:** GitHub Actions matrix (3.11-3.13) with artifact upload to Releases.

## Development tools

### Linting / Type Checking Convention

- All linting and type checking MUST be executed using the project’s environment via uv’s run command.
- This ensures correct tool versions and consistent dependency resolution, avoiding conflicts with globally installed versions.
- Specifically, always run:
  - `uv run ruff check .`
  - `uv run pyright src/`

### Test Execution Convention

- All tests MUST be run using `uv run pytest` to guarantee full plugin and environment integration.
- Example command:
  - `uv run pytest tests/ -v`

---

**Note:** Avoid running these tools directly with `python -m` or using globally installed versions to prevent environment inconsistencies.
