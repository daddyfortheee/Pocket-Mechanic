from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app, UPLOAD_DIR, UPLOADED_MEDIA, OWNERS
from app.guest_security import COOKIE, verify_token


def test_diagnoses_and_profiles_are_private_between_browsers():
    a,b=TestClient(app),TestClient(app)
    data={'category':'automotive','symptom':'Engine clicks but will not start'}
    record=a.post('/api/diagnoses',json=data).json()
    profile=a.post('/api/profiles',json={'name':'Private vehicle','category':'automotive'}).json()
    assert verify_token(a.cookies[COOKIE])
    assert a.get('/api/diagnoses/'+record['id']).status_code==200
    assert b.get('/api/diagnoses/'+record['id']).status_code==404
    assert record['id'] not in {x['id'] for x in b.get('/api/diagnoses').json()}
    assert profile['id'] not in {x['id'] for x in b.get('/api/profiles').json()}
    assert profile['id'] in {x['id'] for x in a.get('/api/profiles').json()}
    b.cookies.set(COOKIE, a.cookies[COOKIE][:-1]+'x')
    assert b.get('/api/diagnoses/'+record['id']).status_code==404


def test_another_browser_cannot_submit_private_photo_id():
    a,b=TestClient(app),TestClient(app)
    record=a.post('/api/uploads',files={'files':('private.jpg',b'image','image/jpeg')}).json()['files'][0]
    try:
        with patch('app.main.analyze_uploaded_images',return_value={'available':False}) as analyzer:
            response=b.post('/api/diagnoses',json={'category':'appliance','symptom':'Oven will not heat','answers':{'media':[record]}})
            assert response.status_code==201
            assert analyzer.call_args.args[0]==[]
    finally:
        (UPLOAD_DIR/record['stored_name']).unlink(missing_ok=True)
        UPLOADED_MEDIA.pop(record['id'],None);OWNERS.pop(record['id'],None)


def test_private_responses_are_not_cacheable_and_cookie_is_http_only():
    response=TestClient(app,base_url='https://pocket.test').get('/api/diagnoses')
    assert response.headers['cache-control']=='no-store'
    assert 'HttpOnly' in response.headers['set-cookie']
    assert 'Secure' in response.headers['set-cookie']


def test_cross_origin_requests_and_source_backups_are_blocked():
    client=TestClient(app)
    assert client.post('/api/diagnoses',headers={'Origin':'https://other.example'},json={'category':'automotive','symptom':'Engine does not start'}).status_code==403
    assert client.get('/static/app.js.backup').status_code==404


def test_rate_limit_bounds_repeated_expensive_requests():
    from app.guest_security import allow_request, RATE_BUCKETS
    RATE_BUCKETS.clear()
    assert allow_request('test','analysis',2,600)
    assert allow_request('test','analysis',2,600)
    assert not allow_request('test','analysis',2,600)
    RATE_BUCKETS.clear()
