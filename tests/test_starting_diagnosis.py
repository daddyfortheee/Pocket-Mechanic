import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app, base_url='https://pocket.test', headers={'Origin':'https://pocket.test'})


def diagnose(symptom, answers=None):
    response = client.post('/api/diagnoses', json={
        'category': 'automotive', 'symptom': symptom, 'answers': answers or {},
    })
    assert response.status_code == 201
    return response.json()


@pytest.mark.parametrize('symptom', [
    "Turn the key when starting and it only makes a clicking sound. The engine doesn’t turn over. The battery voltage is 6.2v.",
    "Turn the key when starting and it only makes a clicking sound. The engine doesn't turn over. The battery voltage is 6.2 V.",
    "No crank. Battery reads 6.2 volts.",
    "Won't start, just clicks. Voltage: 6.2v at the battery.",
])
def test_measured_low_battery_gets_actionable_diagnosis(symptom):
    result = diagnose(symptom)
    cause = result['causes'][0]
    assert 'Battery power too low' in cause['title']
    assert '6.2 V' in cause['why']
    assert any('Charge the battery first' in step for step in cause['repair'])
    assert any('fails the battery test' in step for step in cause['repair'])
    assert not any(c['title'] == 'More specific details needed' for c in result['causes'])


def test_structured_voltage_and_vehicle_details():
    result = diagnose('Engine does not crank, only clicks.', {
        'battery_voltage': '6.2 V', 'item': {'year': 2015, 'engine': '6.2L'},
    })
    assert 'Battery power too low' in result['causes'][0]['title']


@pytest.mark.parametrize('symptom', [
    "2015 truck with 6.2L engine only clicks when starting.",
    "The battery voltage is 12.6V. The engine doesn't turn over, just clicks.",
    "Engine does not crank. It has a 12V battery.",
    "No crank on my vintage car with a 6 volt system. Battery reads 6.2V.",
])
def test_no_false_low_battery_from_specs_or_normal_voltage(symptom):
    result = diagnose(symptom)
    assert result['causes'][0]['title'].startswith('No-crank starting fault')
    assert all('Battery power too low' not in c['title'] for c in result['causes'])


def test_crank_no_start_keeps_fuel_spark_path():
    result = diagnose('The engine cranks but will not start. Battery voltage is 12.6V.')
    assert result['causes'][0]['title'] == 'Crank-no-start condition'


def test_unrelated_clicking_does_not_become_starter_fault():
    result = diagnose('The turn signal makes a clicking sound while driving.')
    assert all('No-crank' not in c['title'] for c in result['causes'])


def test_passed_battery_finding_moves_to_next_checks_despite_original_low_voltage():
    result = diagnose('Only clicks when starting. Battery voltage is 6.2v.', {
        'findings': ['Battery passed a load test after charging, but it still only clicks.'],
    })
    assert result['causes'][0]['title'].startswith('Battery tested good')
    assert any('voltage drop' in check for check in result['causes'][0]['checks'])
    assert all('Battery power too low' not in cause['title'] for cause in result['causes'])


def test_later_failed_test_overrides_earlier_passed_test():
    result = diagnose('Only clicks when starting. Battery voltage is 6.2v.', {
        'findings': ['Battery tested good.', 'Battery failed the load test on recheck.'],
    })
    assert result['causes'][0]['title'].startswith('Battery power too low')


def test_latest_cranking_symptom_moves_off_no_crank_path():
    result = diagnose('Only clicks when starting. Battery voltage is 6.2v.', {
        'findings': ['Battery passed a load test after charging.', 'It now cranks but will not start.'],
    })
    assert result['causes'][0]['title'] == 'Crank-no-start condition'


def test_unproven_battery_condition_is_not_treated_as_passed_test():
    result = diagnose('Only clicks when starting. Battery voltage is 6.2v.', {
        'findings': ["Battery didn't pass the test."],
    })
    assert result['causes'][0]['title'].startswith('Battery power too low')
