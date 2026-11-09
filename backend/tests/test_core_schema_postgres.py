"""M4.2 tests use only owned disposable databases and labelled technical fixtures."""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.util import CommandError
from sqlalchemy import create_engine, inspect, text, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db.base import Base
from app.db.migrations import migration_config
from app.models import Investigation, SourceDocument, MetadataRevision, Observation, AnalyticalResult
from test_scientific_models import approved_statements

pytestmark = pytest.mark.postgres


@pytest.fixture(scope='module')
def schema_databases(postgres_engines):
    owner, _ = postgres_engines
    assert owner.url.database.startswith('flare_test_')
    engines = []
    names = []
    try:
        for purpose in ('implementation', 'oracle', 'orm'):
            name = f'flare_schema_{purpose}_{uuid4().hex}'
            with owner.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
                conn.exec_driver_sql(f'CREATE DATABASE "{name}"')
            names.append(name)
            engines.append(create_engine(owner.url.set(database=name), hide_parameters=True))
        with engines[0].begin() as conn:
            config = migration_config(); config.attributes['connection'] = conn
            command.upgrade(config, '0002_m42_core_schema')
        with engines[1].begin() as conn:
            for statement in approved_statements():
                conn.exec_driver_sql(statement)
        # Test-only materialization also verifies CHECKs that autogeneration omits.
        Base.metadata.create_all(engines[2])
        yield engines
    finally:
        for engine in engines:
            engine.dispose()
        for name in names:
            with owner.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
                conn.exec_driver_sql(f'DROP DATABASE "{name}"')


def catalog(engine):
    with engine.connect() as conn:
        inspector = inspect(conn)
        names = set(inspector.get_table_names()) - {'alembic_version'}
        tables = {}
        for name in sorted(names):
            columns = [(c['name'], str(c['type']), c['nullable'], c['default']) for c in inspector.get_columns(name)]
            pk = inspector.get_pk_constraint(name)['constrained_columns']
            uq = sorted(tuple(c['column_names']) for c in inspector.get_unique_constraints(name))
            checks = sorted(c['sqltext'] for c in inspector.get_check_constraints(name))
            fks = sorted((c['name'], tuple(c['constrained_columns']), c['referred_table'], tuple(c['referred_columns']), c['options'].get('ondelete')) for c in inspector.get_foreign_keys(name))
            indexes = sorted((i['name'], tuple(i['column_names']), i['unique'], i['dialect_options'].get('postgresql_where')) for i in inspector.get_indexes(name) if not i.get('duplicates_constraint'))
            tables[name] = (columns, pk, uq, checks, fks, indexes)
        assert inspector.get_enums() == []
        return tables


def test_catalog_exactly_matches_approved_ddl(schema_databases):
    actual, expected, orm = map(catalog, schema_databases)
    assert actual == expected == orm
    assert len(actual) == 33
    assert sum(len(t[4]) for t in actual.values()) == 140
    assert sum(len(t[5]) for t in actual.values()) == 112
    # Resolve every FK against a real PK/UNIQUE with compatible ordered types.
    for table in actual.values():
        local = {c[0]: c[1] for c in table[0]}
        for _, cols, parent, refs, action in table[4]:
            assert action == 'RESTRICT'
            target = actual[parent]
            assert refs in [tuple(target[1]), *target[2]]
            remote = {c[0]: c[1] for c in target[0]}
            assert [local[c] for c in cols] == [remote[c] for c in refs]
    with schema_databases[0].begin() as conn:
        assert conn.exec_driver_sql('SHOW server_version_num').scalar_one() == '170011'
        assert compare_metadata(MigrationContext.configure(conn), Base.metadata) == []


def test_confirmed_downgrade_and_reproducible_upgrade(schema_databases):
    engine = schema_databases[0]
    with pytest.raises(CommandError, match='explicit'):
        with engine.begin() as conn:
            config = migration_config(); config.attributes['connection'] = conn
            command.downgrade(config, '0001_m41_baseline')
    assert len(catalog(engine)) == 33
    with engine.begin() as conn:
        config = migration_config(); config.attributes.update(connection=conn, allow_destructive_downgrade=True)
        command.downgrade(config, '0001_m41_baseline')
        assert inspect(conn).get_table_names() == ['alembic_version']
        command.upgrade(config, '0002_m42_core_schema')
        command.upgrade(config, '0002_m42_core_schema')
    assert catalog(engine) == catalog(schema_databases[1])


