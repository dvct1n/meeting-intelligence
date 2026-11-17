#!/usr/bin/env python3
"""Run a deterministic, offline walkthrough using the synthetic meeting fixture.

This demo validates a stored Meeting object, displays its precomputed analysis,
performs a transparent keyword-overlap search, and exports Markdown. It does
not run ASR, diarization, an LLM, neural embeddings, or Qdrant.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from meeting_intel.export import to_markdown  # noqa: E402
from meeting_intel.schemas import Meeting  # noqa: E402

SAMPLE_MEETING = ROOT / "examples" / "sample_meeting.json"


def load_sample_meeting() -> Meeting:
    """Load and schema-validate the checked-in synthetic meeting fixture."""
    try:
        raw = json.loads(SAMPLE_MEETING.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot load sample meeting {SAMPLE_MEETING}: {exc}") from exc
    return Meeting.model_validate(raw)


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"\w+", text.casefold()) if len(token) > 1}


def keyword_search(meeting: Meeting, query: str, limit: int = 3) -> list[tuple[float, str, str]]:
    """Rank fixture utterances by query-token overlap (not semantic retrieval)."""
    query_tokens = _tokens(query)
    if not query_tokens:
        return []

    results: list[tuple[float, str, str]] = []
    for utterance in meeting.utterances:
        matched = query_tokens & _tokens(utterance.text)
        if matched:
            score = len(matched) / len(query_tokens)
            label = f"{utterance.speaker} · {utterance.start:.1f}s–{utterance.end:.1f}s"
            results.append((score, label, utterance.text))

    for chunk in meeting.chunks:
        text = chunk.summary or chunk.text
        matched = query_tokens & _tokens(text)
        if matched:
            score = len(matched) / len(query_tokens)
            label = f"Topic chunk {chunk.id} · {chunk.start:.1f}s–{chunk.end:.1f}s"
            results.append((score, label, text))

    return sorted(results, key=lambda item: (-item[0], item[1]))[:limit]


def run_demo(query: str, output: Path | None) -> int:
    meeting = load_sample_meeting()
    analysis = meeting.analysis

    print("MEETING INTELLIGENCE — OFFLINE FIXTURE DEMO")
    print("Synthetic example only; no ML inference or production search is executed.\n")
    print(f"Validated meeting: {meeting.id}")
    print(f"Title: {analysis.title if analysis else meeting.filename}")
    print(f"Duration: {meeting.duration:.1f}s | Utterances: {len(meeting.utterances)} | Chunks: {len(meeting.chunks)}")

    if analysis:
        print("\nSUMMARY")
        print(analysis.summary or "(No summary in fixture)")

        print("\nDECISIONS")
        for item in analysis.decisions:
            print(f"- {item.decision}")

        print("\nACTION ITEMS")
        for item in analysis.action_items:
            owner = item.owner or "Unassigned"
            deadline = item.deadline or "No deadline stated"
            print(f"- {item.task} | Owner: {owner} | Deadline: {deadline}")

    print(f"\nOFFLINE KEYWORD SEARCH: {query!r}")
    hits = keyword_search(meeting, query)
    if not hits:
        print("No matching fixture text found.")
    else:
        for score, label, text in hits:
            print(f"- [{score:.0%}] {label}: {text}")

    if output is not None:
        output_path = output.expanduser()
        if not output_path.is_absolute():
            output_path = (Path.cwd() / output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(to_markdown(meeting), encoding="utf-8")
        print(f"\nMarkdown report written to: {output_path}")

    print("\nNOTE: This walkthrough uses precomputed synthetic data.")
    print("It does not call Whisper, pyannote, an LLM, an embedding model, or Qdrant.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="launch date", help="query for the local keyword-overlap demo")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/demo-report.md"),
        help="Markdown report path (default: artifacts/demo-report.md); use --no-output to skip",
    )
    parser.add_argument("--no-output", action="store_true", help="do not write a Markdown report")
    args = parser.parse_args(argv)
    return run_demo(args.query, None if args.no_output else args.output)


if __name__ == "__main__":
    raise SystemExit(main())
