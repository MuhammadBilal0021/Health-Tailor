# Deploying Health Tailor

## Option A — Portfolio demo on Vercel

This is the quickest deployment and is sufficient for an interactive recruiter walkthrough.

1. Import `MuhammadBilal0021/Health-Tailor` in Vercel.
2. Set **Root Directory** to **`frontend`** and framework to **Next.js**.
3. Use Node.js 22, install command `npm ci`, and build command `npm run build`. Leave output directory at its framework default.
4. Leave `NEXT_PUBLIC_API_ENABLED` unset or set it to `false`. Do not set `BACKEND_URL`.
5. Deploy. Test `/explore`, `/cart`, `/orders`, `/restaurant`, `/admin`, and Arabic switching.
6. Add the resulting URL to GitHub's About/website field and your CV. There is deliberately no invented deployment URL in this README.

In this mode, all demo state is local to the browser; resetting the demo clears its fictional activity. Login is explicitly disabled, AI sends nothing, and no database or API key is required. The root `vercel.json` is for Option B, not this frontend-only project.

## Option B — Next.js and FastAPI in one Vercel project

[Vercel Services](https://vercel.com/docs/services) supports multiple frameworks with shared routing and is currently **Beta**. The root `vercel.json` routes `/api/*` to FastAPI and other paths to Next.js. Follow the current Vercel Services onboarding if the dashboard requires enabling the feature.

1. Provision an external PostgreSQL database and obtain its TLS connection URL. Prefer the provider's pooled URL for runtime and direct URL for migrations if its documentation requires that distinction.
2. Initialize the schema from your machine or a controlled release job using the commands below. Do not run migrations during every serverless request.
3. Import the repo with **Root Directory `.`** so Vercel sees `vercel.json` and both services. Avoid top-level framework, output, or build overrides; each service has its own framework configuration.
4. Set the following project environment variables, then deploy:

| Variable | Value |
| --- | --- |
| `NEXT_PUBLIC_API_ENABLED` | `true` (build-time frontend flag; redeploy after changing) |
| `DATABASE_URL` | PostgreSQL connection URL with TLS; backend secret |
| `APP_ENV` | `production` |
| `COOKIE_SECURE` | `true` |
| `FRONTEND_ORIGINS` | Exact public frontend origin, e.g. `https://your-project.vercel.app`; comma-separated exact origins if necessary |
| `GEMINI_API_KEY` | Optional backend secret; omit to disable AI |
| `GEMINI_MODEL` | Optional available model ID; default `gemini-2.5-flash` |

Leave `BACKEND_URL` **unset** for the shared-domain Services deployment; root routing already handles the API. Only `NEXT_PUBLIC_API_ENABLED` is public. Never prefix database/provider secrets with `NEXT_PUBLIC_`. Keep preview and production databases separate.

### Initialize the live database

From `backend/`, install the Python requirements in a virtual environment and set `DATABASE_URL` in your shell to the database you intend to initialize. `.env.example` is documentation; the Python CLI does not automatically load it.

```bash
python -m venv .venv
# Activate .venv using your shell's activation command.
pip install -r requirements.txt
alembic upgrade head
alembic check
# Optional fictional catalog; safe to repeat, existing records are preserved.
python manage.py seed-catalog
python manage.py create-user --email YOUR_ADMIN_EMAIL --name "Administrator" --role admin
```

Create a restaurant owner via signup, or use `create-user --role restaurant --kitchen r1` to assign an unowned seeded kitchen. The administrator approves signup-created kitchens. Customers start at zero credit and use the prototype credit-request flow. Seeding never creates passwords or credits. Run `python manage.py cleanup-sessions` periodically to remove expired sessions.

### Verify the deployment

- `/api/health` returns version and configuration presence; it is not a database readiness check.
- `/api/docs` displays the OpenAPI reference.
- Create a disposable customer, sign out and back in, request test credit, and approve it as administrator.
- Place one order, verify customer/restaurant ownership, and complete delivery.
- Reload the page to confirm orders persist in PostgreSQL. The current live cart resets on a full reload.
- If AI is configured, verify a consented fictional request and monitor provider cost. The repository tests error paths; they do not call a paid provider.

## Option C — Separate API host

Deploy `frontend/` on Vercel and `backend/` on a Python host. Set `NEXT_PUBLIC_API_ENABLED=true` and `BACKEND_URL=https://YOUR_API_HOST` on the frontend before building. The Next.js rewrite proxies `/api/*`, retaining same-origin browser cookies. Set the backend's `FRONTEND_ORIGINS` to the exact browser-facing Vercel domain. Use HTTPS and secure cookies.

## Native local development

Two terminals, with commands run from the respective directories:

```powershell
# backend/ — PowerShell, Python 3.11 or 3.12
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:DATABASE_URL='sqlite:///healthtailor-local.db'
$env:APP_ENV='development'
$env:COOKIE_SECURE='false'
$env:FRONTEND_ORIGINS='http://localhost:3000'
alembic upgrade head
python manage.py seed-catalog
uvicorn main:app --reload --port 8000
```

```powershell
# frontend/
Copy-Item .env.example .env.local
# Edit .env.local: NEXT_PUBLIC_API_ENABLED=true
npm ci
npm run dev
```

Open `http://localhost:3000` consistently (not a mixture of localhost and 127.0.0.1). SQLite is useful for local development but does not provide PostgreSQL row-lock semantics. Production configuration rejects SQLite. Neither uploads nor databases are stored on Vercel's ephemeral filesystem.

## Troubleshooting

- **Demo works but login is disabled:** enable the public API flag and rebuild; make sure the backend is deployed.
- **503 database not configured:** set the backend database environment variable and run migrations.
- **403 cross-origin write:** configure the exact browser origin, without a path, in `FRONTEND_ORIGINS`.
- **401 after local login:** localhost needs `COOKIE_SECURE=false`; production HTTPS needs `true`.
- **AI unavailable:** absent keys/provider failures intentionally return 503 rather than fake nutrition results.
- **New kitchen missing:** administrator approval is required before it appears in discovery.
- **Build memory pressure:** the project limits static-generation workers to two.

Services configuration follows the [official overview](https://vercel.com/docs/services). Its Beta status means hosting settings may evolve; frontend-only deployment remains independent of Services.
