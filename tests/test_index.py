import pytest

pytest.importorskip("qdrant_client")

from meeting_intel.index import MeetingIndex  # noqa: E402
from meeting_intel.schemas import Chunk  # noqa: E402
from tests.fakes import FakeEmbedder  # noqa: E402


@pytest.fixture
def index(tmp_path):
    return MeetingIndex(FakeEmbedder(), path=tmp_path / "qdrant")


def chunks(word):
    return [Chunk(id=i, start=i * 10, end=i * 10 + 9, speakers=["Speaker 1"], text=f"{word} topic {i}") for i in range(2)]


def test_search_filter_and_delete_with_real_qdrant(index):
    index.upsert_chunks("m1", chunks("alpha"))
    index.upsert_chunks("m2", chunks("beta"))

    hits = index.search("beta", limit=4)
    assert hits[0].meeting_id == "m2"
    assert {h.meeting_id for h in index.search("beta", meeting_id="m1", limit=4)} == {"m1"}

    index.delete_meeting("m2")
    assert {h.meeting_id for h in index.search("beta", limit=4)} == {"m1"}


def test_upsert_is_idempotent(index):
    index.upsert_chunks("m1", chunks("alpha"))
    index.upsert_chunks("m1", chunks("alpha"))
    assert len(index.search("alpha", limit=10)) == 2
