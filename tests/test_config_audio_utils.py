import pytest

from meeting_intel import audio
from meeting_intel.config import Settings
from meeting_intel.schemas import Utterance
from meeting_intel.utils import fmt_time, utterance_line


def test_settings_defaults(monkeypatch):
    for k in ("DATA_DIR", "WHISPER_LANGUAGE", "DIARIZE", "LLM_API_KEY", "API_KEY", "MAX_UPLOAD_MB", "QDRANT_URL"):
        monkeypatch.delenv(k, raising=False)
    s = Settings.from_env()
    assert s.diarize is True and s.whisper_language is None and s.api_key is None
    assert s.max_upload_mb == 500 and s.qdrant_url is None and s.llm_provider == "openai"


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("DIARIZE", "false")
    monkeypatch.setenv("WHISPER_LANGUAGE", " vi ")
    monkeypatch.setenv("LLM_PROVIDER", "Anthropic")
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("MAX_UPLOAD_MB", "12")
    monkeypatch.setenv("DATA_DIR", "/tmp/xyz")
    s = Settings.from_env()
    assert (s.diarize, s.whisper_language, s.llm_provider, s.api_key, s.max_upload_mb) == (False, "vi", "anthropic", "k", 12)
    assert str(s.qdrant_path) == "/tmp/xyz/qdrant"


def test_fmt_time():
    assert fmt_time(5) == "00:05" and fmt_time(65) == "01:05" and fmt_time(3661) == "1:01:01" and fmt_time(-3) == "00:00"
    assert utterance_line(Utterance(start=65, end=70, speaker="Speaker 1", text="hi")) == "[01:05] Speaker 1: hi"


def test_to_wav_reports_missing_ffmpeg(monkeypatch, tmp_path):
    monkeypatch.setattr(audio.shutil, "which", lambda _: None)
    with pytest.raises(RuntimeError, match="ffmpeg not found"):
        audio.to_wav(tmp_path / "a.mp3")


def test_to_wav_reports_ffmpeg_failure(monkeypatch, tmp_path):
    class Proc:
        returncode, stderr = 1, "Invalid data found"

    monkeypatch.setattr(audio.shutil, "which", lambda _: "/usr/bin/ffmpeg")
    monkeypatch.setattr(audio.subprocess, "run", lambda *a, **k: Proc())
    with pytest.raises(RuntimeError, match="Invalid data"):
        audio.to_wav(tmp_path / "a.mp3")
