"""Regression tests for dynamic migration head verification and database record loading."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.analysis.engine import AUTHENTIC_SHA256
from app.api.workstation import authenticated_records, load_authenticated_records_from_db
from app.core.config import Settings
from app.db.backup import get_authoritative_alembic_head, verify_database_integrity, EXPECTED_ALEMBIC_HEAD
from app.db.check import get_head_revision


def test_authoritative_alembic_head_resolution():
    """Verify authoritative head resolves dynamically without hardcoded constants."""
    head = get_authoritative_alembic_head()
    assert head == "0009_m10_4_document_chunks"
    assert EXPECTED_ALEMBIC_HEAD == head

    settings = Settings(_env_file=None, database_url=None)
    assert get_head_revision(settings) == head


def test_integrity_verifier_mismatched_revision():
    """Verify integrity verifier reports mismatch against authoritative head when version differs."""
    mock_conn = MagicMock()
    # Mock alembic_version returning an obsolete revision
    mock_conn.execute.return_value.scalar_one_or_none.return_value = "0008_m6_security_remediation"
    
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    # Patch inspector and lateral query to isolate revision check
    with patch("app.db.backup.inspect") as mock_inspect:
        mock_insp = MagicMock()
        mock_insp.get_schema_names.return_value = ["public", "flare_sealing", "flare_n1", "flare_n2"]
        mock_insp.get_table_names.return_value = [f"t{i}" for i in range(35)]
        mock_inspect.return_value = mock_insp

        report = verify_database_integrity(mock_engine)
        assert not report["valid"]
        assert any("Alembic revision mismatch" in f and "0009_m10_4_document_chunks" in f for f in report["failures"])


def test_authenticated_records_preserves_tampering_rejection():
    """Verify that a tampered file on disk (ValueError) is not masked and raises 409."""
    mock_conn = MagicMock()
    # Source document exists in DB
    mock_conn.execute.return_value.scalar.return_value = 1

    with patch("app.api.workstation.load_authenticated_records", side_effect=ValueError("Hash mismatch")):
        with pytest.raises(HTTPException) as exc_info:
            authenticated_records(mock_conn)
        assert exc_info.value.status_code == 409
        assert "failed SHA-256" in exc_info.value.detail


def test_authenticated_records_unregistered_rejection():
    """Verify 404 is raised if source document is not present in the database."""
    mock_conn = MagicMock()
    # Source document does not exist in DB
    mock_conn.execute.return_value.scalar.return_value = 0

    with pytest.raises(HTTPException) as exc_info:
        authenticated_records(mock_conn)
    assert exc_info.value.status_code == 404
    assert "not been registered" in exc_info.value.detail


def test_load_authenticated_records_from_db_format():
    """Verify load_authenticated_records_from_db reconstructs exact dictionary format."""
    mock_conn = MagicMock()
    # 1. Parse run info
    run_mapping = {"id": "11111111-1111-1111-1111-111111111111", "record_count": 129, "status": "complete"}
    first_result = MagicMock()
    first_result.mappings.return_value.first.return_value = run_mapping

    # 2. Observation rows (129 rows x 2 dummy headers)
    obs_rows = []
    for r in range(2, 131):
        obs_rows.append((r, "Test #", f"B{r-1}"))
        obs_rows.append((r, "Calibrated  initial O2 % by vol ", "20.9"))
    
    mock_conn.execute.side_effect = [first_result, MagicMock(fetchall=lambda: obs_rows)]

    records = load_authenticated_records_from_db(mock_conn)
    assert len(records) == 129
    assert records[0]["csv_record_number"] == 2
    assert records[0]["data_row_index"] == 1
    assert records[0]["Test #"] == "B1"
    assert records[0]["Calibrated  initial O2 % by vol "] == "20.9"
    assert records[-1]["csv_record_number"] == 130
    assert records[-1]["data_row_index"] == 129
