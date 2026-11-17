from meeting_intel.schemas import Meeting
from tests.conftest import add_fake_upload, build_services


def test_full_pipeline_offline(services):
    add_fake_upload(services, "m1")
    m = services.pipeline.process("m1")
    assert m.status == "done", m.error
    assert {u.speaker for u in m.utterances} == {"Speaker 1", "Speaker 2"}
    assert len(m.chunks) >= 2
    a = m.analysis
    assert a.title == "Release planning"
    assert [d.decision for d in a.decisions] == ["Ship the release on Friday"]  # de-duplicated across chunks
    assert a.action_items[0].owner == "Speaker 2" and a.action_items[0].deadline == "by Thursday"
    # speakers with fewer than 30 words (Speaker 1 here) are skipped on purpose
    assert set(a.speaker_summaries) == {"Speaker 2"}

    hits = services.index.search("beta release", meeting_id="m1", limit=3)
    assert hits and "beta" in hits[0].text
    assert services.store.load("m1").status == "done"


def test_pipeline_survives_diarization_failure(tmp_path):
    def boom(p):
        raise RuntimeError("no token")

    svc = build_services(tmp_path, diarize_fn=boom)
    add_fake_upload(svc, "m2")
    m = svc.pipeline.process("m2")
    assert m.status == "done"
    assert {u.speaker for u in m.utterances} == {"Speaker 1"}


def test_diarization_skipped_when_disabled(tmp_path):
    def must_not_run(p):
        raise AssertionError("diarization should be skipped")

    svc = build_services(tmp_path, diarize_fn=must_not_run, diarize=False)
    add_fake_upload(svc, "m4")
    assert svc.pipeline.process("m4").status == "done"


def test_failure_is_recorded(services):
    services.pipeline.asr_fn = lambda p: (_ for _ in ()).throw(ValueError("bad audio"))
    add_fake_upload(services, "m3")
    m = services.pipeline.process("m3")
    assert m.status == "failed" and "bad audio" in m.error
    assert services.store.load("m3").status == "failed"


def test_empty_transcript_still_completes(services):
    services.pipeline.asr_fn = lambda p: []
    add_fake_upload(services, "m5")
    m = services.pipeline.process("m5")
    assert m.status == "done" and m.utterances == [] and m.duration == 0.0


def test_reprocessing_replaces_vectors(services):
    add_fake_upload(services, "m6")
    services.pipeline.process("m6")
    n = len(services.index.rows)
    services.pipeline.process("m6")
    assert len(services.index.rows) == n
    assert isinstance(services.store.load("m6"), Meeting)