@pytest.fixture
def technical(schema_databases):
    with schema_databases[0].connect() as conn:
        transaction = conn.begin()
        session = Session(conn)
        now = datetime.now(timezone.utc)
        inv = uuid4()
        def add(table, **values):
            row = dict(investigation_id=inv, id=uuid4(), created_at=now) | values
            conn.execute(Base.metadata.tables[table].insert(), row)
            return row['id']
        conn.execute(Base.metadata.tables['investigation'].insert(), dict(id=inv, repository_code='technical_fixture', investigation_code=str(inv), name='NOT NASA - schema test', agency='technical_fixture', source_repository_url='urn:technical:fixture', metadata={'technical': True}, created_at=now))
        doc = add('source_document', original_filename='technical.txt', source_type='other', artifact_origin='software_artifact', sha256='a'*64, file_size_bytes=0, storage_key='technical_fixture', metadata={})
        evidence = add('evidence_reference', source_document_id=doc, locator_kind='document', locator_key='technical', locator_version='technical-v1', locator={}, location_basis='technical_fixture', extraction_method='technical_fixture', extractor_version='1', verification_status='unverified', verification_scope='schema test')
        def parse(version):
            return add('parse_run', source_document_id=doc, parser_name='technical_fixture', parser_version=version, code_sha256='b'*64, code_storage_key='technical', configuration_sha256='c'*64, configuration={}, output_sha256='d'*64, output_storage_key='technical', record_count=0, status='complete')
        run = parse('1'); other_run = parse('2')
        record = add('source_record', parse_run_id=run, table_key='technical', source_record_number=1, source_row_id='technical-row', row_evidence_id=evidence)
        field = add('source_field', parse_run_id=run, table_key='technical', ordinal=1, original_header='technical', raw_unit_status='not_stated', header_evidence_id=evidence)
        protocol = add('analysis_protocol', issue_policy='all_unresolved_review_or_blocking', coverage_policy='every_input_test_segment', protocol_code='technical_fixture', protocol_version='1', description='technical_fixture', requirements_schema_version='relational-v1', display_metadata={}, evidence_id=evidence)
        yield dict(conn=conn, session=session, add=add, inv=inv, doc=doc, evidence=evidence, run=run, other_run=other_run, record=record, field=field, protocol=protocol, now=now)
        session.close(); transaction.rollback()


def rejects(t, table, code, **values):
    with pytest.raises(IntegrityError) as error:
        with t['conn'].begin_nested():
            t['add'](table, **values)
    assert error.value.orig.sqlstate == code


def observation_values(t):
    return dict(parse_run_id=t['run'], source_record_id=t['record'], source_field_id=t['field'], evidence_id=t['evidence'], raw_value='', source_value_kind='text', unit_origin='not_stated', parser_classification='technical_fixture', parser_flags={}, original_representation={})


def test_orm_scoped_joins_json_null_and_empty(technical):
    t=technical; session=t['session']
    oid=t['add']('observation', **observation_values(t))
    obj=session.get(Observation, (t['inv'], oid))
    assert obj.raw_value == ''
    session.refresh(obj, ['source_record_scoped_ref', 'source_field_scoped_ref'])
    assert obj.source_record_scoped_ref.parse_run_id == t['run']
    assert obj.source_field_scoped_ref.parse_run_id == t['run']
    obj.raw_value=None; obj.source_value_kind='empty_cell'; session.flush(); session.expire(obj)
    assert obj.raw_value is None
    inv=session.get(Investigation,t['inv']); assert inv.metadata_json == {'technical':True}
    assert inv.created_at.tzinfo is not None
    inv.description='ORM technical fixture'; session.flush(); session.expire(inv)
    assert inv.description=='ORM technical fixture'


@pytest.mark.parametrize('change,code', [({'parse_run_id':'other_run'},'23503'), ({'investigation_id':'new'},'23503'), ({'raw_value':None},'23514'), ({'source_value_kind':'undefined'},'23514'), ({'parser_flags':[]},'23514')])
def test_observation_invalid_scope_and_shape(technical,change,code):
    t=technical; values=observation_values(t)
    values.update({k: t[v] if v=='other_run' else uuid4() if v=='new' else v for k,v in change.items()})
    if 'investigation_id' in values:
        t['conn'].execute(Base.metadata.tables['investigation'].insert(), dict(id=values['investigation_id'], repository_code='technical_fixture', investigation_code=str(values['investigation_id']), name='OTHER technical fixture', agency='technical_fixture', source_repository_url='urn:technical:fixture', metadata={}, created_at=t['now']))
    rejects(t,'observation',code,**values)


def test_decimal_precision_and_finite_check(technical):
    t=technical
    values=dict(protocol_id=t['protocol'], method='technical_fixture', method_version='1', parameters={}, result_kind='numeric', numeric_value=Decimal('12345678901234567890.123456789012345678901234567890'), unit_status='unknown', producer_ref='technical_fixture', uncertainty={})
    rid=t['add']('analytical_result',**values)
    obj=t['session'].get(AnalyticalResult,(t['inv'],rid))
    assert obj.numeric_value==values['numeric_value']
    for value in ('NaN','Infinity','-Infinity'):
        rejects(t,'analytical_result','23514',**(values|{'numeric_value':Decimal(value)}))
    rejects(t,'analytical_result','23514',**(values|{'text_value':'wrong simultaneous target'}))


