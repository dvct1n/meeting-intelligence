from meeting_intel.index import _payload_to_search_hit


def test_payload_to_search_hit_valid_payload():
    hit = _payload_to_search_hit(
        {
            "meeting_id": "meeting-1",
            "chunk_id": 3,
            "start": 12.5,
            "end": 18.0,
            "speakers": ["Speaker 1"],
            "text": "The team agreed to ship the update.",
            "summary": "Release decision",
        },
        0.92,
    )

    assert hit is not None
    assert hit.meeting_id == "meeting-1"
    assert hit.chunk_id == 3
    assert hit.score == 0.92
    assert hit.summary == "Release decision"


def test_payload_to_search_hit_skips_none_payload():
    assert _payload_to_search_hit(None, 0.5) is None


def test_payload_to_search_hit_skips_incomplete_payload():
    payload = {
        "meeting_id": "meeting-1",
        "chunk_id": 3,
        "start": 12.5,
        # Required fields are deliberately missing.
    }

    assert _payload_to_search_hit(payload, 0.5) is None


def test_payload_to_search_hit_skips_malformed_payload():
    payload = {
        "meeting_id": "meeting-1",
        "chunk_id": "not-an-integer",
        "start": 12.5,
        "end": 18.0,
        "speakers": ["Speaker 1"],
        "text": "A valid transcript excerpt.",
    }

    assert _payload_to_search_hit(payload, 0.5) is None
