from unittest.mock import patch
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app, DIAGNOSES, DIAGNOSIS_OWNERS, PROFILES, UPLOADED_MEDIA, UPLOAD_DIR
from app.accounts import ACCESS_COOKIE, REFRESH_COOKIE, current_user

USER = {'id':'account-a','email':'a@example.com','email_confirmed_at':'2026-09-30T00:00:00Z'}
SESSION = {'user':USER,'access_token':'private-access','refresh_token':'private-refresh','expires_in':3600}
CREDS = {'email':'a@example.com','password':'a-long-password'}

@pytest.fixture
def client():
    with TestClient(app, base_url='https://pocket.test', headers={'Origin':'https://pocket.test'}) as c:
        yield c


def test_anonymous_cannot_use_private_endpoints(client):
    for path in ['/api/diagnoses','/api/profiles','/api/obd/P0300']:
        assert client.get(path).status_code == 401
    assert client.post('/api/diagnoses', json={'category':'automotive','symptom':'no start'}).status_code == 401
    assert client.post('/api/uploads', files={'files':('x.jpg',b'x','image/jpeg')}).status_code == 401


def test_signup_requires_verification_even_if_provider_returns_session(client):
    with patch('app.accounts.provider', return_value=SESSION) as provider:
        result = client.post('/api/auth/signup', json=CREDS)
        assert result.status_code == 200
        assert result.json()['verification_required'] is True
        assert 'private-access' not in result.text
        assert not result.headers.get('set-cookie')
        provider.assert_called_once_with('POST','signup',body=CREDS)
    assert client.get('/api/profiles').status_code == 401


def test_unverified_user_cannot_signin_or_use_api(client):
    unverified = {**USER,'email_confirmed_at':None}
    with patch('app.accounts.provider', return_value={**SESSION,'user':unverified}):
        result = client.post('/api/auth/signin', json=CREDS)
        assert result.status_code == 403
        assert not result.headers.get('set-cookie')
    client.cookies.set(ACCESS_COOKIE,'unverified')
    with patch('app.accounts.provider', return_value=unverified):
        assert client.get('/api/profiles',headers={'X-Pocket-Guru-User':USER['id']}).status_code == 403


def test_verification_grants_cookie_session_and_no_client_tokens(client):
    with patch('app.accounts.provider', return_value=SESSION) as provider:
        result = client.post('/api/auth/verify',json={'email':USER['email'],'code':'123456'})
        assert result.json() == {'user':{'id':USER['id'],'email':USER['email'],'verified':True}}
        provider.assert_called_once_with('POST','verify',body={'email':USER['email'],'token':'123456','type':'signup'})
        cookies = result.headers.get_list('set-cookie')
        assert len(cookies) == 2
        assert all('Secure' in x and 'HttpOnly' in x and 'SameSite=lax' in x and 'Path=/' in x for x in cookies)
        assert result.headers['cache-control'] == 'no-store'
        assert 'private-access' not in result.text
    with patch('app.accounts.provider', return_value=USER):
        assert client.get('/api/profiles',headers={'X-Pocket-Guru-User':USER['id']}).status_code == 200
        assert client.get('/api/profiles',headers={'X-Pocket-Guru-User':'account-b'}).status_code == 401


def test_wrong_code_never_grants_session(client):
    with patch('app.accounts.provider', side_effect=HTTPException(400,'That code is incorrect or expired.')):
        result = client.post('/api/auth/verify',json={'email':USER['email'],'code':'000000'})
        assert result.status_code == 400
        assert not result.headers.get('set-cookie')
    assert client.post('/api/auth/verify',json={'email':USER['email'],'code':'123'}).status_code == 422


def test_cross_origin_or_missing_origin_rejected_before_provider(client):
    with patch('app.accounts.provider') as provider:
        for origin in ['https://evil.test','']:
            assert client.post('/api/auth/signup',json=CREDS,headers={'Origin':origin}).status_code == 403
        provider.assert_not_called()


def test_refresh_and_signout(client):
    client.cookies.set(REFRESH_COOKIE,'old-refresh')
    with patch('app.accounts.provider', return_value=SESSION) as provider:
        result = client.post('/api/auth/session')
        assert result.json()['user']['verified']
        provider.assert_called_once_with('POST','token?grant_type=refresh_token',body={'refresh_token':'old-refresh'})
    with patch('app.accounts.provider', side_effect=HTTPException(503,'offline')):
        result = client.post('/api/auth/signout')
        assert result.json()['signed_out']
        assert all('Max-Age=0' in x for x in result.headers.get_list('set-cookie'))


