from __future__ import annotations

from .schemas import Utterance


def fmt_time(sec: float) -> str:
    sec = int(max(0, sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def utterance_line(u: Utterance) -> str:
    return f"[{fmt_time(u.start)}] {u.speaker}: {u.text}"
