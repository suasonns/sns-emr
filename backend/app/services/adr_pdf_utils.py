"""PDF utilities for ADR/TPE export.

This module intentionally avoids business logic; it renders provided content.
"""

from __future__ import annotations

from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from app.schemas.adr_audit import AdrAuditResult


def render_deficiency_report(audit: AdrAuditResult) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    width, height = LETTER

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "ADR Readiness Report — Chart Not Ready for Submission")
    y -= 22

    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Patient ID: {audit.patient_id}")
    y -= 14
    c.drawString(50, y, f"Period: {audit.adr_start} to {audit.adr_end}")
    y -= 14
    c.drawString(50, y, f"Audit Ran At (UTC): {audit.audit_ran_at.isoformat()}")
    y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Deficiencies (FAIL)")
    y -= 16

    c.setFont("Helvetica", 9)
    for f in audit.findings:
        lines = [
            f"{f.rule_id} — {f.summary}",
            f"Why: {f.why_it_blocks}",
            f"Guidance: {f.guidance}",
        ]
        if f.location:
            lines.insert(1, f"Where: {f.location}")
        for line in lines:
            if y < 60:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 9)
            c.drawString(55, y, line[:120])
            y -= 12
        y -= 6

    c.showPage()
    c.save()
    return buf.getvalue()


def render_adr_cover_sheet(audit: AdrAuditResult, agency_name: str = "", ccn: str = "") -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    width, height = LETTER

    y = height - 60
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "ADR Packet Cover Sheet")
    y -= 24

    c.setFont("Helvetica", 10)
    if agency_name:
        c.drawString(50, y, f"Agency: {agency_name}")
        y -= 14
    if ccn:
        c.drawString(50, y, f"CCN: {ccn}")
        y -= 14

    c.drawString(50, y, f"Patient ID: {audit.patient_id}")
    y -= 14
    c.drawString(50, y, f"ADR Billing Period: {audit.adr_start} to {audit.adr_end}")
    y -= 14
    c.drawString(50, y, f"Generated On (UTC): {datetime.utcnow().isoformat()}")
    y -= 20

    c.setFont("Helvetica", 10)
    c.drawString(50, y, "System ADR audit completed. Chart is ready for ADR submission.")
    y -= 16

    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Statement of scope:")
    y -= 12
    c.drawString(55, y, "This packet contains eligibility documentation from SOC through end of ADR period")
    y -= 12
    c.drawString(55, y, "and all clinical and supporting documentation created during the ADR billing period,")
    y -= 12
    c.drawString(55, y, "without duplication.")

    c.showPage()
    c.save()
    return buf.getvalue()