def test_password_reset_uses_code_before_setting_password(client):
    calls=[]
    def fake(method,path,**kwargs):
        calls.append((method,path,kwargs))
        return SESSION if path == 'verify' else USER
    with patch('app.accounts.provider', side_effect=fake):
        assert client.post('/api/auth/verify',json={'email':USER['email'],'code':'123456','purpose':'recovery'}).status_code == 400
        assert not calls
        result=client.post('/api/auth/verify',json={'email':USER['email'],'code':'123456','purpose':'recovery','new_password':'new-secure-password'})
        assert result.status_code == 200
        assert calls[0][2]['body']['type'] == 'recovery'
        assert calls[1] == ('PUT','user',{'token':'private-access','body':{'password':'new-secure-password'}})


def test_resend_and_rate_limit(client):
    with patch('app.accounts.provider', return_value={}) as provider:
        assert client.post('/api/auth/resend',json={'email':USER['email']}).status_code == 200
        provider.assert_called_once_with('POST','resend',body={'email':USER['email'],'type':'signup'})
        for _ in range(9):
            assert client.post('/api/auth/recover',json={'email':USER['email']}).status_code == 200
        assert client.post('/api/auth/recover',json={'email':USER['email']}).status_code == 429
        assert provider.call_count == 10


def test_data_and_attachment_ownership(client):
    app.dependency_overrides[current_user] = lambda: {'id':'account-a'}
    diagnosis=client.post('/api/diagnoses',json={'category':'automotive','symptom':'no start'}).json()
    profile=client.post('/api/profiles',json={'name':'A truck','category':'automotive'}).json()
    upload=client.post('/api/uploads',files={'files':('private.jpg',b'photo','image/jpeg')}).json()['files'][0]
    try:
        assert 'owner_id' not in profile
        app.dependency_overrides[current_user] = lambda: {'id':'account-b'}
        assert client.get('/api/diagnoses/'+diagnosis['id']).status_code == 404
        assert diagnosis['id'] not in [x['id'] for x in client.get('/api/diagnoses').json()]
        assert profile['id'] not in [x['id'] for x in client.get('/api/profiles').json()]
        with patch('app.main.analyze_uploaded_images',return_value={'available':False,'analyzed_files':[]}) as analyzer:
            result=client.post('/api/diagnoses',json={'category':'automotive','symptom':'no start','answers':{'media':[upload]}})
            assert result.status_code == 201
            assert analyzer.call_args.args[0] == []
            assert 'Upload them again' in result.json()['visual_analysis']['attachment_warning']
    finally:
        (UPLOAD_DIR/upload['stored_name']).unlink(missing_ok=True)
        UPLOADED_MEDIA.pop(upload['id'],None)
        DIAGNOSES.clear();DIAGNOSIS_OWNERS.clear();PROFILES.clear()


def test_config_does_not_expose_keys(client,monkeypatch):
    monkeypatch.setenv('SUPABASE_URL','https://project.supabase.co')
    monkeypatch.setenv('SUPABASE_PUBLISHABLE_KEY','never-return-this')
    result=client.get('/api/auth/config')
    assert result.json() == {'configured':True}
    assert 'never-return-this' not in result.text
    assert result.headers['cache-control'] == 'no-store'


def test_provider_calls_trusted_auth_endpoint_and_hides_upstream_errors(monkeypatch):
    import httpx
    from app.accounts import provider
    monkeypatch.setenv('SUPABASE_URL','https://project.supabase.co')
    monkeypatch.setenv('SUPABASE_PUBLISHABLE_KEY','publishable')
    with patch('app.accounts.httpx.Client') as factory:
        http=factory.return_value.__enter__.return_value
        http.request.return_value=httpx.Response(200,json=USER)
        assert provider('GET','user',token='access') == USER
        http.request.assert_called_once_with('GET','https://project.supabase.co/auth/v1/user',headers={'apikey':'publishable','Content-Type':'application/json','Authorization':'Bearer access'},json=None)
        for status,detail in [(503,503),(400,401)]:
            http.request.return_value=httpx.Response(status,json={'msg':'SECRET PROVIDER DETAIL'})
            with pytest.raises(HTTPException) as error:
                provider('POST','token?grant_type=password',body=CREDS)
            assert error.value.status_code == detail
            assert 'SECRET' not in error.value.detail


def test_invalid_refresh_clears_session_but_outage_does_not(client):
    client.cookies.set(REFRESH_COOKIE,'invalid')
    with patch('app.accounts.provider',side_effect=HTTPException(401,'invalid')):
        result=client.post('/api/auth/session')
        assert result.json() == {'user':None}
        assert len(result.headers.get_list('set-cookie')) == 2
    client.cookies.set(REFRESH_COOKIE,'valid')
    with patch('app.accounts.provider',side_effect=HTTPException(503,'temporary outage')):
        result=client.post('/api/auth/session')
        assert result.status_code == 503
        assert not result.headers.get('set-cookie')
