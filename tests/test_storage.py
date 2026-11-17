import pytest

from meeting_intel.schemas import Meeting
from meeting_intel.storage import InvalidMeetingId, MeetingStore


@pytest.fixture
def store(tmp_path):
    return MeetingStore(tmp_path)


def test_roundtrip_and_listing_order(store):
    store.save(Meeting(id="a", filename="audio.wav", created_at="2025-01-01T00:00:00"))
    store.save(Meeting(id="b", filename="audio.wav", created_at="2025-02-01T00:00:00"))
    assert store.load("a").filename == "audio.wav"
    assert [m.id for m in store.list()] == ["b", "a"]  # newest first


@pytest.mark.parametrize("bad", ["..", "../x", "a/b", "", "a" * 65, "x\\y", "."])
def test_unsafe_ids_cannot_escape_the_data_dir(store, tmp_path, bad):
    outside = tmp_path / "precious.txt"
    outside.write_text("keep me")
    with pytest.raises(InvalidMeetingId):
        store.dir(bad)
    with pytest.raises(FileNotFoundError):
        store.load(bad)
    store.delete(bad)  # silently ignored
    assert outside.exists() and store.root.exists()


def test_corrupt_meeting_file_does_not_break_listing(store):
    store.save(Meeting(id="ok", filename="audio.wav"))
    (store.dir("broken") / "meeting.json").write_text("{not json")
    assert [m.id for m in store.list()] == ["ok"]


def test_delete_removes_everything(store):
    (store.dir("gone") / "audio.wav").write_bytes(b"x")
    store.delete("gone")
    assert not (store.root / "gone").exists()


def test_save_leaves_no_temp_files(store):
    store.save(Meeting(id="t", filename="audio.wav"))
    assert [p.name for p in store.dir("t").iterdir()] == ["meeting.json"]


def test_recover_interrupted_marks_stuck_jobs_failed(store):
    store.save(Meeting(id="p", filename="audio.wav", status="processing"))
    store.save(Meeting(id="u", filename="audio.wav", status="uploaded"))
    store.save(Meeting(id="d", filename="audio.wav", status="done"))
    assert sorted(store.recover_interrupted()) == ["p", "u"]
    assert store.load("p").status == "failed" and "Interrupted" in store.load("p").error
    assert store.load("d").status == "done"
