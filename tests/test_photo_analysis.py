from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app, UPLOADED_MEDIA
from app.vision_engine import VisionUnavailableError

client = TestClient(app)

def request(media):
    return client.post('/api/diagnoses', json={'category':'appliance','symptom':'The oven does not heat','answers':{'media':media}})

def test_uploaded_photo_reaches_analyzer_using_server_metadata():
    upload = client.post('/api/uploads', files={'files':('label.jpg',b'test-image','image/jpeg')})
    assert upload.status_code == 200
    record = upload.json()['files'][0]
    try:
        with patch('app.main.analyze_uploaded_images', return_value={'available':True,'model':'MER6600FZ','analyzed_files':['label.jpg']}) as analyzer:
            response = request([{**record,'stored_name':'../../secret','content_type':'text/plain'}])
            assert response.status_code == 201
            assert response.json()['visual_analysis']['model'] == 'MER6600FZ'
            assert analyzer.call_args.args[0] == [record]
    finally:
        from app.main import UPLOAD_DIR
        (UPLOAD_DIR / record['stored_name']).unlink()
        UPLOADED_MEDIA.pop(record['id'],None)

def test_unavailable_photo_analysis_does_not_claim_success_or_break_diagnosis():
    with patch('app.main.analyze_uploaded_images', side_effect=VisionUnavailableError('missing key')):
        response = request([{'id':'expired'}])
        assert response.status_code == 201
        assert response.json()['visual_analysis']['available'] is False
        assert response.json()['causes']

def test_expired_media_reports_reupload():
    with patch('app.main.analyze_uploaded_images', return_value={'available':False,'analyzed_files':[]}) as analyzer:
        response = request([{'id':'expired','stored_name':'../../secret'}])
        assert analyzer.call_args.args[0] == []
        assert 'Upload them again' in response.json()['visual_analysis']['attachment_warning']

def test_symptom_only_request_does_not_call_paid_image_service():
    with patch('app.main.analyze_uploaded_images') as analyzer:
        response = request([])
        assert response.status_code == 201
        assert response.json()['visual_analysis'] is None
        analyzer.assert_not_called()


def test_failed_batch_removes_partial_uploads(tmp_path):
    with patch('app.main.UPLOAD_DIR',tmp_path):
        response=client.post('/api/uploads',files=[('files',('good.jpg',b'image','image/jpeg')),('files',('bad.exe',b'bad','application/octet-stream'))])
        assert response.status_code==415
        assert list(tmp_path.iterdir())==[]
