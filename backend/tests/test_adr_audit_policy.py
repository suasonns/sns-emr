import datetime
from types import SimpleNamespace

import pytest

from app.services.adr_audit_service import AdrAuditService

class DummyDB:
    def __init__(self, responses=None, fail=False):
        self.responses = responses or {}
        self.fail = fail

    def execute(self, stmt, params=None):
        sql = str(stmt)
        key = (sql.strip(), tuple(sorted((params or {}).items())))
        if self.fail:
            raise Exception("missing table")
        val = self.responses.get(key)
        return SimpleNamespace(scalar=lambda: val)


def test_a2_invalid_period_fails():
    svc = AdrAuditService(DummyDB(responses={}))
    audit = svc.run_full_audit(patient_id="p1", adr_start=datetime.date(2026,6,10), adr_end=datetime.date(2026,6,1))
    assert audit.ready is False
    assert any(f.rule_id == 'A2' for f in audit.findings)


def test_fail_closed_on_missing_schema_records_f1_and_rule():
    svc = AdrAuditService(DummyDB(fail=True))
    audit = svc.run_full_audit(patient_id="p1", adr_start=datetime.date(2026,6,1), adr_end=datetime.date(2026,6,30))
    assert audit.ready is False
    # A1, A3 will likely fail due to missing schema; and F1 must be present
    assert any(f.rule_id == 'F1' for f in audit.findings)
