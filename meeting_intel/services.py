from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .config import Settings, get_settings
from .embed import SentenceTransformerEmbedder
from .index import MeetingIndex
from .llm import build_llm
from .pipeline import MeetingPipeline
from .storage import MeetingStore


@dataclass
class Services:
    settings: Settings
    store: MeetingStore
    index: MeetingIndex
    pipeline: MeetingPipeline


@lru_cache(maxsize=1)
def get_services() -> Services:
    s = get_settings()
    store = MeetingStore(s.data_dir)
    embedder = SentenceTransformerEmbedder(s.embedding_model)
    index = MeetingIndex(embedder, path=s.qdrant_path, url=s.qdrant_url)
    pipeline = MeetingPipeline(s, store, index, build_llm(s), embedder)
    return Services(s, store, index, pipeline)
