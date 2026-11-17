"""Semantic search over meeting chunks with Qdrant (embedded mode by default, server optional)."""
from __future__ import annotations

import uuid
from pathlib import Path

from .embed import Embedder
from .schemas import Chunk, SearchHit

COLLECTION = "meeting_chunks"


class MeetingIndex:
    def __init__(self, embedder: Embedder, path: Path | None = None, url: str | None = None):
        self.embedder = embedder
        self.path, self.url = path, url
        self._client = None

    def _get(self):
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
        return [
            SearchHit(
                meeting_id=p.payload["meeting_id"], chunk_id=p.payload["chunk_id"], score=float(p.score),
                start=p.payload["start"], end=p.payload["end"], speakers=p.payload["speakers"],
                text=p.payload["text"], summary=p.payload.get("summary"),
            )
            for p in res.points
        ]

    def delete_meeting(self, meeting_id: str) -> None:
        from qdrant_client import models

        flt = models.Filter(must=[models.FieldCondition(key="meeting_id", match=models.MatchValue(value=meeting_id))])
        self._get().delete(COLLECTION, points_selector=models.FilterSelector(filter=flt))
