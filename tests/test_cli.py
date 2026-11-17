import json

import pytest

from meeting_intel import cli
from tests.conftest import build_services


@pytest.fixture
def svc(tmp_path, monkeypatch):
    s = build_services(tmp_path)
    monkeypatch.setattr(cli, "_services", lambda: s)
    return s


def test_process_then_list_show_search_delete(svc, tmp_path, capsys):
    audio = tmp_path / "standup.wav"
    audio.write_bytes(b"RIFFfake")
    out = tmp_path / "report.md"
    assert cli.main(["process", str(audio), "-o", str(out)]) == 0
    assert out.read_text().startswith("# Release planning")

    mid = svc.store.list()[0].id
    capsys.readouterr()
    assert cli.main(["list"]) == 0
    assert mid in capsys.readouterr().out
    assert cli.main(["show", mid, "--no-transcript"]) == 0
    shown = capsys.readouterr().out
    assert "## Decisions" in shown and "## Transcript" not in shown
    assert cli.main(["search", "ship the release", "-m", mid]) == 0
    assert mid in capsys.readouterr().out
    assert cli.main(["delete", mid]) == 0
    assert svc.store.list() == []


def test_process_missing_file_and_unknown_meeting(svc, capsys):
    assert cli.main(["process", "/nope/a.wav"]) == 2
    assert cli.main(["show", "ghost"]) == 1


def test_offline_eval_commands_do_not_need_services(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "_services", lambda: (_ for _ in ()).throw(AssertionError("must not load services")))
    ref, hyp = tmp_path / "r.txt", tmp_path / "h.txt"
    ref.write_text("the cat sat")
    hyp.write_text("the dog sat")
    assert cli.main(["wer", str(ref), str(hyp)]) == 0
    assert "33.33%" in capsys.readouterr().out

    pred, gold = tmp_path / "p.json", tmp_path / "g.json"
    pred.write_text(json.dumps(["send the report"]))
    gold.write_text(json.dumps(["send the report", "book a room"]))
    assert cli.main(["eval-items", str(pred), str(gold)]) == 0
    assert "precision 100.00%  recall 50.00%" in capsys.readouterr().out


def test_eval_search(svc, tmp_path, capsys):
    from tests.conftest import add_fake_upload

    add_fake_upload(svc, "mm")
    svc.pipeline.process("mm")
    hit = svc.index.search("beta release", limit=1)[0]
    q = tmp_path / "q.json"
    q.write_text(json.dumps([{"query": "beta release", "relevant": [{"meeting_id": "mm", "chunk_id": hit.chunk_id}]}]))
    assert cli.main(["eval-search", str(q), "-k", "1"]) == 0
    assert "Recall@1: 100.00%" in capsys.readouterr().out
