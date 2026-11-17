"""Semantic search over meeting chunks with Qdrant (embedded mode by default, server optional)."""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .embed import Embedder
from .schemas import Chunk, SearchHit

if TYPE_CHECKING:
    from qdrant_client import QdrantClient

COLLECTION = "meeting_chunks"


def _payload_to_search_hit(payload: dict[str, Any] | None, score: float) -> SearchHit | None:
    """Convert a Qdrant payload into a validated hit.

    Qdrant allows points without payloads, and older or manually edited
    collections may contain incomplete payloads. Skip those records instead
    of failing the entire search request.
    """
    if payload is None:
        return None

    try:
        return SearchHit(
            meeting_id=payload["meeting_id"],
            chunk_id=payload["chunk_id"],
            score=float(score),
            start=payload["start"],
            end=payload["end"],
            speakers=payload["speakers"],
            text=payload["text"],
            summary=payload.get("summary"),
        )
    except (KeyError, TypeError, ValueError):
        # An incomplete or malformed point should not break other search hits.
        return None


class MeetingIndex:
    def __init__(self, embedder: Embedder, path: Path | None = None, url: str | None = None):
        self.embedder = embedder
        self.path, self.url = path, url
        # Keep the Qdrant import lazy while giving mypy the concrete attribute type.
        self._client: QdrantClient | None = None

    def _get(self) -> QdrantClient:
        if self._client is None:
            from qdrant_client import QdrantClient, models

            if self.url:
                client = QdrantClient(url=self.url)
            else:
                path = Path(self.path or "data/qdrant")
                path.mkdir(parents=True, exist_ok=True)
                client = QdrantClient(path=str(path))
            if not client.collection_exists(COLLECTION):
                client.create_collection(
                    COLLECTION,
                    vectors_config=models.VectorParams(size=self.embedder.dim, distance=models.Distance.COSINE),
                )
            self._client = client
        # The lazy initialization above guarantees a client at this point.
        assert self._client is not None
        return self._client

    @staticmethod
    def _point_id(meeting_id: str, chunk_id: int) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{meeting_id}:{chunk_id}"))

    def upsert_chunks(self, meeting_id: str, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        from qdrant_client import models

        # embed summary + raw text so that both high-level and detailed queries match
        texts = [f"{c.summary or ''}\n{c.text}".strip() for c in chunks]
        vectors = self.embedder.embed_passages(texts)
        points = [
            models.PointStruct(
                id=self._point_id(meeting_id, c.id),
                vector=v,
                payload={
                    "meeting_id": meeting_id, "chunk_id": c.id, "start": c.start, "end": c.end,
                    "speakers": c.speakers, "text": c.text, "summary": c.summary,
                },
            )
            for c, v in zip(chunks, vectors)
        ]
        self._get().upsert(COLLECTION, points=points)

    def search(self, query: str, meeting_id: str | None = None, limit: int = 5) -> list[SearchHit]:
        from qdrant_client import models

        flt = None
        if meeting_id:
            flt = models.Filter(must=[models.FieldCondition(key="meeting_id", match=models.MatchValue(value=meeting_id))])
        res = self._get().query_points(
            COLLECTION, query=self.embedder.embed_query(query), limit=limit, query_filter=flt, with_payload=True
        )
        hits: list[SearchHit] = []
        for point in res.points:
            hit = _payload_to_search_hit(point.payload, point.score)
            if hit is not None:
                hits.append(hit)
        return hits

    def delete_meeting(self, meeting_id: str) -> None:
        from qdrant_client import models

        flt = models.Filter(must=[models.FieldCondition(key="meeting_id", match=models.MatchValue(value=meeting_id))])
        self._get().delete(COLLECTION, points_selector=models.FilterSelector(filter=flt))
