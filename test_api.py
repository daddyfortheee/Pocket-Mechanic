from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['version'] == '0.4.0'

def test_diagnosis():
    response = client.post('/api/diagnoses', json={'category':'automotive','symptom':'speedometer odometer and cruise do not work','answers':{}})
    assert response.status_code == 201
    assert response.json()['causes'][0]['title'] == 'Vehicle speed signal loss'

def test_obd():
    response = client.get('/api/obd/P0300')
    assert response.status_code == 200
    assert response.json()['code'] == 'P0300'
