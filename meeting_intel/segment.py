"""Transcript segmentation: group utterances into topic-coherent chunks.

Idea (TextTiling-style): embed every utterance, compare the average embedding of the
`window` utterances before and after each position. A clearly lower similarity than usual
marks a likely topic change. Chunk size limits are always enforced so that each chunk fits
in an LLM prompt.
"""
from __future__ import annotations

import numpy as np

from .embed import Embedder
from .schemas import Chunk, Utterance
from .utils import utterance_line


def topic_boundaries(utts: list[Utterance], embedder: Embedder, window: int = 3, k: float = 0.5) -> set[int]:
    n = len(utts)
    if n < 2 * window + 1:
        return set()
    E = np.asarray(embedder.embed_passages([u.text for u in utts]), dtype=float)
    E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9

    sims: dict[int, float] = {}
    for i in range(1, n):
        left = E[max(0, i - window):i].mean(axis=0)
        right = E[i:i + window].mean(axis=0)
        sims[i] = float(left @ right / (np.linalg.norm(left) * np.linalg.norm(right) + 1e-9))

    vals = np.array(list(sims.values()))
    if vals.std() < 1e-6:
        return set()
    threshold = vals.mean() - k * vals.std()

    # keep only local minima: a real topic change dips at one point, not at its whole neighbourhood
    boundaries: set[int] = set()
    for i, s in sims.items():
        if s >= threshold:
            continue
        before = [sims[j] for j in range(i - window, i) if j in sims]
        after = [sims[j] for j in range(i + 1, i + window + 1) if j in sims]
        if all(s < b for b in before) and all(s <= a for a in after):
            boundaries.add(i)
    return boundaries


def chunk_utterances(
    utts: list[Utterance],
    embedder: Embedder | None = None,
    max_chars: int = 3500,
    min_chars: int = 600,
    window: int = 3,
) -> list[Chunk]:
    bounds = topic_boundaries(utts, embedder, window) if embedder is not None else set()

    chunks: list[Chunk] = []
    cur: list[Utterance] = []
    size = 0

    def flush() -> None:
        nonlocal cur, size
        if not cur:
            return
        chunks.append(
            Chunk(
                id=len(chunks),
                start=cur[0].start,
                end=cur[-1].end,
                speakers=sorted({u.speaker for u in cur}),
                text="\n".join(utterance_line(u) for u in cur),
            )
        )
        cur, size = [], 0

    for i, u in enumerate(utts):
        length = len(utterance_line(u)) + 1
        too_big = size + length > max_chars
        topic_shift = i in bounds and size >= min_chars
        if cur and (too_big or topic_shift):
            flush()
        cur.append(u)
        size += length
    flush()
    return chunks
