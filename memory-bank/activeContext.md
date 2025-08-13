# Current Active Tasks

## 1. Cleanup and Base Initialization
- **Problem:** `src/mopidy_vkm/__init__.py` is currently a placeholder containing imports to non-existent modules.
- **Action:**
  - Remove or replace invalid imports.
  - Set up minimal, valid import paths for existing and to-be-implemented modules.
  - Ensure the package is discoverable by Mopidy’s extension loader.

## 2. Implement Core Backend
- **Goal:** Create a functional `mopidy_vkm.backend` module that:
  - Registers the Mopidy backend extension (`library`, `playback`, and optionally `playlists` providers).
  - Initializes and exposes the `VKMAuthService`.
  - Manages lifecycle events for the VK service connection.
  - Supplies a Mopidy URI scheme handler (`vkm:`) for VK tracks.

## 3. Implement Web Interface
- **Goal:** Create `mopidy_vkm.web` module that:
  - Provides Tornado request handlers for `/vkm/auth` endpoints.
  - Implements the `/vkm/auth/status` method to report current authentication state (e.g., `processing`, `captcha_required`, `2fa_required`, `success`, `error`).
  - Supports login, captcha submission, and 2FA code submission routes.
  - Updates frontend via polling or asynchronous events.

## 4. Authentication Flow Completion
- Ensure full VK authentication workflow works end-to-end:
  1. User opens `/vkm` and submits credentials.
  2. Backend invokes `VKMAuthService` (using `vkpymusic`).
  3. If captcha or 2FA required, status updates accordingly.
  4. On success, credentials are securely saved via `CredentialsManager`.

## 5. Authorization Testing Strategy
- **Key Constraint:** Testing must validate the `/vkm/auth/status` flow **without** reading sensitive data directly from the credentials file.
- **Approach:**
  - Mock or stub the `CredentialsManager` when testing status responses.
  - Simulate status transitions in controlled test environments.
  - Ensure test coverage for both success and failure paths of authorization.
- **Manual E2E Test with real VK test account:**
  1. Place test account credentials in root `.env` file under:
     - `TEST_USER_LOGIN`
     - `TEST_USER_PASSWORD`
  2. Open `/vkm` in browser.
  3. Enter the credentials from `.env` (either manually or via test harness).
  4. If prompted, complete captcha or 2FA step.
  5. Verify `/vkm/auth/status` transitions to `success` and that the VK library is accessible.


---

# Notes
- All sensitive data must be accessed through `CredentialsManager` API.
- Target: After implementation, the end-to-end VK login and `/vkm/auth/status` polling must be functional in development and test environments.
- Ensure logging does not expose tokens, passwords, or user profile details.
