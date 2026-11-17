"""Lightweight stand-ins for the heavy models so the tests run offline in seconds."""
import json

import numpy as np


class FakeEmbedder:
    """Topic-aware toy embedding: texts mentioning 'alpha' / 'beta' / 'gamma' get distinct directions."""
    dim = 4
    TOPICS = ["alpha", "beta", "gamma"]

    def _vec(self, text: str) -> list[float]:
        v = np.zeros(self.dim)
        for i, t in enumerate(self.TOPICS):
            if t in text.lower():
                v[i] = 1.0
        v[3] = 0.05
        return (v / np.linalg.norm(v)).tolist()

    def embed_passages(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


class FakeLLM:
    def complete(self, system, user, *, json_mode=False, max_tokens=1500):
        if "extract structured information" in system:
            if "ship the release" in user:
                return json.dumps({
                    "decisions": [{"decision": "Ship the release on Friday", "rationale": "QA is done"}],
                    "action_items": [{"task": "Update the changelog", "owner": "Speaker 2", "deadline": "by Thursday"}],
                })
            return "```json\n" + json.dumps({"decisions": [], "action_items": []}) + "\n```"
        if "summaries of consecutive parts" in system:
            return json.dumps({"title": "Release planning", "summary": "The team planned the release.", "topics": ["release", "QA"]})
        if "main points" in system:
            return "They discussed the plan."
        return "Short summary of the excerpt."


class FakeIndex:
    """In-memory stand-in for MeetingIndex (cosine similarity), so most tests need no Qdrant."""

    def __init__(self, embedder):
        self.embedder = embedder
        self.rows = []  # (meeting_id, chunk, vector)

    def upsert_chunks(self, meeting_id, chunks):
        self.rows = [r for r in self.rows if r[0] != meeting_id]
        texts = [f"{c.summary or ''}\n{c.text}".strip() for c in chunks]
        self.rows += [(meeting_id, c, v) for c, v in zip(chunks, self.embedder.embed_passages(texts))]

    def search(self, query, meeting_id=None, limit=5):
        from meeting_intel.schemas import SearchHit

        q = np.asarray(self.embedder.embed_query(query))
        scored = [
            (float(q @ np.asarray(v)), mid, c)
            for mid, c, v in self.rows
            if meeting_id is None or mid == meeting_id
        ]
        scored.sort(key=lambda t: t[0], reverse=True)
        return [
            SearchHit(meeting_id=mid, chunk_id=c.id, score=s, start=c.start, end=c.end,
                      speakers=c.speakers, text=c.text, summary=c.summary)
            for s, mid, c in scored[:limit]
        ]

    def delete_meeting(self, meeting_id):
        self.rows = [r for r in self.rows if r[0] != meeting_id]
