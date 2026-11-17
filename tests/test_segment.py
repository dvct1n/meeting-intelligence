from meeting_intel.schemas import Utterance
from meeting_intel.segment import chunk_utterances
from tests.fakes import FakeEmbedder


def utts(words):
    return [Utterance(start=i * 5, end=i * 5 + 4, speaker="Speaker 1", text=f"{w} point number {i}") for i, w in enumerate(words)]


def test_size_limit_without_embedder():
    chunks = chunk_utterances(utts(["x"] * 40), embedder=None, max_chars=300)
    assert len(chunks) > 1
    assert all(len(c.text) <= 300 + 80 for c in chunks)
    assert chunks[0].id == 0 and chunks[-1].end == 39 * 5 + 4


def test_topic_shift_creates_boundary():
    data = utts(["alpha"] * 8 + ["beta"] * 8)
    chunks = chunk_utterances(data, FakeEmbedder(), max_chars=10_000, min_chars=50)
    assert len(chunks) == 2
    assert "alpha" in chunks[0].text and "beta" not in chunks[0].text
    assert "beta" in chunks[1].text


def test_short_meeting_is_one_chunk():
    assert len(chunk_utterances(utts(["alpha"] * 3), FakeEmbedder())) == 1
