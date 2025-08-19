
# System Patterns

1. **Layered Hexagonal Architecture**
   - Core domain entities (`Track`, `Playlist`, `Credentials`) are isolated from I/O.
   - Adapters: VK API (`vkpymusic.Service`), Mopidy Providers, Tornado Web UI.
2. **Actor Model (Pykka)** for all long-running tasks to avoid blocking Mopidy core.
3. **Service Locator** for sharing the authenticated `vk_service` between providers.
4. **Retry with Exponential Back-Off** when refreshing tokens or resolving stream URLs.
5. **Strict Typing + Pydantic** for config and credentials schema validation.

## Module Structure

### Authentication Module

The authentication module is organized into a package with specialized submodules:

```
mopidy_vkm/auth/
├── __init__.py       # Exports public API
├── credentials.py    # Secure storage and retrieval of credentials
├── handlers.py       # Handlers for captcha and 2FA challenges
├── service.py        # Main authentication service
├── status.py         # Authentication status enum
├── token.py          # VK token and service classes
└── data/             # Static data files
    └── user_agents.json  # Preset user agent strings
```

Each submodule has a specific responsibility:

1. **credentials.py**: Manages secure storage and retrieval of VK credentials
   - Handles file I/O with proper permissions
   - Implements user agent selection strategy
   - Provides a clean API for accessing credential data

2. **handlers.py**: Manages authentication challenges
   - Handles captcha and 2FA requests
   - Provides thread-safe state management
   - Exposes methods for submitting solutions

3. **service.py**: Coordinates the authentication process
   - Initializes and manages the VK service
   - Handles the authentication workflow
   - Provides status reporting

4. **status.py**: Defines authentication status enum
   - Provides a type-safe way to represent auth states
   - Used for status reporting and state transitions

5. **token.py**: Provides VK token and service classes
   - Wraps the vkpymusic library
   - Handles import errors gracefully
   - Provides placeholder implementations for testing

## Type Annotation Conventions

1. **Standard Type Annotations**
   - All function parameters and return values have explicit type annotations
   - Complex types use the typing module (e.g., `dict[str, Any]`, `list[str]`)
   - Optional parameters use the `| None` syntax (Python 3.10+)

2. **Dynamic Typing with Any**
   - `Any` is used sparingly and only when necessary
   - When used, it should be accompanied by a `# noqa: ANN401` comment
   - Common cases for `Any`:
     - External library interfaces with unknown types
     - Variable keyword arguments (`**kwargs: Any`)
     - Dictionary values with heterogeneous types

3. **Type Checking Directives**
   - `# type: ignore[attr-defined]` for accessing attributes that may not exist
   - `# type: ignore[assignment]` for assignments that may violate type constraints
   - Always include the specific error code in square brackets

4. **Forward References**
   - Use string literals for forward references
   - Import TYPE_CHECKING from typing for conditional imports

## Mopidy Guidelines
- All URIs use the `vkm:` scheme.
- Providers must implement: `browse`, `lookup`, `search`, `translate_uri`, `play`, `pause`, `seek`.
- Never block the actor loop; use threads or async helpers.
