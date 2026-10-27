---
name: secret-scan
description: Scanning the repository and the logs for credentials, tokens and keys (NFR-SEC-005, hard constraint "no credentials in the repo"). Use before every commit that touches config or scripts, before a pull request, and before the final submission.
---

# Secret scan

Why: the repo is public-facing and ships `code/.env.example` with variable names only. `.env` and `.env.*` are git-ignored. The JobDiva token stays in memory and is never logged. The scan covers files **and** history, and the logs.

Steps:
1. **Tool.** Prefer `gitleaks` (`winget install gitleaks`); alternatives are `detect-secrets` or `trufflehog`. Install only with the user's agreement. If none is available, fall back to Grep over tracked files for the patterns below and say the check is weaker.
2. **Working tree and history.** `gitleaks detect --source . --redact` (history) and `gitleaks detect --no-git --source . --redact` (files). Always use `--redact`: never print a secret value in the result.
3. **Patterns for the Grep fallback.** `sk-ant-`, `ANTHROPIC_API_KEY=` with a value, `JOBDIVA_API_PASSWORD=` with a value, `postgresql://user:password@` with a real password, `-----BEGIN`, `Bearer `, long base64 or hex strings next to `key`, `token`, `secret`, `password`. Ignore the placeholders in `.env.example` (`<DB_APP_PASSWORD>` and empty values).
4. **Ignored files.** Confirm with `git check-ignore code/.env` that `.env` is ignored and `git ls-files | grep -i "\.env"` lists only `.env.example`.
5. **Logs and responses.** Grep `code/logs/` and the audit log for the sandbox token and the API key; the NFR-SEC-005 case also checks that a failing JobDiva call does not log the token. `code/logs/` is local and is not committed.
6. **Result.** Any finding blocks: report file, line and rule, **never the value**. A real secret that reached a commit means the key must be revoked and rotated by its owner; history rewriting is a decision for the user. Save a clean or findings summary (no values) in `code/tests/evidence/secret-scan-<date>.txt`.

Do not open, print or copy `code/.env`.
