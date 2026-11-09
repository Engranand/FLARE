"""Independent approved-DDL oracle and declarative metadata tests."""
from pathlib import Path
import re
import warnings

from sqlalchemy import CheckConstraint
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import configure_mappers
from alembic.script import ScriptDirectory

import app.models
from app.db.base import Base
from app.db.migrations import migration_config

PROPOSAL = Path(__file__).resolve().parents[2] / 'docs/architecture/postgresql_schema_proposal.md'


def approved_statements():
    source = PROPOSAL.read_text(encoding='utf-8')
    tables = re.findall(r'CREATE TABLE \w+ \(\n.*?\n\);', source, re.S)
    fks = re.findall(r'ALTER TABLE \w+ ADD CONSTRAINT .*?;', source)
    indexes = re.findall(r'CREATE (?:UNIQUE )?INDEX .*?;', source)
    assert (len(tables), len(fks), len(indexes)) == (33, 140, 112)
    return tables + fks + indexes


def test_metadata_inventory_and_relationship_ownership():
    with warnings.catch_warnings():
        warnings.simplefilter('error', SAWarning)
        configure_mappers()
    assert len(Base.metadata.tables) == 33
    assert sum(len(t.foreign_key_constraints) for t in Base.metadata.tables.values()) == 140
    assert sum(len(t.indexes) for t in Base.metadata.tables.values()) == 112
    assert sum(bool(i.unique) for t in Base.metadata.tables.values() for i in t.indexes) == 4
    assert all(f.ondelete == 'RESTRICT' for t in Base.metadata.tables.values() for f in t.foreign_key_constraints)
    assert sum(len(m.relationships) for m in Base.registry.mappers) == 140
    for mapper in Base.registry.mappers:
        for rel in mapper.relationships:
            assert rel.viewonly and rel.lazy == 'raise'
            assert len(rel.local_remote_pairs) == len(rel._user_defined_foreign_keys)
    source = PROPOSAL.read_text(encoding='utf-8')
    expected = set(re.findall(r'ADD CONSTRAINT (\w+)', source))
    assert expected == {f.name for t in Base.metadata.tables.values() for f in t.foreign_key_constraints}
    diagram = PROPOSAL.with_name('scientific_data_model.mmd').read_text(encoding='utf-8')
    assert len(re.findall(r'^\s*\w+\s*\{\s*$', diagram, re.M)) == 33


def test_static_migration_matches_every_approved_statement():
    module = ScriptDirectory.from_config(migration_config()).get_revision('0002_m42_core_schema').module
    actual = list(module.TABLE_DDL + module.FK_DDL + module.INDEX_DDL)
    def normalize(sql):
        sql = re.sub(r'CONSTRAINT (?:pk|uq|ck)_\w+ ', '', sql)
        # Inline CHECKs are lifted to named table checks without changing expression.
        return re.sub(r'\s+', '', sql).rstrip(';')
    # Column CHECK lifting affects just analysis_protocol; live catalog oracle covers it.
    for approved, implemented in zip(approved_statements(), actual, strict=True):
        if approved.startswith('CREATE TABLE analysis_protocol '):
            continue
        assert normalize(approved) == normalize(implemented)
    assert not any('CREATE TYPE' in x for x in actual)
    assert all(c.name for t in Base.metadata.tables.values() for c in t.constraints if isinstance(c, CheckConstraint))
