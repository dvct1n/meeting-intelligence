import pytest

from meeting_intel.config import Settings
from meeting_intel.pipeline import MeetingPipeline
from meeting_intel.schemas import Meeting, Segment, SpeakerTurn
from meeting_intel.services import Services
from meeting_intel.storage import MeetingStore
from tests.fakes import FakeEmbedder, FakeIndex, FakeLLM

SEGMENTS = (
    [Segment(start=i * 8, end=i * 8 + 5, text=f"alpha planning item {i}") for i in range(6)]
    + [Segment(start=60 + i * 8, end=60 + i * 8 + 5, text=f"beta we agreed to ship the release on Friday {i}") for i in range(6)]
)
TURNS = [SpeakerTurn(start=0, end=55, speaker="SPEAKER_01"), SpeakerTurn(start=55, end=140, speaker="SPEAKER_00")]


def make_settings(tmp_path, diarize=True, **overrides) -> Settings:
    base = dict(
        data_dir=tmp_path, whisper_model="x", whisper_language=None, diarize=diarize,
        diarization_model="x", hf_token=None, embedding_model="x", qdrant_path=tmp_path / "qdrant",
        qdrant_url=None, llm_provider="openai", llm_model="x", llm_base_url=None, llm_api_key=None,
        chunk_max_chars=3500, chunk_min_chars=60,
    )
    base.update(overrides)
    return Settings(**base)


def build_services(tmp_path, diarize_fn=None, diarize=True, index=None, **settings_overrides) -> Services:
    s = make_settings(tmp_path, diarize, **settings_overrides)
    store, emb = MeetingStore(tmp_path), FakeEmbedder()
    index = index or FakeIndex(emb)
    pipe = MeetingPipeline(
        s, store, index, FakeLLM(), emb,
        audio_fn=lambda p: p, asr_fn=lambda p: SEGMENTS, diarize_fn=diarize_fn or (lambda p: TURNS),
    )
    return Services(s, store, index, pipe)


def add_fake_upload(svc: Services, meeting_id: str) -> None:
    (svc.store.dir(meeting_id) / "audio.wav").write_bytes(b"fake")
    svc.store.save(Meeting(id=meeting_id, filename="audio.wav"))


@pytest.fixture
def services(tmp_path):
    return build_services(tmp_path)
