from meeting_intel.export import to_markdown
from meeting_intel.schemas import ActionItem, Analysis, Chunk, Decision, Meeting, Utterance


def make_meeting():
    return Meeting(
        id="x", filename="audio.wav", duration=3725, created_at="2025-03-04T10:15:00+00:00", status="done",
        utterances=[Utterance(start=0, end=4, speaker="Speaker 1", text="Let's ship Friday.")],
        chunks=[Chunk(id=0, start=0, end=4, speakers=["Speaker 1"], text="t", summary="Release talk")],
        analysis=Analysis(
            title="Release planning", summary="They planned the release.", topics=["release", "QA"],
            decisions=[Decision(decision="Ship Friday", rationale="QA done")],
            action_items=[ActionItem(task="Update | changelog", owner="Speaker 1", deadline=None)],
            speaker_summaries={"Speaker 1": "Drove the plan."},
        ),
    )


def test_markdown_has_every_section():
    md = to_markdown(make_meeting())
    for part in ("# Release planning", "1:02:05", "## Decisions", "Ship Friday — _QA done_", "## Action items",
                 "## Speakers", "## Topic timeline", "## Transcript", "Let's ship Friday."):
        assert part in md


def test_markdown_escapes_table_pipes_and_marks_missing_values():
    md = to_markdown(make_meeting())
    assert "| Update \\| changelog | Speaker 1 | — |" in md


def test_transcript_can_be_omitted():
    assert "## Transcript" not in to_markdown(make_meeting(), include_transcript=False)


def test_unanalysed_meeting_renders_status():
    md = to_markdown(Meeting(id="y", filename="audio.wav", status="failed"))
    assert "audio.wav" in md and "failed" in md
