"""Merge ASR segments with diarization turns into speaker-labelled utterances."""
from __future__ import annotations

from .schemas import Segment, SpeakerTurn, Utterance


def _overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def assign_speakers(
    segments: list[Segment], turns: list[SpeakerTurn], default: str = "SPEAKER_00"
) -> list[Utterance]:
    """Give each ASR segment the speaker whose turns overlap it the most."""
    out: list[Utterance] = []
    for seg in segments:
        scores: dict[str, float] = {}
        for t in turns:
            ov = _overlap(seg.start, seg.end, t.start, t.end)
            if ov > 0:
                scores[t.speaker] = scores.get(t.speaker, 0.0) + ov
        if scores:
            speaker = max(scores, key=lambda k: scores[k])
        elif turns:  # no overlap (silence/noise): nearest turn wins
            mid = (seg.start + seg.end) / 2
            speaker = min(turns, key=lambda t: min(abs(mid - t.start), abs(mid - t.end))).speaker
        else:
            speaker = default
        out.append(Utterance(start=seg.start, end=seg.end, speaker=speaker, text=seg.text))
    return out


def merge_utterances(utts: list[Utterance], max_gap: float = 2.0) -> list[Utterance]:
    """Join consecutive utterances from the same speaker if the pause is short."""
    merged: list[Utterance] = []
    for u in utts:
        if merged and merged[-1].speaker == u.speaker and u.start - merged[-1].end <= max_gap:
            prev = merged[-1]
            merged[-1] = Utterance(
                start=prev.start, end=max(prev.end, u.end), speaker=prev.speaker,
                text=f"{prev.text} {u.text}".strip(),
            )
        else:
            merged.append(u.model_copy())
    return merged


def relabel_speakers(utts: list[Utterance]) -> list[Utterance]:
    """SPEAKER_03 -> 'Speaker 1', 'Speaker 2', ... in order of first appearance."""
    mapping: dict[str, str] = {}
    for u in utts:
        if u.speaker not in mapping:
            mapping[u.speaker] = f"Speaker {len(mapping) + 1}"
    return [u.model_copy(update={"speaker": mapping[u.speaker]}) for u in utts]
