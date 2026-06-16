import datetime

from app.schemas.adr_audit import AdrReadinessBanner


def test_banner_text_ready():
    # Pure schema test
    b = AdrReadinessBanner(ready=True, banner_text="READY FOR ADR", fail_count=0, top_fail_rules=[], audit={
        "ready": True,
        "findings": [],
        "audit_ran_at": datetime.datetime.utcnow().isoformat(),
        "patient_id": "p1",
        "adr_start": "2026-06-01",
        "adr_end": "2026-06-30",
        "mode": "ADR",
    })
    assert b.ready is True
