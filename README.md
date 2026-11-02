<p align="center"><img src="docs/banner.svg" alt="Health Tailor — Good food. A better fit for you." width="100%"></p>

<p align="center">
  <a href="https://github.com/MuhammadBilal0021/Health-Tailor/actions/workflows/tests.yml"><img src="https://github.com/MuhammadBilal0021/Health-Tailor/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python 3.11 or newer">
  <img src="https://img.shields.io/badge/Flask-Web_application-233e34?logo=flask&logoColor=white" alt="Flask web application">
  <img src="https://img.shields.io/badge/Status-Graduation_project-bd623e" alt="Graduation project">
</p>

# Health Tailor

**A web application connecting personal dietary preferences with food discovery and restaurant ordering.**

Choosing a meal can involve more than price and convenience. People may want to consider ingredients, spice preferences, and health considerations, yet those decisions often happen separately from the ordering experience. Health Tailor brings a personal profile, optional AI-assisted meal exploration, restaurant menus, and order tracking into one application.

This is my graduation project, developed to explore a practical intersection of **full-stack engineering, AI integration, and user-focused product design**. It demonstrates an end-to-end ordering workflow while making the limits of AI-generated food suggestions explicit.

[Try locally](#quick-start) · [Features](#features) · [Architecture](docs/architecture.md) · [Security notes](SECURITY.md) · [Changes](CHANGELOG.md)

## Quick start

The default demo runs **without Firebase credentials, an API key, or an email account**.

```sh
git clone https://github.com/MuhammadBilal0021/Health-Tailor.git
cd Health-Tailor
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```sh
# macOS / Linux
source .venv/bin/activate
```

Then install and run:

```sh
python -m pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** and select **Explore the demo**.

### A two-minute walkthrough

1. Enter the customer demo with fictional profile data and PKR 5,000 in test credit.
2. Browse **The Green Table**, a fictional restaurant with sample dishes.
3. Add a meal to your cart and check out with a fictional delivery address.
4. Open your orders to inspect the order details or cancel a pending order.
5. Visit the meal explorer to see its consent controls and honest unavailable state when AI is disabled.

Demo data is shared within one process and resets on restart. No actual payments, emails, or AI requests are sent. Use fictional information only. The illustration above is a project banner, not an application screenshot.

## Features

| Area | What it does |
| --- | --- |
| Customer profile | Records food preferences and optional health considerations |
| Restaurant discovery | Lists restaurants, categories, cities, and menus |
| Cart and checkout | Checks current menu availability and prices, then creates an order with a wallet debit |
| Order lifecycle | Tracks pending, confirmed, preparing, ready, delivered, and cancelled states |
| Wallet ledger | Records recharge approvals, checkout debits, cancellation refunds, and restaurant settlement |
| Restaurant workspace | Supports menus, availability, orders, gallery, reviews, and profile management |
| Administration | Provides customer/restaurant approval and wallet request review |
| Optional AI | Uses Gemini for photo-based dish exploration and food ideas after explicit consent |
| Local demo | Offers an easy way to explore the customer journey with fictional data |

**Scope:** wallet balances are application ledger records. There is no integrated payment gateway or bank-transfer execution. AI output is an estimate; the app cannot verify allergens, ingredients, nutrition measurements, or medical suitability from a photo.

## Engineering highlights

- **Atomic state changes:** checkout, recharge approval, cancellation, and settlement update related records in one transaction. Repeated recharge approvals cannot credit a wallet again.
- **Controlled order transitions:** completed and cancelled orders cannot be moved back into active states.
- **Current-price validation:** checkout re-reads menu prices and availability rather than trusting an old cart snapshot.
- **Failure isolation:** email notification failures do not undo a successful order update or prevent restaurant settlement.
- **Password hashing and configuration:** account passwords are hashed; cloud credentials and administrator configuration are loaded from the environment.
- **CSRF protection:** state-changing requests require a session-bound token.
- **Honest AI behavior:** unavailable results stay unavailable. The app does not invent a dish or display fixed nutrition percentages as measured analysis.
- **Regression coverage:** tests exercise permissions, rendering, checkout, refunds, duplicate approval, settlement, and AI failure behavior.

## Stack and structure

| Layer | Technology |
| --- | --- |
| Web application | Python, Flask, Jinja |
| Interface | HTML, CSS, JavaScript; existing dashboard templates use Tailwind CDN |
| Live database | Firebase Realtime Database through the Admin SDK |
| Local demo | In-memory adapter implementing the database operations used by the app |
| Optional AI | Google Gen AI Python SDK / Gemini |
| Optional email | SMTP through yagmail |
| Testing | Python unittest, Flask test client, GitHub Actions |

```text
Health-Tailor/
├── app.py                 # Routes and application workflows
├── runtime.py             # Environment configuration, demo data, adapters
├── transactions.py        # Atomic order and wallet operations
├── templates/             # Customer, restaurant, and admin views
├── static/                # Styles, scripts, and original SVG artwork
├── tests/                 # Offline regression tests
├── docs/                  # Architecture and project banner
├── .env.example           # Configuration names; no credentials
└── .github/workflows/      # Continuous integration
```

See [architecture and tradeoffs](docs/architecture.md) for the transaction design and planned refactoring.

## Tests

```sh
python -m unittest discover -s tests -v
```

The suite runs offline in demo mode. It covers public/customer/restaurant/admin page rendering and template syntax, password hashing, CSRF rejection, concurrent recharge replay, current-price checkout, single refunds, legal order transitions, and repeat settlement protection.

The browser-based visual review was not completed in this environment. Live Firebase, SMTP, and Gemini integrations require separate integration testing with newly configured credentials; passing offline tests does not establish production readiness.

## Configure live integrations

Start with a **new test Firebase project**, not personal or production data.

```sh
python -m pip install -r requirements-live.txt
```

Copy `.env.example` to `.env` and set:

| Variable | Purpose |
| --- | --- |
| `APP_MODE=live` | Enable persistent Firebase storage |
| `SECRET_KEY` | Random session-signing secret of at least 32 characters |
| `FIREBASE_CREDENTIALS` | Absolute path to a service-account JSON file outside this repository |
| `FIREBASE_DATABASE_URL` | Your Firebase Realtime Database URL |
| `ADMIN_EMAIL` | Administrator sign-in email |
| `ADMIN_PASSWORD_HASH` | Werkzeug password hash for the administrator |
| `GEMINI_API_KEY` | Optional key for AI requests |
| `GEMINI_MODEL` | Configurable model name; default is `gemini-2.5-flash` |
| `SMTP_USER`, `SMTP_PASSWORD` | Optional email configuration |
| `COOKIE_SECURE=true` | Set when serving through HTTPS |

Generate a session secret locally:

```sh
python -c "import secrets; print(secrets.token_hex(32))"
```

Generate an administrator password hash without placing the password in shell history:

```sh
python -c "from getpass import getpass; from werkzeug.security import generate_password_hash; print(generate_password_hash(getpass('Admin password: ')))"
```

Keep these values local. Never commit `.env`, service-account files, or uploaded personal data. Credentials included in earlier archives must be revoked and replaced. Existing plaintext password records must be reset; plaintext login is deliberately unsupported.

For a controlled live-mode evaluation, a WSGI server is available with the optional dependencies:

```sh
waitress-serve --listen=127.0.0.1:5000 app:app
```

This is not a complete deployment recipe. Review [SECURITY.md](SECURITY.md) before exposing the app to users. The current root-transaction design favors correctness for a small prototype over large-scale throughput.

## What comes next

- Verified ingredient, portion, and allergen information supplied by restaurants.
- Arabic localization and right-to-left layouts.
- A real payment provider with verified webhooks and reconciliation.
- Broader mobile, accessibility, and browser test coverage.
- Route blueprints, distributed rate limiting, audit trails, and background email delivery.

These are planned improvements, not claims about current capabilities.

## Author

**Muhammad Bilal** · [GitHub](https://github.com/MuhammadBilal0021)

Graduation project focused on connecting a real user need with practical software engineering. See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidance.
