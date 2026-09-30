# Pocket Guru

FastAPI repair and DIY guide with verified-email accounts, photo inspection, My Garage, OBD-II lookup, Repair Library, and history.

## Accounts and deployment

This version requires a verified account. Configure Supabase Auth and production email delivery before deploying it to the live Render service; an unconfigured deployment shows the account setup screen and blocks private APIs.

Required server environment variables:

| Variable | Value |
| --- | --- |
| `SUPABASE_URL` | HTTPS URL of your Supabase project, without `/auth/v1` |
| `SUPABASE_PUBLISHABLE_KEY` | Supabase publishable key (legacy anon key also works); never use the service-role key |
| `APP_ORIGIN` | Exact public HTTPS origin, currently `https://pocket-mechanic-1.onrender.com` |
| `OPENAI_API_KEY` | Existing server key for photo analysis |

In Supabase Auth:

1. Enable email/password sign-up and **Confirm email**. Set minimum password length to at least eight characters.
2. Set the site URL to the same `APP_ORIGIN`. Disable unused anonymous, phone, and social providers.
3. Set email OTP length to six digits and expiry to 600 seconds; preserve rate limits and the resend interval of at least 60 seconds.
4. Paste `email-templates/confirmation.html` into the Confirm signup template, with subject `Verify your Pocket Guru account`. Paste `email-templates/recovery.html` into Reset password, with subject `Reset your Pocket Guru password`. Both use `{{ .Token }}`, rather than a link.
5. Enable custom SMTP through Resend, using its supplied SMTP credentials and a sender on a verified domain. Supabase's default email service is unsuitable for public sign-up. SMTP credentials belong in Supabase, not in the frontend or GitHub.
6. Before activating this version, test with an email outside the Supabase project team: sign-up sends a code, access is blocked before verification, the code verifies once, an incorrect/expired code fails, resend and password reset work, and sign-out blocks access again.

Start command remains `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Python dependencies are in `requirements.txt`. Local sign-in testing requires HTTPS because session cookies are Secure. Run `pytest` for mocked backend tests; no tests send real emails. For browser DOM checks, install `jsdom@26.1.0` in a temporary npm directory, set `NODE_PATH` to that directory’s `node_modules`, and run `node tests/frontend_accounts.cjs` and `node tests/frontend_garage.cjs`. These checks do not replace a real-device/email delivery test.

## Privacy and storage

Supabase manages passwords, email codes, and identities. Pocket Guru sends credentials only to its same-origin backend; session tokens stay in Secure, HttpOnly, SameSite cookies and never enter localStorage. The backend confirms verification and binds private API requests to the account displayed in the browser. Unsafe requests require the configured origin.

Garage and history remain browser-local, stored under each account's ID. They do **not** sync between devices yet. Existing guest data is imported only when the signed-in user explicitly chooses the import button; it is not automatically assigned to a new account. API profiles, diagnosis records, and uploads are filtered by their owner, but remain temporary server storage and can disappear on restart. Account registration is durable in Supabase; this update does not add durable garage/database sync.

The service worker caches the public app shell only. API responses and sessions are never cached. A verified session and reachable account service are required for private API operations.
