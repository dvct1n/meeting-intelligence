from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:  # optional: load a local .env file
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass


def _opt(name: str) -> str | None:
    v = os.getenv(name, "").strip()
    return v or None


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    # speech recognition
    whisper_model: str
    whisper_language: str | None
    # diarization
    diarize: bool
    diarization_model: str
    hf_token: str | None
    # embeddings / vector store
    embedding_model: str
    qdrant_path: Path
    qdrant_url: str | None
    # LLM
    llm_provider: str  # "openai" (any OpenAI-compatible server) | "anthropic"
    llm_model: str
    llm_base_url: str | None
    llm_api_key: str | None
    # chunking
    chunk_max_chars: int
    chunk_min_chars: int
    # service
    max_upload_mb: int = 500
    api_key: str | None = None  # when set, every endpoint except /health requires `X-API-Key`
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        data_dir = Path(os.getenv("DATA_DIR", "data"))
        return cls(
            data_dir=data_dir,
            whisper_model=os.getenv("WHISPER_MODEL", "openai/whisper-small"),
            whisper_language=_opt("WHISPER_LANGUAGE"),
            diarize=os.getenv("DIARIZE", "true").lower() in {"1", "true", "yes"},
            diarization_model=os.getenv("DIARIZATION_MODEL", "pyannote/speaker-diarization-3.1"),
            hf_token=_opt("HF_TOKEN"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small"),
            qdrant_path=Path(os.getenv("QDRANT_PATH", str(data_dir / "qdrant"))),
            qdrant_url=_opt("QDRANT_URL"),
            llm_provider=os.getenv("LLM_PROVIDER", "openai").lower(),
            llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            llm_base_url=_opt("LLM_BASE_URL"),
            llm_api_key=_opt("LLM_API_KEY"),
            chunk_max_chars=int(os.getenv("CHUNK_MAX_CHARS", "3500")),
            chunk_min_chars=int(os.getenv("CHUNK_MIN_CHARS", "600")),
            max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "500")),
            api_key=_opt("API_KEY"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
