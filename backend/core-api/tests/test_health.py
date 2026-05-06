"""Smoke test the /healthz endpoint without DB/Redis dependencies."""

from fastapi.testclient import TestClient


def test_healthz() -> None:
    from app.main import app

    with TestClient(app) as client:
        r = client.get("/healthz")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
