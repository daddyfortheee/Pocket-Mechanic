from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_speed_signal_diagnosis():
    response = client.post("/api/diagnoses", json={
        "category": "automotive",
        "symptom": "Speedometer and odometer stay at zero and cruise control does not work",
        "answers": {}
    })
    assert response.status_code == 201
    body = response.json()
    assert body["causes"][0]["title"] == "Vehicle speed signal loss"
    assert body["causes"][0]["confidence"] > 0.8
