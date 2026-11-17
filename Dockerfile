# Pin the Python patch release and Debian base family for more predictable builds.
FROM python:3.15.2-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOME=/home/app \
    HF_HOME=/home/app/.cache/huggingface \
    XDG_CACHE_HOME=/home/app/.cache

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install application dependencies before copying source for better layer caching.
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY pyproject.toml README.md ./
COPY meeting_intel ./meeting_intel
COPY ui ./ui
RUN python -m pip install --no-deps -e . \
    && groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --create-home --home-dir /home/app --shell /usr/sbin/nologin app \
    && mkdir -p /app/data /home/app/.cache/huggingface /home/app/.streamlit \
    && chown -R app:app /app /home/app

USER 10001:10001

EXPOSE 8000 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "meeting_intel.api:app", "--host", "0.0.0.0", "--port", "8000"]
