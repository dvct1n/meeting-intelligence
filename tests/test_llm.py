import pytest

from meeting_intel.llm import extract_json, with_retries


def test_extract_json_plain_fenced_and_noisy():
    assert extract_json('{"a": 1}') == {"a": 1}
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Sure! Here you go:\n{"a": {"b": 2}}\nHope that helps.') == {"a": {"b": 2}}


def test_extract_json_rejects_garbage():
    with pytest.raises(ValueError):
        extract_json("no json here")


def test_retries_then_succeeds():
    calls, sleeps = [], []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError("boom")
        return "ok"

    assert with_retries(flaky, attempts=3, base_delay=1.0, sleep=sleeps.append) == "ok"
    assert sleeps == [1.0, 2.0]  # exponential back-off


def test_retries_give_up_and_reraise():
    def always():
        raise RuntimeError("down")

    with pytest.raises(RuntimeError, match="down"):
        with_retries(always, attempts=2, sleep=lambda s: None)
