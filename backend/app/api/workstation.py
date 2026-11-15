"""Bounded, read-only workstation endpoints. No ingestion or client-defined SQL."""
from typing import Any, Literal
from uuid import UUID, uuid4
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.analysis.engine import AUTHENTIC_SHA256, load_authenticated_records
from app.intelligence.tool_executor import execute_m9_get_analytical_result, execute_flare_retrieve_documents
from app.intelligence.tool_schemas import ToolResult
from app.services.workstation import science_data, distribution, number, O2
from app.analysis.p3_airflow import classify_airflow_record

router = APIRouter(prefix='/workstation', tags=['workstation'])

class Payload(BaseModel):
    data: dict[str, Any]

class Page(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int


def connection(request: Request):
    engine = getattr(request.app.state, 'db_engine', None)
    if engine is None:
        raise HTTPException(503, 'Scientific database is not configured. No substitute data is shown.')
    try:
        with engine.connect() as conn, conn.begin():
            conn.execute(text('SET LOCAL transaction_read_only = on'))
            conn.execute(text('SET LOCAL statement_timeout = 5000'))
            # Short interactive queries must not incur PostgreSQL JIT compilation costs.
            conn.execute(text('SET LOCAL jit = off'))
            yield conn
    except SQLAlchemyError:
        raise HTTPException(503, 'Scientific data could not be read. Check database availability and schema readiness.') from None


def rows(conn, sql, params=None):
    return [dict(r) for r in conn.execute(text(sql), params or {}).mappings()]


def authenticated_records(conn):
    present = conn.execute(text('SELECT count(*) FROM source_document WHERE sha256=:sha'), {'sha': AUTHENTIC_SHA256}).scalar()
    if not present:
        raise HTTPException(404, 'Authenticated BASS-II source has not been registered in this database.')
    try:
        return load_authenticated_records()
    except (ValueError, FileNotFoundError):
        raise HTTPException(409, 'Original BASS-II source unavailable or failed SHA-256 verification.') from None


@router.get('/summary', response_model=Payload)
def summary(conn=Depends(connection)):
    investigations = rows(conn, '''SELECT i.investigation_code, i.name, i.description,
        i.source_repository_url, (SELECT count(*) FROM source_record s WHERE s.investigation_id=i.id) AS records,
        (SELECT count(*) FROM source_document d WHERE d.investigation_id=i.id) AS documents
        FROM investigation i ORDER BY i.investigation_code''')
    documents = rows(conn, '''SELECT d.id, i.investigation_code, d.original_filename, d.sha256, d.source_type,
        d.metadata->>'title' AS title, d.metadata->>'epistemic_attribution' AS attribution,
        d.metadata->>'document_type' AS document_type, d.created_at,
        (SELECT count(*) FROM document_chunk c WHERE c.source_document_id=d.id) AS passages
        FROM source_document d JOIN investigation i ON i.id=d.investigation_id ORDER BY d.created_at DESC LIMIT 100''')
    counts = rows(conn, '''SELECT (SELECT count(*) FROM source_record) AS records,
        (SELECT count(DISTINCT source_document_id) FROM document_chunk) AS indexed_documents,
        (SELECT count(*) FROM document_chunk) AS passages,
        (SELECT count(*) FROM investigation) AS investigations''')[0]
    tool = execute_m9_get_analytical_result(conn, {'investigation': 'PSI-25'}, uuid4())
    metrics = tool.result_data if tool.execution_status.value == 'SUCCESS' else []
    counts['validated_results'] = len(metrics) if tool.execution_status.value in ('SUCCESS', 'NO_RESULTS') else None
    # Unique specimens are supplied by authenticated M9 source grouping, not guessed from tests.
    counts['unique_specimens'] = None
    counts['experimental_records'] = conn.execute(text('''SELECT count(*) FROM source_record sr
        JOIN parse_run pr ON (pr.investigation_id,pr.id)=(sr.investigation_id,sr.parse_run_id)
        JOIN source_document d ON (d.investigation_id,d.id)=(pr.investigation_id,pr.source_document_id)
        WHERE d.sha256=:sha OR d.metadata->>'epistemic_attribution'='experimental_observation' '''), {'sha':AUTHENTIC_SHA256}).scalar_one()
    return Payload(data={'counts': counts, 'investigations': investigations, 'documents': documents,
                         'metrics': metrics, 'metric_status': tool.execution_status.value,
                         'limitations': tool.limitations, 'evidence': tool.evidence_references})


@router.get('/science', response_model=Payload)
def science(conn=Depends(connection)):
    return Payload(data=science_data(authenticated_records(conn)))


OBS_FROM = ''' FROM observation o
 JOIN investigation i ON i.id=o.investigation_id
 JOIN source_record sr ON (sr.investigation_id,sr.id)=(o.investigation_id,o.source_record_id)
 JOIN source_field sf ON (sf.investigation_id,sf.id)=(o.investigation_id,o.source_field_id)
 JOIN parse_run pr ON (pr.investigation_id,pr.id)=(o.investigation_id,o.parse_run_id)
 JOIN source_document d ON (d.investigation_id,d.id)=(pr.investigation_id,pr.source_document_id)
 JOIN evidence_reference e ON (e.investigation_id,e.id)=(o.investigation_id,o.evidence_id)
'''
# Attribution is explicit metadata only; the authenticated M9 source has a known experimental identity.
ATTR = "CASE WHEN d.sha256=:auth_sha THEN 'experimental_observation' ELSE COALESCE(d.metadata->>'epistemic_attribution','unresolved_attribution') END"

@router.get('/observations', response_model=Page)
def observations(page: int = Query(1, ge=1, le=100000), page_size: int = Query(25, ge=1, le=100),
                 q: str = Query('', max_length=200), investigation: str = Query('', max_length=80),
                 dataset: str = Query('', max_length=250), variable: str = Query('', max_length=250),
                 quality: str = Query('', max_length=100), attribution: str = Query('', max_length=80),
                 source_row: int | None = Query(None, ge=1), record_id: UUID | None = None,
                 sort: Literal['row','variable','value'] = 'row', direction: Literal['asc','desc'] = 'asc',
                 conn=Depends(connection)):
    where = ['TRUE']
    params = {'auth_sha': AUTHENTIC_SHA256, 'limit': page_size, 'offset': (page-1)*page_size}
    for key, value, expression in [('investigation', investigation, 'i.investigation_code'), ('dataset', dataset, 'd.original_filename'),
                                   ('variable', variable, 'sf.original_header'), ('quality', quality, 'o.parser_classification'),
                                   ('attribution', attribution, ATTR), ('source_row', source_row, 'sr.source_record_number'), ('record_id', record_id, 'o.id')]:
        if value is not None and value != '':
            where.append(f'{expression}=:{key}')
            params[key] = value
    if q:
        where.append("(sf.original_header ILIKE :q OR COALESCE(o.raw_value,'') ILIKE :q OR sr.source_row_id ILIKE :q)")
        params['q'] = '%' + q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
    clause = OBS_FROM + ' WHERE ' + ' AND '.join(where)
    total = conn.execute(text('SELECT count(*)' + clause), params).scalar_one()
    order = {'row':'sr.source_record_number, sf.ordinal', 'variable':'sf.original_header', 'value':'o.raw_value'}[sort]
    items = rows(conn, '''SELECT o.id, i.investigation_code, sr.source_row_id AS test_identifier,
        sr.source_record_number, sf.original_header AS variable, o.raw_value AS value, o.raw_unit AS unit,
        o.source_value_kind, o.parser_classification AS quality, o.parser_flags, d.original_filename AS dataset,
        d.sha256, e.locator AS source_locator, e.verification_status, ''' + ATTR + ' AS attribution' + clause +
        f' ORDER BY {order} {direction}, o.id LIMIT :limit OFFSET :offset', params)
    if record_id and items:
        item = items[0]
        item['annotations'] = rows(conn, """SELECT sv.variable_code, sa.value_kind, sa.numeric_value,
            sa.interpreted_unit, sa.unit_status, sa.revision, sa.transformation_method
            FROM semantic_annotation sa JOIN scientific_variable sv ON (sv.investigation_id,sv.id)=(sa.investigation_id,sa.variable_id)
            WHERE sa.observation_id=:id ORDER BY sa.revision DESC LIMIT 100""", {'id':record_id})
        item['quality_issues'] = rows(conn, """SELECT issue_type, description, severity FROM data_quality_issue
            WHERE observation_id=:id ORDER BY created_at LIMIT 100""", {'id':record_id})
        if item['sha256'] == AUTHENTIC_SHA256:
            source = next((r for r in authenticated_records(conn) if r['csv_record_number']==item['source_record_number']), None)
            if source:
                from dataclasses import asdict
                from app.analysis.p2_oxygen import classify_oxygen_record
                item['experimental_conditions'] = {k:source.get(k) for k in [O2,'Calibrated final O2 % by vol','Air display','Fuel Sample Material','Sample #']}
                item['oxygen_eligibility'] = asdict(classify_oxygen_record(source))
                item['airflow_eligibility'] = asdict(classify_airflow_record(source))
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get('/filters', response_model=Payload)
def filters(conn=Depends(connection)):
    result = {}
    for key, column in [('investigation','i.investigation_code'), ('dataset','d.original_filename'), ('variable','sf.original_header'), ('quality','o.parser_classification'), ('attribution',ATTR)]:
        result[key] = [r['value'] for r in rows(conn, 'SELECT DISTINCT ' + column + ' AS value' + OBS_FROM + ' ORDER BY value LIMIT 500', {'auth_sha': AUTHENTIC_SHA256})]
    return Payload(data=result)


@router.get('/evidence', response_model=ToolResult)
def evidence(q: str = Query(..., min_length=2, max_length=500), conn=Depends(connection)):
    return execute_flare_retrieve_documents(parameters={'query': q, 'limit': 10}, request_id=uuid4(), conn=conn)


@router.get('/passages/{chunk_id}', response_model=Payload)
def passage(chunk_id: UUID, conn=Depends(connection)):
    result = rows(conn, '''SELECT c.id, c.chunk_text, c.page_start, c.page_end, c.section_title,
        c.chunk_index, c.source_document_id, d.original_filename, d.sha256, d.metadata,
        (SELECT id FROM document_chunk p WHERE p.source_document_id=c.source_document_id AND p.chunk_index<c.chunk_index ORDER BY p.chunk_index DESC LIMIT 1) AS previous,
        (SELECT id FROM document_chunk n WHERE n.source_document_id=c.source_document_id AND n.chunk_index>c.chunk_index ORDER BY n.chunk_index LIMIT 1) AS next
        FROM document_chunk c JOIN source_document d ON (d.investigation_id,d.id)=(c.investigation_id,c.source_document_id) WHERE c.id=:id''', {'id':chunk_id})
    if not result:
        raise HTTPException(404, 'Passage not found')
    return Payload(data=result[0])


class Condition(BaseModel):
    investigation: Literal['PSI-25'] = 'PSI-25'
    oxygen_min: Decimal = Field(0, ge=0, le=100)
    oxygen_max: Decimal = Field(100, ge=0, le=100)
    airflow_min: Decimal | None = Field(None, ge=2, le=15)
    airflow_max: Decimal | None = Field(None, ge=2, le=15)
    fuel: str = Field('', max_length=250)

    @model_validator(mode='after')
    def valid_ranges(self):
        if self.oxygen_min > self.oxygen_max or (self.airflow_min is not None and self.airflow_max is not None and self.airflow_min > self.airflow_max):
            raise ValueError('Minimum must not exceed maximum')
        return self

class ComparisonRequest(BaseModel):
    a: Condition
    b: Condition

@router.post('/comparison', response_model=Payload)
def comparison(payload: ComparisonRequest, conn=Depends(connection)):
    records = authenticated_records(conn)
    output = {}
    selected_rows = []
    for name, condition in [('a',payload.a), ('b',payload.b)]:
        selected = []
        for r in records:
            oxygen = number(r.get(O2))
            if oxygen is None or not condition.oxygen_min <= oxygen <= condition.oxygen_max:
                continue
            if condition.fuel and r.get('Fuel Sample Material','').strip() != condition.fuel:
                continue
            if condition.airflow_min is not None or condition.airflow_max is not None:
                flow = classify_airflow_record(r)
                if not flow.is_eligible_static or flow.raw_scalar_display is None or not Decimal(2) <= flow.raw_scalar_display <= Decimal(15):
                    continue
                if not (condition.airflow_min or Decimal(2)) <= flow.raw_scalar_display <= (condition.airflow_max or Decimal(15)):
                    continue
            selected.append(r)
        selected_rows.append({r['csv_record_number'] for r in selected})
        output[name] = distribution(name, f'Condition {name.upper()} • initial oxygen', 'mol/mol', [(number(r[O2])/100,r['csv_record_number']) for r in selected], len(records), ['Descriptive subset, not a sealed M9 population metric. No causal or inferential comparison.', 'Repeated specimens may occur in both groups.'])
    output['overlap'] = len(selected_rows[0] & selected_rows[1])
    return Payload(data=output)

@router.get('/reference', response_model=Payload)
def resolve_reference(uri: str = Query(..., max_length=500), conn=Depends(connection)):
    import re
    result_match = re.fullmatch(r'flare:result:(M9-P[1-4]-[A-Z0-9-]+):([a-z0-9_]+)', uri)
    if result_match:
        result = execute_m9_get_analytical_result(conn, {'investigation':'PSI-25', 'protocol_code':result_match[1], 'metric_code':result_match[2]}, uuid4())
        if result.execution_status.value != 'SUCCESS' or not result.result_data:
            raise HTTPException(404, 'Verified analytical reference could not be resolved.')
        return Payload(data={'kind':'analytical_result', 'result':result.model_dump(mode='json')})
    doc_match = re.fullmatch(r'flare:doc:([a-f0-9]{64}):page=(\d+)', uri)
    chunk_match = re.fullmatch(r'flare://source_document/([a-f0-9-]{36})#(?:page=[^&]+&)?chunk=(\d+)', uri)
    if doc_match:
        found = rows(conn, '''SELECT c.id FROM document_chunk c JOIN source_document d ON d.id=c.source_document_id
          WHERE d.sha256=:sha AND c.page_start<=:page AND c.page_end>=:page ORDER BY c.chunk_index LIMIT 1''', {'sha':doc_match[1],'page':int(doc_match[2])})
    elif chunk_match:
        found = rows(conn, 'SELECT id FROM document_chunk WHERE source_document_id=:id AND chunk_index=:idx', {'id':UUID(chunk_match[1]),'idx':int(chunk_match[2])})
    else:
        raise HTTPException(422, 'Reference does not contain a resolvable source identity. No reference is inferred.')
    if not found:
        raise HTTPException(404, 'Source reference not found in indexed passages.')
    return Payload(data={'kind':'document_passage', 'chunk_id':str(found[0]['id'])})
