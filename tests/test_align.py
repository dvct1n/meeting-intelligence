from meeting_intel.align import assign_speakers, merge_utterances, relabel_speakers
from meeting_intel.schemas import Segment, SpeakerTurn, Utterance


def test_assign_picks_max_overlap():
    segs = [Segment(start=0, end=4, text="hello"), Segment(start=4, end=9, text="world")]
    turns = [SpeakerTurn(start=0, end=3.5, speaker="A"), SpeakerTurn(start=3.5, end=10, speaker="B")]
    out = assign_speakers(segs, turns)
    assert [u.speaker for u in out] == ["A", "B"]


def test_assign_nearest_turn_when_no_overlap():
    segs = [Segment(start=20, end=21, text="late")]
    turns = [SpeakerTurn(start=0, end=5, speaker="A"), SpeakerTurn(start=15, end=18, speaker="B")]
    assert assign_speakers(segs, turns)[0].speaker == "B"


def test_assign_without_diarization_uses_default():
    out = assign_speakers([Segment(start=0, end=1, text="x")], [])
    assert out[0].speaker == "SPEAKER_00"


def test_merge_same_speaker_and_respect_gap():
    u = lambda s, e, sp, t: Utterance(start=s, end=e, speaker=sp, text=t)
    merged = merge_utterances([u(0, 2, "A", "one"), u(2.5, 4, "A", "two"), u(4.2, 5, "B", "three"), u(20, 21, "B", "four")])
    assert [(m.speaker, m.text) for m in merged] == [("A", "one two"), ("B", "three"), ("B", "four")]


def test_relabel_in_order_of_appearance():
    u = lambda sp: Utterance(start=0, end=1, speaker=sp, text="x")
    out = relabel_speakers([u("SPEAKER_07"), u("SPEAKER_02"), u("SPEAKER_07")])
    assert [x.speaker for x in out] == ["Speaker 1", "Speaker 2", "Speaker 1"]
