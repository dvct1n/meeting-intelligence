import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from meeting_intel.api import app  # noqa: E402
from meeting_intel.services import get_services  # noqa: E402
from tests.conftest import add_fake_upload, build_services  # noqa: E402

WAV = ("standup.wav", b"RIFFfake", "audio/wav")


def make_client(svc):
    app.dependency_overrides[get_services] = lambda: svc
    return TestClient(app)


@pytest.fixture
def client(services):
    yield make_client(services)
    app.dependency_overrides.clear()


def test_upload_list_get_search_delete(client):
    assert client.get("/health").json()["status"] == "ok"
    r = client.post("/meetings", files={"file": WAV})
    assert r.status_code == 202
    mid = r.json()["id"]

    got = client.get(f"/meetings/{mid}").json()  # background task already ran in TestClient
    assert got["status"] == "done" and got["analysis"]["title"] == "Release planning"
    listing = client.get("/meetings").json()
    assert listing[0]["id"] == mid and listing[0]["utterances"] == []

    hits = client.post("/search", json={"query": "ship the release", "limit": 2}).json()
    assert hits and hits[0]["meeting_id"] == mid

    assert client.delete(f"/meetings/{mid}").status_code == 204
    assert client.get(f"/meetings/{mid}").status_code == 404
    assert client.delete(f"/meetings/{mid}").status_code == 404


def test_validation_errors(client):
    assert client.post("/search", json={"query": "  "}).status_code == 400
    assert client.post("/search", json={"query": "x", "limit": 0}).status_code == 422
    assert client.post("/search", json={"query": "x", "limit": 500}).status_code == 422
    assert client.post("/meetings", files={"file": ("notes.txt", b"hi")}).status_code == 400
    assert client.post("/meetings", files={"file": ("empty.wav", b"")}).status_code == 400


def test_upload_size_limit(tmp_path):
    svc = build_services(tmp_path, max_upload_mb=1)
    c = make_client(svc)
    try:
        big = b"0" * (1024 * 1024 + 1)
        assert c.post("/meetings", files={"file": ("big.wav", big)}).status_code == 413
        assert svc.store.list() == []  # the partial upload was cleaned up
        assert not any((tmp_path / "meetings").iterdir())
    finally:
        app.dependency_overrides.clear()


def test_export_markdown(client):
    mid = client.post("/meetings", files={"file": WAV}).json()["id"]
    r = client.get(f"/meetings/{mid}/export")
    assert r.status_code == 200 and r.text.startswith("# Release planning")
    assert "Ship the release on Friday" in r.text
    assert client.get("/meetings/nope/export").status_code == 404


def test_path_traversal_is_rejected(client, services):
    marker = services.store.root.parent / "keep.txt"
    marker.write_text("important")
    for bad in ("..", "%2e%2e", "a%2f..%2f.."):
        assert client.delete(f"/meetings/{bad}").status_code in (404, 405)
        assert client.get(f"/meetings/{bad}").status_code == 404
    assert marker.exists()


def test_cannot_delete_while_processing(client, services):
    add_fake_upload(services, "busy")
    m = services.store.load("busy")
    m.status = "processing"
    services.store.save(m)
    assert client.delete("/meetings/busy").status_code == 409


def test_api_key_is_enforced_when_configured(tmp_path):
    svc = build_services(tmp_path, api_key="s3cret")
    c = make_client(svc)
    try:
        assert c.get("/health").status_code == 200  # health stays open for probes
        assert c.get("/meetings").status_code == 401
        assert c.get("/meetings", headers={"X-API-Key": "wrong"}).status_code == 401
        assert c.get("/meetings", headers={"X-API-Key": "s3cret"}).status_code == 200
    finally:
        app.dependency_overrides.clear()
