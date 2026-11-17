"""Render a processed meeting as a shareable Markdown document."""
from __future__ import annotations

from .schemas import Meeting
from .utils import fmt_time


def _cell(text: str | None) -> str:
    return (text or "—").replace("|", "\\|").replace("\n", " ")


def to_markdown(meeting: Meeting, include_transcript: bool = True) -> str:
    a = meeting.analysis
    lines = [f"# {a.title if a else meeting.filename}", ""]
    speakers = {u.speaker for u in meeting.utterances}
    lines.append(
        f"*{meeting.created_at[:16].replace('T', ' ')} UTC · duration {fmt_time(meeting.duration)} · "
        f"{len(speakers)} speaker(s)*"
    )
    lines.append("")

    if a is None:
        lines.append(f"_Status: {meeting.status}._")
        return "\n".join(lines) + "\n"

    if a.summary:
        lines += ["## Summary", "", a.summary, ""]
    if a.topics:
        lines += ["**Topics:** " + " · ".join(a.topics), ""]

    lines += ["## Decisions", ""]
    if a.decisions:
        for d in a.decisions:
            lines.append(f"- {d.decision}" + (f" — _{d.rationale}_" if d.rationale else ""))
    else:
        lines.append("_None found._")
    lines.append("")

    lines += ["## Action items", ""]
    if a.action_items:
        lines += ["| Task | Owner | Deadline |", "|---|---|---|"]
        lines += [f"| {_cell(i.task)} | {_cell(i.owner)} | {_cell(i.deadline)} |" for i in a.action_items]
    else:
        lines.append("_None found._")
    lines.append("")

    if a.speaker_summaries:
        lines += ["## Speakers", ""]
        for name, text in a.speaker_summaries.items():
            lines.append(f"- **{name}** — {text}")
        lines.append("")

    if meeting.chunks:
        lines += ["## Topic timeline", ""]
        for c in meeting.chunks:
            lines.append(f"- `{fmt_time(c.start)}–{fmt_time(c.end)}` {c.summary or ''}".rstrip())
        lines.append("")

    if include_transcript and meeting.utterances:
        lines += ["## Transcript", ""]
        lines += [f"`{fmt_time(u.start)}` **{u.speaker}**: {u.text}  " for u in meeting.utterances]
        lines.append("")
    return "\n".join(lines)
