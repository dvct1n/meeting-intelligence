# Contributing

Thanks for your interest! Bug reports, ideas and pull requests are welcome. Participation follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## Setup

```bash
git clone https://github.com/dvct1n/meeting-intelligence.git
cd meeting-intelligence
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # light: no models are downloaded
pre-commit install               # optional: ruff + hygiene hooks on commit
make check                       # ruff + mypy + pytest, exactly what CI runs
make demo                        # offline example workflow
make synthetic-eval              # metric fixture calculation
```

Processing real audio needs the ML stack: `pip install -e ".[all,dev]"` and `ffmpeg`.

## Guidelines

- **Tests first for behaviour changes.** Heavy models are never loaded in tests; use the fakes in `tests/fakes.py` and inject them (see `tests/conftest.py`). A test that needs a real model, GPU or network does not belong in the default suite.
- Keep functions small and typed; `mypy meeting_intel` must stay clean.
- New configuration → add it to `config.py`, `.env.example` and the README.
- Never commit recordings, transcripts, `.env` files or API keys (`.gitignore` and the pre-commit hook help, but double-check your diff).
- Use clear commit messages; one logical change per pull request. The Security workflow scans commits and pull requests with Gitleaks; never put real credentials in fixtures or tests.

## Reporting bugs

Use the bug-report template and include versions, models, and logs. Please do not attach confidential recordings; a synthetic or public sample is enough. For security issues, see [SECURITY.md](SECURITY.md) instead of opening a public issue.
