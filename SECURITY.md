# Security policy

## Reporting a vulnerability

Please **do not** open a public issue for security problems. Use GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
("Security" tab → "Report a vulnerability") on this repository. Include a description, steps to reproduce and the affected version. You can expect an acknowledgement within a few days.

## Scope and deployment notes

- The API ships with optional shared-secret authentication (`API_KEY` → `X-API-Key`). There are no user accounts or per-meeting permissions; do not expose the service to the internet without HTTPS and a reverse proxy.
- Uploads are limited by `MAX_UPLOAD_MB` and by file extension; files are processed by `ffmpeg`, so keep it up to date.
- Meeting ids are validated to stay inside `DATA_DIR`.
- Transcript text is sent to the configured LLM provider. Use a local model if recordings must not leave your infrastructure.
- Never commit `.env`, API keys, Hugging Face tokens, private keys, service-account files, meeting audio/video, private transcripts, logs, or vector/database files. `.gitignore` and `.dockerignore` cover common cases, but review the staged diff before every push.
- If a credential is ever committed, revoke/rotate it immediately; deleting the file or adding it to `.gitignore` does not remove it from Git history. See [the publication checklist](docs/github_release_checklist.md).
