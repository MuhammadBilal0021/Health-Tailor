# Security

This repository is a graduation/portfolio prototype. Security controls are implemented and tested, but it has not undergone an independent penetration test.

## Implemented controls

- Password hashes use scrypt with individual random salts; plaintext passwords are not stored.
- Session tokens are random, hashed in the database, and issued as HttpOnly, SameSite=Lax cookies. Secure cookies are the default.
- Authenticated mutations require a session-bound CSRF token. Origin checks support an exact allowlist for reverse-proxy deployments.
- Server-side role and ownership checks protect administrative actions and kitchen/order access.
- Pydantic bounds request fields; database constraints and transactions protect financial invariants.
- PostgreSQL-backed rate buckets limit login, signup, and AI requests across instances.
- AI credentials are backend-only. Uploaded images are limited by byte size, format, and pixel dimensions.
- The API does not return password hashes, session hashes, or provider keys. Responses disable caching.

## Deployment responsibilities and current limits

Use HTTPS, separate production and preview databases, restricted database accounts, backups, provider spending limits, and an appropriate retention policy. Do not enter real health information into the public browser demo. Real personal-data collection requires a suitable privacy notice and operational review.

Account recovery, verified email ownership, MFA, account deletion/export, comprehensive audit logs, and automated security scanning are not implemented. Login limits are per email and signup limits use the request peer address; proxy behavior and abuse controls need deployment-specific review. Rate-bucket rows currently need operator-managed retention. The Content-Length check supplements schema/image limits; it is not a streaming upload gateway. Collection endpoints need pagination before larger deployments.

Credit approval is not payment verification. This application must not be treated as a bank wallet, payment processor, medical device, or allergy-safety system.

No credentials from the original project are included in this migration. If any original credentials were ever publicly exposed, their owner should revoke/rotate them; deleting a file does not invalidate a key.

## Reporting

Use GitHub's private vulnerability reporting if enabled. Otherwise contact the repository owner privately before sharing sensitive reproduction details. Do not post secrets or personal information in public issues.
