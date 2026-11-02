# Security and deployment notes

This is an educational prototype, not a production payment or medical service.

- Never upload service-account files or API keys. Configure them outside the repository.
- Credentials distributed with earlier project archives must be revoked and replaced by the account owner. Removing them here does not invalidate existing copies.
- Existing plaintext password records are deliberately rejected. Use the password-reset workflow with configured email, or recreate test accounts.
- Demo mode uses disposable in-memory fictional data, shared between visitors to one process. It is intended for local review, not personal data collection.
- Live mode needs HTTPS, secure cookies, suitable hosting, independently reviewed access control and Firebase rules, shared rate limiting, monitoring, backups, and data retention policies.
- Wallet amounts are application ledger entries. No payment processor or bank transfer is implemented.
- Report vulnerabilities privately to the repository owner through their GitHub profile; never include real credentials or personal data in a public issue.
