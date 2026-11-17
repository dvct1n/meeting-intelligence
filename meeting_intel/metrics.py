"""Dependency-free evaluation metrics, so results can be reproduced without extra installs.

* ``wer``            word error rate for ASR (lower is better)
* ``recall_at_k``    did a relevant chunk appear in the top-k search hits
* ``match_items``    precision / recall / F1 of extracted action items vs a hand-written list
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Sequence


def normalize(text: str) -> list[str]:
    """Lower-case, strip punctuation, split on whitespace (keeps Vietnamese diacritics)."""
    text = unicodedata.normalize("NFC", text).lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return text.split()


def edit_distance(a: Sequence[str], b: Sequence[str]) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def wer(reference: str, hypothesis: str) -> float:
    """Word error rate = (substitutions + deletions + insertions) / reference words."""
    ref, hyp = normalize(reference), normalize(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    return edit_distance(ref, hyp) / len(ref)


def recall_at_k(ranked_ids: Iterable[Sequence[object]], relevant: Iterable[set], k: int = 3) -> float:
    """Fraction of queries whose top-``k`` results contain at least one relevant id."""
    hits = total = 0
    for ranked, rel in zip(ranked_ids, relevant):
        total += 1
        hits += bool(set(list(ranked)[:k]) & set(rel))
    return hits / total if total else 0.0


def _similar(a: str, b: str, threshold: float) -> bool:
    ta, tb = set(normalize(a)), set(normalize(b))
    if not ta or not tb:
        return False
    return len(ta & tb) / len(ta | tb) >= threshold  # Jaccard overlap of words


@dataclass
class PRF:
    precision: float
    recall: float
    f1: float


def match_items(predicted: Sequence[str], gold: Sequence[str], threshold: float = 0.4) -> PRF:
    """Greedy one-to-one matching of predicted vs gold items by word overlap."""
    unmatched = list(gold)
    tp = 0
    for p in predicted:
        for g in unmatched:
            if _similar(p, g, threshold):
                unmatched.remove(g)
                tp += 1
                break
    precision = tp / len(predicted) if predicted else (1.0 if not gold else 0.0)
    recall = tp / len(gold) if gold else (1.0 if not predicted else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return PRF(precision, recall, f1)
