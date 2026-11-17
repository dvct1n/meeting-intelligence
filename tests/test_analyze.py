import json

from meeting_intel.analyze import _dedupe, analyze_meeting, extract_items, speaker_summaries
from meeting_intel.schemas import ActionItem, Chunk, Decision, Utterance


class ScriptedLLM:
    def __init__(self, reply):
        self.reply = reply

    def complete(self, system, user, *, json_mode=False, max_tokens=1500):
        return self.reply(system, user) if callable(self.reply) else self.reply


def chunk(text="[00:00] Speaker 1: hello"):
    return Chunk(id=0, start=0, end=5, speakers=["Speaker 1"], text=text)


def test_extract_items_parses_and_drops_empty_entries():
    reply = json.dumps({
        "decisions": [{"decision": "Use Postgres"}, {"decision": ""}],
        "action_items": [{"task": "Write ADR", "owner": None, "deadline": "Monday"}, {"task": ""}],
    })
    decisions, actions = extract_items(ScriptedLLM(reply), chunk())
    assert [d.decision for d in decisions] == ["Use Postgres"]
    assert [(a.task, a.deadline) for a in actions] == [("Write ADR", "Monday")]


def test_extract_items_is_fail_soft_on_bad_output():
    for bad in ("not json at all", '{"decisions": "oops"}', '{"action_items": [{"task": 5, "owner": {"x": 1}}]}'):
        assert extract_items(ScriptedLLM(bad), chunk()) == ([], [])


def test_dedupe_is_case_insensitive_and_owner_aware():
    d, a = _dedupe(
        [Decision(decision="Ship it"), Decision(decision=" ship IT ")],
        [ActionItem(task="Fix bug", owner="An"), ActionItem(task="fix bug", owner="an"), ActionItem(task="Fix bug", owner="Binh")],
    )
    assert len(d) == 1 and len(a) == 2


def test_speaker_summaries_skip_quiet_speakers():
    utts = [
        Utterance(start=0, end=1, speaker="Speaker 1", text="word " * 40),
        Utterance(start=1, end=2, speaker="Speaker 2", text="ok"),
    ]
    out = speaker_summaries(ScriptedLLM("summary"), utts)
    assert out == {"Speaker 1": "summary"}


def test_analyze_meeting_falls_back_when_overview_is_not_json():
    def reply(system, user):
        if "extract structured" in system:
            return '{"decisions": [], "action_items": []}'
        return "plain text, not json"

    chunks = [chunk()]
    analysis = analyze_meeting(ScriptedLLM(reply), [], chunks)
    assert chunks[0].summary == "plain text, not json"
    assert analysis.summary.startswith("Part 1:")  # raw chunk summaries are kept instead of crashing
    assert analysis.title == "Untitled meeting"


def test_progress_callback_reports_every_stage():
    seen = []
    analyze_meeting(ScriptedLLM('{"decisions": [], "action_items": []}'), [], [chunk()], on_progress=seen.append)
    assert seen == ["Summarizing chunks", "Extracting decisions and action items", "Writing overview", "Summarizing speakers"]
