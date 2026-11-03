# Graduation project — application and interview wording

## Brief application answer

My graduation project, Health Tailor, is a full-stack food discovery and ordering platform designed to help people make more informed meal choices based on their preferences and available ingredient information. It connects customer, restaurant, and administrator workflows, including personalized discovery, order tracking, menu management, and controlled credit approvals. The project has evolved from a Flask prototype into a Next.js and TypeScript frontend with a FastAPI and PostgreSQL backend, with English/Arabic support and automated tests. It demonstrates how I approach practical product problems through usable interfaces, secure APIs, and reliable data handling.

## Short CV version

**Health Tailor — Full-stack graduation project:** Developed a preference-based food discovery and ordering prototype using Next.js, TypeScript, FastAPI, and PostgreSQL, with English/Arabic UI, role-based workflows, transactional checkout, idempotent refunds/settlement, automated tests, and Vercel deployment configuration.

## Discuss these choices in an interview

- The problem: users need context about meals, while kitchens need a manageable order workflow.
- The difficult part: preserving correct balances and ownership when requests are repeated or concurrent.
- The solution: server-calculated totals, PostgreSQL transactions/locks, idempotency keys, explicit status transitions, and API integration tests.
- The product judgment: an accessible demo helps reviewers explore the whole system without credentials; live authorization remains server-side.
- The regional adaptation: English/Arabic layouts and SAR sample pricing, without claiming market validation or regulatory compliance.
- The next experiment: interview diners and restaurant operators and measure whether ingredient visibility improves decision confidence.

Use these statements only to the extent that you can explain and demonstrate the implementation. Do not claim production customers, measured health improvements, payment processing, or clinically validated recommendations. Be transparent about tools and assistance used when asked.
