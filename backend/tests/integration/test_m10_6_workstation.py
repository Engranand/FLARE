"""M10.6 acceptance against real originals and isolated PostgreSQL."""
import os
from pathlib import Path
import time
import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import create_app
from app.api.workstation import connection
from app.core.config import Settings
from tests.integration.test_m10_5_integration import m10_5_db

pytestmark = pytest.mark.postgres

@pytest.fixture
def client(m10_5_db):
    app = create_app(Settings(_env_file=None, database_url=None))
    app.state.db_engine = m10_5_db
    return TestClient(app)


def test_catalog_and_sealed_results(client):
    r = client.get('/api/v1/workstation/summary')
    assert r.status_code == 200, r.text
    data = r.json()['data']
    assert data['counts']['records'] == 129
    assert data['counts']['experimental_records'] == 129
    assert data['counts']['validated_results'] == 20
    assert data['counts']['indexed_documents'] > 0
    assert all(m['seal']['member_digest'] for m in data['metrics'])


def test_scientific_populations(client):
    data = client.get('/api/v1/workstation/science').json()['data']
    charts = {c['key']: c for c in data['charts']}
    assert charts['initial_o2']['sample_size'] == 129
    assert charts['initial_o2']['median'] == '0.182'
    assert charts['depletion']['sample_size'] == 122
    assert charts['depletion']['bins'][0]['low'] < 0
    assert data['oxygen_quality']['NEGATIVE_SENSOR_DRIFT'] == 5
    assert data['oxygen_quality']['QUARANTINED_GROSS_ANOMALY'] == 5
    assert charts['airflow']['sample_size'] == 24
    assert data['unique_specimens'] == 107 and data['repeated_specimens'] == 20
    assert charts['co']['sample_size'] == 126
    assert charts['co2']['sample_size'] == 127
    for c in charts.values():
        assert sum(b['count'] for b in c['bins']) == c['sample_size']
        assert c['sha256'] and c['unit']


def test_pagination_filtering_sort_and_inspector(client):
    first = client.get('/api/v1/workstation/observations?page_size=7').json()
    second = client.get('/api/v1/workstation/observations?page_size=7&page=2').json()
    assert len(first['items']) == len(second['items']) == 7
    assert not {r['id'] for r in first['items']} & {r['id'] for r in second['items']}
    record = first['items'][0]
    detail = client.get('/api/v1/workstation/observations', params={'record_id':record['id']}).json()
    assert detail['total'] == 1
    assert detail['items'][0]['experimental_conditions']
    assert detail['items'][0]['oxygen_eligibility']['category']
    assert len(client.get('/api/v1/workstation/observations').json()['items']) == 25
    assert detail['items'][0]['sha256'] == record['sha256']
    filters = client.get('/api/v1/workstation/filters').json()['data']
    assert 'PSI-25' in filters['investigation']
    var = filters['variable'][0]
    filtered = client.get('/api/v1/workstation/observations', params={'variable':var,'sort':'value','direction':'desc'}).json()
    assert all(r['variable']==var for r in filtered['items'])
    assert client.get('/api/v1/workstation/observations',params={'q':"'; DROP TABLE observation; --"}).json()['total']==0
    assert client.get('/api/v1/workstation/observations?page_size=101').status_code==422
    assert client.get('/api/v1/workstation/observations?sort=arbitrary_sql').status_code==422


def test_comparison_validation_and_overlap(client):
    r=client.post('/api/v1/workstation/comparison',json={'a':{},'b':{}})
    assert r.status_code==200, r.text
    data=r.json()['data']
    assert data['a']['sample_size']==129 and data['overlap']==129
    assert client.post('/api/v1/workstation/comparison',json={'a':{'investigation':'PSI-117'},'b':{}}).status_code==422
    assert client.post('/api/v1/workstation/comparison',json={'a':{'airflow_min':1},'b':{}}).status_code==422
    assert client.post('/api/v1/workstation/comparison',json={'a':{'oxygen_min':20,'oxygen_max':10},'b':{}}).status_code==422
    result=client.post('/api/v1/workstation/comparison',json={'a':{'airflow_min':2,'airflow_max':15},'b':{}}).json()['data']
    assert result['a']['sample_size']==24


def test_evidence_and_reference_resolution(client):
    r=client.get('/api/v1/workstation/evidence?q=microgravity%20flame')
    assert r.status_code==200,r.text
    passages=r.json()['result_data']
    assert passages
    passage=passages[0]
    detail=client.get('/api/v1/workstation/passages/'+passage['chunk_id'])
    assert detail.status_code==200
    assert detail.json()['data']['sha256']==passage['source_document_sha256']
    resolved=client.get('/api/v1/workstation/reference',params={'uri':passage['flare_uri']})
    assert resolved.status_code==200
    assert resolved.json()['data']['chunk_id']==passage['chunk_id']
    assert client.get('/api/v1/workstation/reference',params={'uri':'flare:result:M9-P1-ENV-STATS:ambient_initial_o2_median'}).status_code==200
    assert client.get('/api/v1/workstation/reference',params={'uri':'https://untrusted.example'}).status_code==422


def test_readonly_transaction(client):
    # Exercise the actual dependency and verify server-side transaction policy.
    with connection_context(client.app) as conn:
        assert conn.execute(text('SHOW transaction_read_only')).scalar_one()=='on'
        assert conn.execute(text('SHOW statement_timeout')).scalar_one()=='5s'

from contextlib import contextmanager
@contextmanager
def connection_context(app):
    from starlette.requests import Request
    generator=connection(Request({'type':'http','app':app}))
    conn=next(generator)
    try:
        yield conn
    finally:
        generator.close()


def test_concurrent_workstation_reads(client):
    from concurrent.futures import ThreadPoolExecutor
    paths = ['summary', 'science', 'observations', 'filters'] * 2
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda path: client.get('/api/v1/workstation/'+path), paths))
    assert all(r.status_code == 200 for r in responses), [(r.status_code, r.text[:100]) for r in responses]


def test_optional_browser_preview(m10_5_db):
    if os.environ.get('FLARE_M106_PREVIEW') != '1':
        pytest.skip('Interactive preview is opt-in')
    import uvicorn
    app=create_app(Settings(_env_file=None,database_url=None))
    # Reuse the fully seeded isolated acceptance database; no development database is modified.
    from contextlib import asynccontextmanager
    @asynccontextmanager
    async def lifespan(app):
        app.state.db_engine=m10_5_db
        yield
    app.router.lifespan_context=lifespan
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=8000,log_level='warning'))
    thread=threading.Thread(target=server.run,daemon=True)
    thread.start()
    print('M10.6 isolated preview ready on port 8000',flush=True)
    stop=Path(__file__).parents[3]/'scratch/m106-preview-stop'
    deadline=time.monotonic()+3600
    while not stop.exists() and time.monotonic()<deadline:
        time.sleep(1)
    server.should_exit=True
    thread.join(timeout=10)
