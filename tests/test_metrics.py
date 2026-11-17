import pytest

from meeting_intel.metrics import edit_distance, match_items, normalize, recall_at_k, wer


def test_normalize_keeps_vietnamese_diacritics():
    assert normalize("Chúng ta, họp lúc 9 giờ!") == ["chúng", "ta", "họp", "lúc", "9", "giờ"]


def test_edit_distance():
    assert edit_distance(list("kitten"), list("sitting")) == 3
    assert edit_distance([], ["a", "b"]) == 2


def test_wer_values():
    assert wer("the cat sat", "the cat sat") == 0.0
    assert wer("the cat sat", "the dog sat") == pytest.approx(1 / 3)
    assert wer("the cat sat", "the cat") == pytest.approx(1 / 3)
    assert wer("a b", "a b c d") == 1.0
    assert wer("", "") == 0.0 and wer("", "x") == 1.0
    assert wer("Hello, World!", "hello world") == 0.0  # case and punctuation are ignored


def test_recall_at_k():
    ranked = [["a", "b", "c"], ["x", "y", "z"], ["m"]]
    relevant = [{"c"}, {"q"}, {"m"}]
    assert recall_at_k(ranked, relevant, k=3) == pytest.approx(2 / 3)
    assert recall_at_k(ranked, relevant, k=2) == pytest.approx(1 / 3)
    assert recall_at_k([], [], k=3) == 0.0


def test_match_items_precision_recall_f1():
    gold = ["Send the report to finance", "Book the meeting room"]
    pred = ["send report to finance team", "Order pizza"]
    r = match_items(pred, gold)
    assert (r.precision, r.recall) == (0.5, 0.5) and r.f1 == pytest.approx(0.5)


def test_match_items_is_one_to_one():
    r = match_items(["send the report", "send the report"], ["send the report"])
    assert r.precision == 0.5 and r.recall == 1.0


def test_match_items_empty_cases():
    assert match_items([], []).f1 == 1.0  # nothing to find, nothing found: perfect
    assert match_items(["x"], []).precision == 0.0  # hallucinated item
    assert match_items([], ["x"]).recall == 0.0  # missed item
