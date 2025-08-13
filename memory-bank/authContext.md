
# Auth Subsystem Context

## Overview

The authentication subsystem manages secure access to VK through the vkpymusic library and stores all sensitive credentials on disk. The system handles complex multi-step VK authentication (including captcha and 2FA) and must support smooth reauthorization using stored credentials when available.


The **VKMAuthService** handles VKontakte sign-in using `vkpymusic.TokenReceiver`.

```
+-------------+        start_auth()       +------------------+
|  Web /vkm   |  ───────────────────────▶ |  VKMAuthService  |
|  Tornado UI |                           +---------+--------+
+------+------+                                      │
       │ login & pwd                                │TokenReceiver callbacks
       │                                            ▼
+------+----------------------+        +-------------------+
| VKMAuthHandlers (captcha,  | ◀────── | TokenReceiver     |
| 2FA, invalid client, etc.) |        +-------------------+
+------+----------------------+        │ access_token      │
       │                                       │
       ▼                                       ▼
+------+----------------------+        +-------------------+
| CredentialsManager (JSON)  | ◀────── | vk_service        |
+-----------------------------+        +-------------------+
```

## File storage (Credentials)

Credentials saved to a single JSON file at path supplied by `sensitive_cache_path` in `ext.conf`

The credentials file securely stores the following fields:
- `access_token` — VK API authentication token (short- or long-lived)
- `refresh_token` — token for obtaining new `access_token`
- `client_user_id` — VK user ID, determined after first login; required for subsequent API calls
- `user_agent` — browser/User-Agent string used when authenticating
- `user_profile` — JSON-encoded profile object (id, name, avatar, etc.) that may be needed by frontend/components


File permissions are enforced as 600 to restrict access.


## User-Agent selection strategy

The VK backend must provide a valid User-Agent string for every session. The strategy is as follows:

1. **Use the cached value**
   If `user_agent` is present in Credentials, use it.
2. **Use a configured value**
   If there is a value specified in the main Mopidy extension config (`ext.conf`), use it.
3. **Randomly select from preset**
   If neither of the above exists, randomly pick a User-Agent string from a preset containing popular browser signatures:
   - Google Chrome, Mozilla Firefox on Windows, Ubuntu (Linux), and macOS
   - At least 2 up-to-date User-Agent lines for each OS/browser combination should be included in the preset, e.g.:
     - Windows: Chrome/119.0.6045.159, Firefox/119.0
     - Ubuntu: Chrome/119.0.6045.159, Firefox/119.0
     - macOS: Chrome/119.0.6045.159, Firefox/119.0

This hierarchy reduces the risk of triggering anti-fraud systems or VK account locks by reusing or rotating legitimate user agents.


## Token retrieval strategy

The logic to obtain a working access token:

1. **Cached token**
   Try to use the `access_token` from Credentials.
   - Before each VK API call, verify that the token is still valid (as supported by vkpymusic).
2. **Authorization flow**
   If there is no token or the existing token is invalid/expired, initiate the VK authentication process via vkpymusic, including captcha or 2FA as necessary.
   - On success, update and cache the new `access_token` and `refresh_token`.
   - Also store resulting `client_user_id` and the selected `user_agent` for future sessions.


## Security notes

- Credentials are never stored in plaintext outside the secured directory.
- All backend code must access tokens and IDs through the CredentialsManager API, not through manual file reads/writes.
- User-Agent rotation and caching logic must ensure the selected value is reused whenever possible to avoid suspicious VK activity.
- Authentication logs and error traces must never leak actual token values.

## Extensibility

- The auth subsystem is open for future improvements, e.g., supporting device-level identity, remote token refreshing, or alternative backends.
- The current vkpymusic library dependency may be replaced in the future, but the credential and user-agent strategies should be preserved.
