from __future__ import annotations

from fastapi.testclient import TestClient

from api.app import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_static_workspace_loads():
    with TestClient(app) as client:
        response = client.get("/")
        script = client.get("/static/app.js")

    assert response.status_code == 200
    assert "contract-scene" in response.text
    assert script.status_code == 200
    assert "THREE" in script.text
