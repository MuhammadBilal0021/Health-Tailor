# Changelog

## 2.0.0 — Modern full-stack migration

- Rebuilt the interface with Next.js, React, and strict TypeScript.
- Added bilingual English/Arabic layouts, responsive discovery, and original SVG meal illustrations.
- Implemented customer, kitchen, and administrator workflows in browser demo and connected modes.
- Introduced FastAPI, SQLAlchemy, PostgreSQL, and Alembic migrations.
- Added opaque sessions, CSRF checks, server authorization, transactional checkout, refunds, settlement, and credit approval.
- Added opt-in AI meal exploration with explicit unavailable responses.
- Added domain/API tests, PostgreSQL CI, Docker Compose, and Vercel deployment instructions.
- Preserved the Flask/Firebase version on `legacy-flask`; no Firebase records or balances are migrated automatically.
