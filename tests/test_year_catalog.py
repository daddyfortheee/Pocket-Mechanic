from unittest.mock import patch, MagicMock
import json
from fastapi.testclient import TestClient
from app.main import app
from app.vehicle_catalog import motorcycle_models

client=TestClient(app)

def test_1980_kawasaki_only_documented_period_models():
    response=client.get('/api/vehicles/models',params={'category':'motorcycle','year':1980,'make':'Kawasaki'})
    assert response.status_code==200
    models=response.json()['options']
    assert 'KZ550-A1' in models and 'KDX175-A1' in models
    assert not any('Ninja' in model or 'Vulcan' in model for model in models)

def test_farm_year_and_make_exclude_other_periods_and_brands():
    params={'category':'equipment','year':1968,'make':'John Deere'}
    models=client.get('/api/vehicles/models',params=params).json()['options']
    assert '4020' in models and '3020' in models
    assert '1025R' not in models and '4440' not in models and '8N' not in models
    params.update(year=1950,make='Ford')
    assert '8N' in client.get('/api/vehicles/models',params=params).json()['options']
    params['year']=1980
    assert '8N' not in client.get('/api/vehicles/models',params=params).json()['options']

def test_year_scoped_auto_catalog_keeps_make_model_dependencies():
    with patch('app.vehicle_catalog.fetch_menu',return_value=('F150',)) as fetch:
        response=client.get('/api/vehicles/models',params={'year':1993,'make':'Ford'})
        assert response.json()['options']==['F150']
        assert fetch.call_args.args[:4]==('model',1993,'Ford','')
    assert client.get('/api/vehicles/models',params={'year':1993}).status_code==422

def test_motorcycle_api_filters_unreliable_years_and_wrong_make():
    motorcycle_models.cache_clear()
    responses=[]
    for data in [{'Results':[{'Make_Name':'KAWASAKI','Model_Name':'Ninja ZX-10R'},{'Make_Name':'KAWASAKI','Model_Name':'Ninja 400'}]},
                 {'results':[{'modelYear':'2004','make':'KAWASAKI','model':'NINJA ZX-10R'},
                             {'modelYear':'2020','make':'KAWASAKI','model':'Ninja 400'},
                             {'modelYear':'2004','make':'HONDA','model':'Ninja 400'}]}]:
        response=MagicMock();response.__enter__.return_value.read.return_value=json.dumps(data).encode();responses.append(response)
    with patch('app.vehicle_catalog.urlopen',side_effect=responses):
        options,source=motorcycle_models(2004,'Kawasaki',123)
        assert options==('NINJA ZX-10R',)
        assert 'year-specific' in source
    motorcycle_models.cache_clear()
