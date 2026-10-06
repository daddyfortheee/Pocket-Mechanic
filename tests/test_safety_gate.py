import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.parametrize('category,symptom',[('home','I smell gas near the heater'),('appliance','Oven has a gas leak'),('automotive','The car has no brakes'),('diy','Building shelf but smoke from outlet'),('equipment','Tractor has a fuel leak'),('motorcycle','My motorcycle brakes failed')])
def test_explicit_hazard_overrides_normal_repair_flow(category,symptom):
    result=TestClient(app).post('/api/diagnoses',json={'category':category,'symptom':symptom}).json()
    assert result['causes'][0]['safety']=='stop'
    assert result['safety_message'].startswith('STOP')


def test_negated_hazard_does_not_override_normal_checks():
    result=TestClient(app).post('/api/diagnoses',json={'category':'home','symptom':'There is no gas leak, the fan is noisy'}).json()
    assert result['causes'][0]['safety']!='stop'
