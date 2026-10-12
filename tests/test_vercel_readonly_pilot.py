from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_home_declares_read_only_boundaries():
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "read-only deployment pilot"
    assert payload["mutations_enabled"] is False
    assert payload["external_ai_calls_enabled"] is False
    assert "pre-commercial" in payload["status"]


def test_health_is_read_only():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "read-only"}


def test_unknown_write_route_is_not_exposed():
    response = client.post("/receipts", json={"example": True})
    assert response.status_code == 404
