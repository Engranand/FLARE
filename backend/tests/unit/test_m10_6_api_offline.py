from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import Settings


def test_workstation_unconfigured_and_cors():
    with TestClient(create_app(Settings(_env_file=None,database_url=None))) as client:
        for path in ('summary','science','observations','filters'):
            r=client.get('/api/v1/workstation/'+path)
            assert r.status_code==503
            assert 'not configured' in r.json()['detail']
        response=client.options('/api/v1/intelligence/execute',headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type'})
        assert response.status_code==200
        denied=client.options('/api/v1/intelligence/execute',headers={'Origin':'https://untrusted.example','Access-Control-Request-Method':'POST'})
        assert denied.status_code==400
