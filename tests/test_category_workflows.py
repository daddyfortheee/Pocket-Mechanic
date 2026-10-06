import pytest
from app.diagnosis_engine import build_diagnostic_causes

@pytest.mark.parametrize('symptom',["Dishwasher will not drain","Washer does not drain","Dishwasher doesn't drain"])
def test_plain_language_drain_complaints(symptom):
    assert build_diagnostic_causes('appliance',symptom)[0]['title']=='Drain restriction or drain-pump fault'

@pytest.mark.parametrize('category',['motorcycle','equipment'])
def test_cranking_complaint_does_not_assume_engine_type(category):
    result=build_diagnostic_causes(category,'Engine turns over but will not start')[0]
    assert result['title'].startswith('Engine turns over')
    assert 'fuel type' in result['checks'][0]

def test_faucet_drip_has_relevant_checks():
    assert build_diagnostic_causes('home','Faucet drips with water off')[0]['title'].startswith('Faucet leak')
