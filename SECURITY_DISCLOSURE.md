# Security Disclosure Policy & Guidelines

The DNK OS project takes software security and data privacy with utmost seriousness. This document outlines our disclosure guidelines for the public read-only architecture mirror.

---

## 1. Strictly Forbidden Activities

- **NO SECRETS**: It is strictly forbidden to commit, publish, or submit pull requests containing live API keys, tokens, passwords, private certificates, or customer data.
- **NO LIVE CREDENTIALS**: Do not configure or execute this repository using production credentials or live e-commerce store tokens.
- **NOT A PRODUCTION DEPLOYMENT**: This mirror is intended exclusively for architecture analysis and security peer review. It is not hardened for public facing production deployment.

---

## 2. Reporting a Vulnerability

If you discover any security issue, unintended artifact, or potential vulnerability in this architecture mirror, please report it responsibly:

- **Email:** `security@dnk-e.com`
- **PGP Encryption:** Optional, available upon request.
- **What to include:**
  - Description of the vulnerability or finding.
  - Affected file path and line numbers.
  - Proof of concept or reproduction steps (read-only).
  - Remediation recommendations if available.

Please allow 48 to 72 hours for our security team to investigate and acknowledge your report before making any public disclosure.

---

## 3. Pre-Publication Sanitization Certification

Prior to public mirroring, this repository underwent:
1. Automated secret scanning via **Gitleaks** and custom pattern matching.
2. Complete exclusion of all `.env` files, `.db`/`.sqlite` databases, logs, and build caches.
3. Clean-room git tree initialization with zero inherited history.
4. Quarantine isolation of all third-party and experimental runtime modules.
