# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- Corrected the TOML scope of `project.dependencies` in `pyproject.toml`, restoring editable package installation and the CI test matrix.
- Made the settings path test platform-independent by using pytest's native temporary directory instead of asserting POSIX path separators; this fixes the Windows-only test failure.

## [0.2.1] - 2026-11-17

### Added
- Offline sample-meeting walkthrough that validates the fixture, displays the stored analysis, runs transparent keyword-overlap search, and exports Markdown.
- Gitleaks GitHub Actions workflow for push, pull request, manual and scheduled secret scanning.
- Release publication checklist, reproducibility guidance and citation metadata.

### Changed
- Updated GitHub links and badges for `dvct1n/meeting-intelligence`.
- Pinned Docker base images, run application containers as non-root, use read-only root filesystems where practical, and keep published ports on localhost.
- Updated CI actions to current major releases and run the offline demos in CI.

## [0.2.0]

### Added
- `meeting-intel` command-line interface: `process`, `list`, `show`, `search`, `delete`, plus `wer`, `eval-search` and `eval-items` evaluation commands.
- Markdown export (`GET /meetings/{id}/export`, CLI, download button in the UI).
- Dependency-free evaluation metrics (WER, Recall@k, action-item precision/recall/F1) and evaluation guide.
- Optional API-key authentication, upload size limit (`MAX_UPLOAD_MB`), `/health` version, start-up recovery of interrupted jobs.
- LLM call retries with exponential back-off.
- `pyproject.toml` packaging with `ml` / `ui` / `dev` extras, ruff + mypy configuration, Makefile, pre-commit.
- GitHub Actions CI (lint, type-check, tests on Python 3.10–3.12), Dependabot, issue / PR templates.
- Tests for the LLM wrapper, analysis, storage, export, metrics, config, audio, CLI and API; in-memory fake index so most tests need no Qdrant.
- Docs: architecture, evaluation method, Vietnamese README, SECURITY, CONTRIBUTING, synthetic example report.

### Changed
- UI auto-refreshes only while a meeting is processing; sends `X-API-Key` when `API_KEY` is set.
- Search requests are validated (`1 ≤ limit ≤ 50`, query ≤ 1000 chars).
- `DELETE /meetings/{id}` returns `404` for unknown ids and `409` while processing.
- Docker image no longer copies the whole build context; added `.dockerignore`, health check, optional Qdrant service.

### Fixed
- Meeting ids are validated, so `..` or path separators can no longer reach files outside the data directory (previously `DELETE` could remove the wrong folder).
- `meeting.json` is written atomically.

## [0.1.0]

- Initial pipeline: Whisper ASR, pyannote diarization, speaker alignment, topic segmentation, LLM analysis, Qdrant semantic search, FastAPI and Streamlit.
