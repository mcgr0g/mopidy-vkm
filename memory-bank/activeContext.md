# Current Active Tasks

## 1. Cleanup and Base Initialization
- **Problem:** `src/mopidy_vkm/__init__.py` is currently a placeholder containing imports to non-existent modules.
- **Action:**
  - Remove or replace invalid imports.
  - Set up minimal, valid import paths for existing and to-be-implemented modules.
  - Ensure the package is discoverable by Mopidy's extension loader.

## 2. Implement Core Backend
- **Goal:** Create a functional `mopidy_vkm.backend` module that:
  - Registers the Mopidy backend extension (`library`, `playback`, and optionally `playlists` providers).
  - Initializes and exposes the `VKMAuthService`.
  - Manages lifecycle events for the VK service connection.
  - Supplies a Mopidy URI scheme handler (`vkm:`) for VK tracks.

## 3. Implement Web Interface
- **Goal:** Create `mopidy_vkm.web` module that:
  - Provides Tornado request handlers for `/vkm/auth` endpoints.
  - Implements the `/vkm/auth/status` method to report current authentication state.
  - Supports login, captcha submission, and 2FA code submission routes.
  - Updates frontend via polling or asynchronous events.

## 4. Authentication Flow Completion
- Ensure full VK authentication workflow works end-to-end:
  1. User opens `/vkm` and submits credentials.
  2. Backend invokes `VKMAuthService` (using `vkpymusic`).
  3. If captcha or 2FA required, status updates accordingly.
  4. On success, credentials are securely saved via `CredentialsManager`.

## 5. Manual E2E Testing
- **Goal:** Verify the complete authentication flow with a real VK account
- **Steps:**
  1. Place test account credentials in root `.env` file under:
     - `VK_TEST_LOGIN`
     - `VK_TEST_PASSWORD`
  2. Open `/vkm` in browser.
  3. Enter the credentials from `.env` (either manually or via test harness).
  4. If prompted, complete captcha or 2FA step.
  5. Verify `/vkm/auth/status` transitions to `success` and that the VK library is accessible.

---

# Recent Improvements

## Authentication Module
- ✅ Refactored into specialized submodules with clear separation of concerns
- ✅ Fixed all linter and type checking errors
- ✅ Improved error handling and security
- ✅ Enhanced test coverage to 64%

## Code Quality Standards
- All new code must follow the type annotation conventions in `systemPatterns.md`
- Linter errors must be fixed or explicitly suppressed with appropriate comments
- Security-sensitive code must use `secrets` module instead of `random`
- Exception handling must include specific error messages and proper logging

## Notes
- All sensitive data must be accessed through `CredentialsManager` API.
- Ensure logging does not expose tokens, passwords, or user profile details.
