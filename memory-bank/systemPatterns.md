
# System Patterns

1. **Layered Hexagonal Architecture**
   - Core domain entities (`Track`, `Playlist`, `Credentials`) are isolated from I/O.
   - Adapters: VK API (`vkpymusic.Service`), Mopidy Providers, Tornado Web UI.
2. **Actor Model (Pykka)** for all long-running tasks to avoid blocking Mopidy core.
3. **Service Locator** for sharing the authenticated `vk_service` between providers.
4. **Retry with Exponential Back-Off** when refreshing tokens or resolving stream URLs.
5. **Strict Typing + Pydantic** for config and credentials schema validation.

## Mopidy Guidelines
- All URIs use the `vkm:` scheme.
- Providers must implement: `browse`, `lookup`, `search`, `translate_uri`, `play`, `pause`, `seek`.
- Never block the actor loop; use threads or async helpers.
