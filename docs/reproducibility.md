# Reproducibility and environment management

This repository currently identifies itself as version 0.2.1 (see `meeting_intel.__version__` and `CHANGELOG.md`). It separates a lightweight development/test environment from the larger optional ML runtime. Model downloads and hardware availability can make full audio-pipeline runs differ across machines; record the environment whenever you publish a real benchmark.

## Recommended local environment

- Python **3.11.18** is the repository's recommended development interpreter (`.python-version`). The source package declares Python 3.10+ and CI checks 3.10, 3.11 and 3.12.
- Install the lightweight developer environment with `python -m pip install -e ".[dev]"`.
- Run `make check` before submitting changes.
- Run `make demo` for the synthetic fixture walkthrough and `make synthetic-eval` for metric-function examples.

## Full ML environment

Install `python -m pip install -e ".[all,dev]"`, install `ffmpeg`, and configure `.env` locally. `HF_TOKEN`, diarization access and LLM credentials are only needed for the relevant real-model stages. Never commit `.env` or downloaded model caches.

For a reproducible experiment, record at minimum:

1. OS, Python version, CPU/GPU model, driver and CUDA version where relevant.
2. The resolved Python package versions (`python -m pip freeze`).
3. Whisper model ID/revision, pyannote model ID/revision, embedding model ID/revision, LLM provider/model and prompt/config revision.
4. Dataset provenance, language, duration, train/dev/test split and annotation protocol.
5. Whether model loading, preprocessing and data transfer are included in latency measurements.

## Dependency locking

`pyproject.toml` is the dependency source of truth and currently uses compatibility ranges for the optional ML stack. A universal lockfile is intentionally not claimed here: dependency resolution must be run on a supported target environment and verified, especially for PyTorch/CUDA and `pyannote.audio`. When preparing a fixed deployment or a benchmark, resolve and commit a lockfile generated in that target environment (for example with `uv lock`), then install with the lock enforced (for example `uv sync --locked`). Do not generate a lock using a different CUDA/runtime target and assume it is portable.

## Model reproducibility

Model names alone may resolve to newer model revisions over time. For published experiments, pin Hugging Face model revisions/commit hashes in your experiment configuration and store the configuration alongside the result table. Do not check model weights into Git; use an artifact store or documented download process.
