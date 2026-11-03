# Contributing

Use Node.js 22 and Python 3.11/3.12. Run the checks in the README before proposing a change. Format frontend code with `npm run format` and backend code with `ruff format .`; keep generated build output, environment files, databases, and credentials out of commits.

Add behavior tests for changes to checkout, authorization, refunds, or settlement. Use an isolated database for tests: `TEST_DATABASE_URL` points to disposable tables that the suite creates and drops. Never point it at a real deployment.

Database changes require a reviewed Alembic migration. Keep English and Arabic interface text together and verify narrow layouts. Describe what changed, why, and how it was validated in the pull request.
