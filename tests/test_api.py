from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200


def test_root():
    response = client.get("/")
    assert response.status_code == 200


def test_get_incidents():
    response = client.get("/incidents")
    assert response.status_code == 200


def test_get_dashboard_stats():
    response = client.get("/dashboard/stats")
    assert response.status_code == 200


def test_get_nonexistent_incident():
    response = client.get("/incidents/999999")
    assert response.status_code in [404, 200]


def test_reset_incidents():
    response = client.delete("/incidents/reset")
    assert response.status_code == 200