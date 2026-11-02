# Changelog

## Portfolio edition

- Added a responsive landing page, illustrated meal asset, demo entry, and clear error pages.
- Standardized Health Tailor branding and customer currency labels to PKR.
- Added a cloud-free demo with fictional customer, restaurant, menu, and wallet data.
- Removed bundled credentials and moved integration settings to environment variables.
- Replaced plaintext password writes with hashes and rejected legacy plaintext login.
- Added session-bound CSRF protection and an 8 MB upload limit.
- Made checkout, recharge approval, refund, and restaurant settlement transactional.
- Fixed order-status email arguments and separated email failure from payout processing.
- Fixed restaurant order rendering, dictionary item access, and a Jinja syntax error.
- Removed fabricated fallback food analysis and fixed-value nutrition charts.
- Added AI consent controls, regression tests, and GitHub Actions checks.