def test_revision_join_partial_unique_and_restrict(technical):
    t=technical
    values=dict(subject_kind='investigation',revision=1,evidence_id=t['evidence'],reason='technical_fixture')
    first=t['add']('metadata_revision',**values)
    second=t['add']('metadata_revision',**(values|{'revision':2,'supersedes_id':first}))
    obj=t['session'].scalars(select(MetadataRevision).where(MetadataRevision.investigation_id==t['inv'], MetadataRevision.id==second).options(selectinload(MetadataRevision.supersedes_ref))).one()
    assert obj.supersedes_ref.id==first
    rejects(t,'metadata_revision','23505',**values)
    rejects(t,'metadata_revision','23505',**(values|{'revision':3,'supersedes_id':first}))
    rejects(t,'metadata_revision','23514',**(values|{'revision':0}))
    with pytest.raises(IntegrityError) as error:
        with t['conn'].begin_nested():
            t['conn'].execute(Base.metadata.tables['source_document'].delete().where(Base.metadata.tables['source_document'].c.id==t['doc']))
    assert error.value.orig.sqlstate=='23503'


def test_exclusive_targets_and_entry_shapes(technical):
    t=technical
    rejects(t,'data_quality_issue','23514', issue_type='technical_fixture', detector_method='technical_fixture', detector_version='1', severity='review', description='technical_fixture', evidence_id=t['evidence'])
    rejects(t,'approval_dependency','23514', owner_review_id=uuid4(), entry_kind='scope_observation', role='scope_observation')


def test_snapshot_shapes_and_all_scope_partial_indexes(technical):
    t = technical
    obs = t['add']('observation', **observation_values(t))
    test = t['add']('experimental_test', identity_namespace='technical_fixture', test_identifier='NOT-NASA', identity_evidence_id=t['evidence'], metadata={})
    link = t['add']('test_source_record', experimental_test_id=test, source_record_id=t['record'], evidence_id=t['evidence'], match_method='technical_fixture', method_version='1')
    issue = t['add']('data_quality_issue', observation_id=obs, issue_type='technical_fixture', severity='review', description='technical_fixture', detector_method='technical_fixture', detector_version='1', evidence_id=t['evidence'])
    revision = t['add']('metadata_revision', subject_kind='investigation', revision=1, evidence_id=t['evidence'], reason='technical_fixture')
    def review(number):
        return t['add']('review_event', metadata_revision_id=revision, revision=number, decision='needs_review', rationale='technical_fixture', evidence_id=t['evidence'], reviewer_ref='technical_fixture', reviewed_at=t['now'])
    owner, dependency = review(1), review(2)
    for kind, extra in [('scope_observation', {}), ('scope_link', {'snapshot_link_id':link}), ('scope_issue', {'snapshot_issue_id':issue})]:
        values = dict(owner_review_id=owner, entry_kind=kind, role=kind, snapshot_observation_id=obs) | extra
        t['add']('approval_dependency', **values)
        rejects(t, 'approval_dependency', '23505', **values)
        rejects(t, 'approval_dependency', '23514', **(values | {'dependency_review_id':dependency}))
        if kind != 'scope_observation':
            rejects(t, 'approval_dependency', '23514', **(values | {'snapshot_review_seal_id':uuid4()}))
    decision = dict(owner_review_id=owner, entry_kind='decision', role='technical_fixture', dependency_review_id=dependency)
    t['add']('approval_dependency', **decision)
    rejects(t, 'approval_dependency', '23514', **(decision | {'dependency_review_id':owner}))
    rejects(t, 'approval_dependency', '23514', **(decision | {'snapshot_observation_id':obs}))


def test_required_values_and_protocol_domains(technical):
    t = technical
    rejects(t, 'source_document', '23502', original_filename='technical_fixture')
    values = dict(issue_policy='all_unresolved_review_or_blocking', coverage_policy='every_input_test_segment', protocol_code='technical_fixture_2', protocol_version='1', description='technical_fixture', requirements_schema_version='relational-v1', display_metadata={}, evidence_id=t['evidence'])
    rejects(t, 'analysis_protocol', '23514', **(values | {'issue_policy':'unsupported'}))
    rejects(t, 'analysis_protocol', '23514', **(values | {'coverage_policy':'unsupported'}))
    rejects(t, 'analysis_protocol', '23514', **(values | {'display_metadata':{'invented':True}}))


def test_session_commit_and_new_session_retrieval(schema_databases):
    engine = schema_databases[0]
    identity = uuid4()
    try:
        with Session(engine) as session, session.begin():
            session.add(Investigation(id=identity, repository_code='technical_fixture', investigation_code=str(identity), name='NOT NASA', agency='technical_fixture', source_repository_url='urn:technical:fixture', metadata_json={'nested':{'array':[0, '', None]}}, created_at=datetime.now(timezone.utc)))
        with Session(engine) as session:
            row = session.get(Investigation, identity)
            assert row.metadata_json == {'nested':{'array':[0, '', None]}}
            assert row.description is None
    finally:
        with Session(engine) as session, session.begin():
            row = session.get(Investigation, identity)
            if row is not None:
                session.delete(row)
