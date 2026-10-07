import pytest
from fastapi.testclient import TestClient
from app.main import app


def run(records=None,category='automotive',symptom='Engine will not start',findings=None):
    with TestClient(app) as client:
        response=client.post('/api/diagnoses',json={'category':category,'symptom':symptom,'answers':{'guided_answers':records or [],'findings':findings or []}})
    assert response.status_code==201
    return response.json()


def record(q,a,d=''):
    return {'question_id':q,'answer':a,'detail':d}


def test_ambiguous_starting_complaint_is_clarified_before_parts():
    r=run()
    assert r['guided_step']['question_id']=='start_behavior'
    assert 'cranks' in [x['value'] for x in r['guided_step']['choices']]


@pytest.mark.parametrize('category',['automotive','motorcycle','equipment'])
def test_passed_battery_moves_to_power_delivery_not_replacement(category):
    r=run([record('start_behavior','no_crank'),record('battery_test','passed')],category=category)
    assert r['guided_step']['question_id']=='connection_test'
    assert 'Battery tested good' in r['causes'][0]['title']
    assert 'voltage drop' in r['guided_step']['instruction']


def test_structured_cranking_observation_overrides_earlier_clicking_description():
    r=run([record('start_behavior','cranks')],symptom='Engine only clicks and will not start')
    assert r['causes'][0]['title']=='Crank-no-start condition'
    assert r['guided_step']['question_id'].startswith('check_')
    assert r['guided_step']['question_id']!='battery_test'


def test_good_battery_and_cables_do_not_prove_starter_failure():
    r=run([record('start_behavior','no_crank'),record('battery_test','passed'),record('connection_test','passed')])
    assert r['guided_step']['question_id']=='starter_test'
    assert r['guided_step']['state']=='investigating'


def test_repair_is_open_until_successful_retest_reported():
    records=[record('start_behavior','no_crank'),record('battery_test','failed')]
    assert run(records)['guided_step']['question_id']=='repair_retest'
    r=run(records+[record('repair_retest','resolved','Battery failed load test; replaced correct battery, starts normally repeatedly.')])
    assert r['guided_step']['state']=='resolved'
    assert 'by you' in r['guided_step']['title']
    assert run(records+[record('repair_retest','persists')])['guided_step']['state']=='needs_help'


def test_hazard_cannot_be_overridden_by_claimed_success():
    r=run([record('repair_retest','resolved','Reported fixed')],category='appliance',symptom='Oven has a gas leak')
    assert r['guided_step']['state']=='stop'
    assert r['guided_step']['choices']==[]


def test_generic_check_uses_observation_then_confirmation_then_retest():
    symptom='Dishwasher will not drain; standing water remains'
    first=run(category='appliance',symptom=symptom)['guided_step']
    q=first['question_id']
    second=run([record(q,'observed','Drain hose is blocked')],category='appliance',symptom=symptom)['guided_step']
    assert second['question_id']==q+'_confirm'
    third=run([record(q,'observed','Drain hose is blocked'),record(q+'_confirm','confirmed','Drain hose blockage confirmed using service procedure')],category='appliance',symptom=symptom)['guided_step']
    assert third['question_id']=='repair_retest'


def test_completed_check_moves_forward_and_unknown_codes_do_not_skip():
    first=run(symptom='Engine runs rough and misfires')['guided_step']
    second=run([record(first['question_id'],'clear','Read codes, none stored')],symptom='Engine runs rough and misfires')['guided_step']
    assert second['question_id']!=first['question_id']
    invalid=run([record('start_behavior','made_up'),record('repair_retest','invented')])
    assert invalid['guided_step']['question_id']=='start_behavior'


def test_cannot_test_leads_to_actionable_handoff_instead_of_endless_loop():
    r=run([record('start_behavior','no_crank'),record('battery_test','untested')])
    assert r['guided_step']['state']=='needs_help'
    assert 'capacity test' in r['guided_step']['instruction']


def test_leaking_fuel_words_override_reported_success():
    from app.safety_gate import urgent_hazard
    assert urgent_hazard("Engine will not start; leaking fuel", {})["safety"] == "stop"
    assert urgent_hazard("No leaking fuel observed", {}) is None


def test_dsc_complaint_has_targeted_path_and_not_transmission_guess():
    symptom="DSC OFF stays lit, button will not turn it on. I drive daily and cannot do a burnout."
    first=run(symptom=symptom)
    assert first['guided_step']['question_id']=='dsc_lights'
    assert 'DSC / traction-control' in first['causes'][0]['title']
    second=run([record('dsc_lights','off_only')],symptom=symptom)
    assert second['guided_step']['question_id']=='dsc_scan'
    assert 'ABS / DSC' in second['guided_step']['instruction']
    assert run([record('dsc_lights','brake')],symptom=symptom)['guided_step']['state']=='stop'
    rows=[record('dsc_lights','off_only'),record('dsc_scan','codes')]
    assert run(rows,symptom=symptom)['guided_step']['question_id']=='check_dsc_fault_confirm'
    assert run(rows+[record('check_dsc_fault_confirm','confirmed','Fault isolated by technician')],symptom=symptom)['guided_step']['question_id']=='repair_retest'

@pytest.mark.parametrize('behavior',['no_crank','slow_crank'])
def test_latest_guided_start_observation_overrides_older_free_text(behavior):
    result=run([record('start_behavior','cranks'),record('start_behavior',behavior)],
               findings=['Earlier attempt: cranks but will not start'])
    assert result['guided_step']['question_id']=='battery_test'
    assert result['causes'][0]['title'].startswith('No-crank starting fault')
