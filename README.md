# KeyRotate

A single-user dashboard that tracks API key expirations and emails you reminders before they die. Built because most LLM/SaaS providers (Anthropic, Mistral, etc.) don't expose a programmatic admin API for rotation — but most do let you set an expiration date manually. KeyRotate fills the gap: you log your keys + expiration dates, and it pings you at J−14 / J−7 / J−1 with a direct deep link to the provider's console.

## What it does

- Track API keys (name, provider, expiration date, notes)
- Daily cron checks for upcoming expirations
- Notifications via email (Resend) and/or Slack webhook
- Each notification includes a one-click "I rotated it" link that lets you set the new expiration date without logging in
- 12 providers pre-configured with the right rotation URL (Anthropic, OpenAI, Mistral, Supabase, AWS, GCP, Stripe, GitHub, Vercel, Cloudflare, Resend, Other)
- Single-user password auth (simple cookie session)

## Stack

- Backend: FastAPI + SQLModel + SQLite + APScheduler
- Frontend: Vite + React + TypeScript + Tailwind
- Email: Resend (with stub fallback if no key configured)

## Quick start

### 1. Backend

```bash
cd backend
cp .env.example .env
# edit .env — at minimum set APP_PASSWORD, SECRET_KEY, NOTIFY_EMAIL
uv sync
uv run uvicorn main:app --reload --port 8000
```

The backend creates `data/keyrotate.db` on first run and starts the daily scheduler.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, log in with `APP_PASSWORD`.

## Configuring notifications

### Email (Resend)

1. Sign up at https://resend.com (3000 emails/month free)
2. Create an API key
3. Set `RESEND_API_KEY` and `NOTIFY_EMAIL` in `backend/.env`
4. For prod: verify a domain and update `RESEND_FROM` to use it

If `RESEND_API_KEY` is empty, emails are logged to the backend console instead of being sent — useful for local dev.

### Slack

1. Create a Slack incoming webhook: https://api.slack.com/messaging/webhooks
2. Set `SLACK_WEBHOOK_URL` in `backend/.env`
3. On each key, choose "Slack" or "Both" as the notify channel

## Testing the reminder pipeline

The dashboard has a **"Trigger check"** button that runs the daily check on demand. To test end-to-end:

1. Add a key with an expiration date in the next 14 days
2. Click "Trigger check"
3. Look at the backend logs — if Resend is configured, you'll receive the email. Otherwise the rendered HTML is logged.

You can also hit `POST /api/_run_check` directly (must be logged in).

## How rotation works

When you receive a reminder email:

1. Click **"Rotate on Anthropic"** (or whichever provider) → opens the provider's console in a new tab
2. Generate the new key, paste it into your secrets (Doppler, your `.env`, etc.)
3. Back in the email, click **"I rotated it"** → lands on a small form to set the new expiration date
4. The notification schedule resets — you'll be pinged again as the new date approaches

You can also rotate from the dashboard by clicking "Rotated" on a key row.

## Deployment

The project ships with a full Docker setup (backend + frontend build + internal nginx) that fits behind any existing reverse proxy. See [DEPLOY.md](./DEPLOY.md) for a step-by-step guide to deploying on a server with an existing nginx (the example walks through wiring it under a subdomain via a shared Docker network).

For simpler hosts (Railway, Fly.io, Render): the `docker-compose.yml` works out of the box if you adjust the `web` network to be internal or remove the nginx service and expose the backend directly.

Set `APP_BASE_URL` and `BACKEND_BASE_URL` in `backend/.env` to your real URLs so email links point to the right place.

## File layout

```
backend/
├── main.py              FastAPI app + lifespan
├── config.py            Settings from .env
├── db.py                SQLite engine + session
├── models.py            APIKey table
├── auth.py              Cookie session + rotation token (itsdangerous)
├── providers.py         Provider registry with rotation URLs
├── scheduler.py         Daily cron job (APScheduler)
├── routes/
│   ├── auth.py          login/logout/me
│   ├── keys.py          CRUD + rotate
│   └── rotate.py        Public rotation page (token-based)
├── notifications/
│   ├── email.py         Resend integration + HTML template
│   └── slack.py         Slack webhook
└── templates/
    ├── rotate.html      Rotation form (server-rendered for email links)
    └── rotated.html     Confirmation page

frontend/
├── src/
│   ├── App.tsx          Routes + auth guard
│   ├── lib/api.ts       API client (fetch wrapper)
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   └── KeyForm.tsx  Used for both create and edit
│   └── components/Layout.tsx
└── vite.config.ts       Proxies /api and /rotate to backend in dev
```

## What's not in V1 (deliberately)

- Multi-user / multi-tenant — single password, single notification email
- Auto-discovery from provider admin APIs — manual entry for everyone, works for all providers
- Push to Doppler/Vercel/etc. — you rotate in the provider console, paste into your secrets manager yourself
- SMS / Discord / Telegram — easy to add following the `notifications/` pattern

## Why this exists

See the design rationale in the conversation that spawned this — the short version is:
1. Doppler/Infisical can rotate AWS/GCP/databases automatically because those providers have admin APIs
2. They cannot rotate Anthropic, Mistral, Vercel, etc., because those providers don't expose admin APIs
3. So "automatic rotation" is not solvable from the secrets-manager side for the majority of providers most indie devs use
4. The realistic protection is: set expirations + get reminded + rotate manually in 5 minutes when pinged
5. That's what this app is
