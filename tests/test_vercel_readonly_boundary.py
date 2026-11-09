import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
@pytest.mark.parametrize("path", ["/", "/health", "/receipts"])
def test_write_methods_reject_without_echo_or_state(method, path):
    marker = "SYNTHETIC_REQUEST_MARKER"
    with TestClient(app) as client:
        before = client.get("/").json()
        response = client.request(method, path, json={"private": marker})
        assert response.status_code == (404 if path == "/receipts" else 405)
        assert marker not in response.text
        assert client.get("/").json() == before


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json", "/.env",
                                  "/README.md", "/candidate-record-v0.1.schema.json"])
def test_undeclared_routes_and_repository_files_are_not_served(path):
    with TestClient(app) as client:
        assert client.get(path).status_code == 404


def test_route_inventory_is_the_two_declared_reads():
    assert {route.path: route.methods for route in app.routes} == {
        "/": {"GET"}, "/health": {"GET"},
    }
