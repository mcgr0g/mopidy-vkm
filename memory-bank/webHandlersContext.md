
# Web Handlers Context

| Route | Method | Purpose |
|-------|--------|---------|
| `/vkm` | GET | Render status/login page. |
| `/vkm/auth/login` | POST | `{login, password}` — kick off authentication in thread. Returns JSON with `status`. |
| `/vkm/auth/verify` | POST | Submit CAPTCHA text or 2FA code. |
| `/vkm/auth/status` | GET | Poll current auth state (`processing`, `captcha_required`, `2fa_required`, `success`, `error`). |

Frontend is a lightweight HTML+fetch UI served from `web/` static directory; no frameworks to minimise bundle size.
