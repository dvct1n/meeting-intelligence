"""LLM analysis: chunk summaries -> overview, decisions, action items, per-speaker summaries."""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Callable

from pydantic import ValidationError

from .llm import LLM, extract_json
from .schemas import ActionItem, Analysis, Chunk, Decision, Utterance
from .utils import utterance_line

log = logging.getLogger(__name__)

LANG_RULE = "Write in the same language as the transcript. Never invent facts that are not in the text."

CHUNK_SYSTEM = (
    "You are an expert meeting analyst. Summarize the meeting excerpt in 2-4 sentences. "
    "Mention who said what when it matters. " + LANG_RULE
)

EXTRACT_SYSTEM = (
    "You extract structured information from a meeting excerpt. Return ONLY valid JSON with this shape:\n"
    '{"decisions": [{"decision": str, "rationale": str|null}], '
    '"action_items": [{"task": str, "owner": str|null, "deadline": str|null}]}\n'
    "Rules: include only items explicitly stated in the excerpt. 'owner' is the responsible person "
    "(use the name if mentioned, otherwise the speaker label). 'deadline' is copied as stated "
    "(e.g. 'by Friday'); use null when none is given. Use empty lists when nothing applies. " + LANG_RULE
)

OVERVIEW_SYSTEM = (
    "You are given summaries of consecutive parts of one meeting. Return ONLY valid JSON: "
    '{"title": str (max 10 words), "summary": str (max 6 sentences), "topics": [str] (3-8 short topics)}. '
    + LANG_RULE
)

SPEAKER_SYSTEM = (
    "Summarize this participant's main points, positions and commitments in 2-3 sentences. " + LANG_RULE
)


def summarize_chunk(llm: LLM, chunk: Chunk) -> str:
    return llm.complete(CHUNK_SYSTEM, chunk.text, max_tokens=300).strip()


def extract_items(llm: LLM, chunk: Chunk) -> tuple[list[Decision], list[ActionItem]]:
    try:
        data = extract_json(llm.complete(EXTRACT_SYSTEM, chunk.text, json_mode=True, max_tokens=1200))
        decisions = [Decision(**d) for d in data.get("decisions", []) if d.get("decision")]
        actions = [ActionItem(**a) for a in data.get("action_items", []) if a.get("task")]
        return decisions, actions
    except (ValueError, ValidationError, TypeError, AttributeError) as e:
        log.warning("extraction failed for chunk %s: %s", chunk.id, e)
        return [], []


def _dedupe(decisions: list[Decision], actions: list[ActionItem]):
    seen_d: set[str] = set()
    seen_a: set[tuple[str, str]] = set()
    d_out, a_out = [], []
    for d in decisions:
        dkey = d.decision.strip().lower()
        if dkey not in seen_d:
            seen_d.add(dkey)
            d_out.append(d)
    for a in actions:
        akey = (a.task.strip().lower(), (a.owner or "").strip().lower())
        if akey not in seen_a:
            seen_a.add(akey)
            a_out.append(a)
    return d_out, a_out


def speaker_summaries(llm: LLM, utts: list[Utterance], min_words: int = 30, max_chars: int = 6000) -> dict[str, str]:
    by_speaker: dict[str, list[Utterance]] = defaultdict(list)
    for u in utts:
        by_speaker[u.speaker].append(u)
    out: dict[str, str] = {}
    for speaker, items in by_speaker.items():
        if sum(len(u.text.split()) for u in items) < min_words:
            continue
        text = "\n".join(utterance_line(u) for u in items)[:max_chars]
        out[speaker] = llm.complete(SPEAKER_SYSTEM, f"Participant: {speaker}\n\n{text}", max_tokens=250).strip()
    return out


def analyze_meeting(
    llm: LLM,
    utterances: list[Utterance],
    chunks: list[Chunk],
    on_progress: Callable[[str], None] | None = None,
) -> Analysis:
    say = on_progress or (lambda msg: None)

    say("Summarizing chunks")
    for ch in chunks:
        ch.summary = summarize_chunk(llm, ch)

    say("Extracting decisions and action items")
    decisions: list[Decision] = []
    actions: list[ActionItem] = []
    for ch in chunks:
        d, a = extract_items(llm, ch)
        decisions += d
        actions += a
    decisions, actions = _dedupe(decisions, actions)

    say("Writing overview")
    analysis = Analysis(decisions=decisions, action_items=actions)
    joined = "\n".join(f"Part {c.id + 1}: {c.summary}" for c in chunks if c.summary)
    if joined:
        try:
            data = extract_json(llm.complete(OVERVIEW_SYSTEM, joined, json_mode=True, max_tokens=600))
            analysis.title = str(data.get("title") or analysis.title)
            analysis.summary = str(data.get("summary") or "")
            analysis.topics = [str(t) for t in data.get("topics", [])][:8]
        except (ValueError, TypeError) as e:
            log.warning("overview parsing failed: %s", e)
            analysis.summary = joined

    say("Summarizing speakers")
    analysis.speaker_summaries = speaker_summaries(llm, utterances)
    return analysis
