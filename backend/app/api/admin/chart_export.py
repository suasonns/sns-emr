from __future__ import annotations

from datetime import date
from uuid import UUID
from typing import Dict, Any, Literal, List, Tuple
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from app.core.db import get_db
from app.dependencies.auth import get_current_user


router = APIRouter(prefix="/admin", tags=["Admin"])


# ---------------------------------------------------------
# Security
# ---------------------------------------------------------

def require_admin(user) -> None:
    role = getattr(user, "role", "").upper()
    # OWNER is the platform/vendor super-user and must never export patient
    # charts. DPCS_ADMINISTRATOR covers an agency principal holding both the
    # DPCS and Administrator titles.
    if role not in {"ADMIN", "SUPER_ADMIN", "DPCS_ADMIN", "DPCS", "ADMINISTRATOR", "DPCS_ADMINISTRATOR"}:
        raise HTTPException(status_code=403, detail="Admin access required")


def _apply_tenant_search_path(db: Session, schema_name: str) -> None:
    if not schema_name:
        raise HTTPException(status_code=400, detail="Tenant schema missing")
    if not schema_name.replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="Invalid tenant schema")
    db.execute(text(f"SET search_path TO {schema_name}, public"))


def _table_exists(db: Session, table_name: str) -> bool:
    return bool(
        db.execute(
            text(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                  AND table_name = :t
                """
            ),
            {"t": table_name},
        ).scalar()
    )


def _safe_query(db: Session, table_name: str, sql: str, params: dict) -> list[dict]:
    if not _table_exists(db, table_name):
        return []
    return [dict(r) for r in db.execute(text(sql), params).mappings()]


# ---------------------------------------------------------
# Request Model (Checklist + Output Options)
# ---------------------------------------------------------

class ChartExportRequest(BaseModel):
    patient_id: UUID
    from_date: date
    to_date: date

    # ✅ Default behavior: PDF
    output_format: Literal["PDF", "ZIP"] = Field(
        "PDF",
        description="PDF (default) or ZIP (optional, only if you want separate PDFs in one download)",
    )

    # ✅ Print vs Download (PDF only can be printed inline)
    output_mode: Literal["PRINT", "DOWNLOAD"] = Field(
        "DOWNLOAD",
        description="PRINT = inline PDF; DOWNLOAD = attachment",
    )

    # ✅ When ZIP is requested, choose separate behavior
    zip_mode: Literal["SEPARATE_ONLY", "SEPARATE_PLUS_COMBINED"] = Field(
        "SEPARATE_ONLY",
        description="If ZIP: either only per-section PDFs, or also include combined PDF",
    )

    # ✅ ALL vs selected (you control exactly what you want)
    all_sections: bool = False

    # Checklist (expand later as section tables exist)
    communication_log: bool = True
    visit_notes: bool = False
    md_visit_notes: bool = False

    include_attachments: bool = False
    add_section_breaks: bool = False

    filename_prefix: str = "patient_chart"


SECTION_ORDER: List[Tuple[str, str]] = [
    ("communication_log", "Communication Log"),
    ("visit_notes", "Visit Notes"),
    ("md_visit_notes", "MD Visit Notes"),
]


def _selected(payload: ChartExportRequest, key: str) -> bool:
    if payload.all_sections:
        return True
    return bool(getattr(payload, key, False))


def _gather_sections(db: Session, payload: ChartExportRequest) -> Dict[str, list[dict]]:
    params = {"pid": payload.patient_id, "from": payload.from_date, "to": payload.to_date}
    sections: Dict[str, list[dict]] = {}

    if _selected(payload, "communication_log"):
        sections["communication_log"] = _safe_query(
            db,
            "communications_logs",
            """
            SELECT *
            FROM communications_logs
            WHERE patient_id = :pid
              AND event_time BETWEEN :from AND :to
            ORDER BY event_time
            """,
            params,
        )

    if _selected(payload, "visit_notes"):
        sections["visit_notes"] = _safe_query(
            db,
            "visits",
            """
            SELECT *
            FROM visits
            WHERE patient_id = :pid
              AND visit_datetime BETWEEN :from AND :to
            ORDER BY visit_datetime
            """,
            params,
        )

    if _selected(payload, "md_visit_notes"):
        sections["md_visit_notes"] = _safe_query(
            db,
            "clinical_notes",
            """
            SELECT *
            FROM clinical_notes
            WHERE patient_id = :pid
              AND created_at BETWEEN :from AND :to
            ORDER BY created_at
            """,
            params,
        )

    # Attachments metadata (optional)
    if payload.include_attachments:
        sections["attachments"] = _safe_query(
            db,
            "communications_log_attachments",
            """
            SELECT *
            FROM communications_log_attachments
            WHERE log_id IN (
                SELECT id
                FROM communications_logs
                WHERE patient_id = :pid
                  AND event_time BETWEEN :from AND :to
            )
            ORDER BY uploaded_at
            """,
            params,
        )

    return sections


def _render_combined_pdf(payload: ChartExportRequest, sections: Dict[str, list[dict]]) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    _, height = LETTER
    y = height - 50

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Patient Chart Export")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Patient ID: {payload.patient_id}")
    y -= 14
    c.drawString(50, y, f"Date Range: {payload.from_date} to {payload.to_date}")
    y -= 22

    def page_break():
        nonlocal y
        c.showPage()
        y = height - 50

    def render_section(title: str, rows: list[dict]):
        nonlocal y
        if payload.add_section_breaks:
            page_break()

        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, title)
        y -= 14

        c.setFont("Helvetica", 9)
        if not rows:
            c.drawString(60, y, "(0 records)")
            y -= 14
            return

        for r in rows:
            line = str(r.get("summary") or r.get("event_type") or r.get("id") or "").replace("\n", " ").strip()
            if len(line) > 110:
                line = line[:110] + "…"
            c.drawString(60, y, f"- {line}")
            y -= 12
            if y < 60:
                page_break()
        y -= 8

    for key, label in SECTION_ORDER:
        if _selected(payload, key):
            render_section(label, sections.get(key, []))

    if payload.include_attachments:
        render_section("Attachments (Metadata)", sections.get("attachments", []))

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


def _render_single_section_pdf(payload: ChartExportRequest, title: str, rows: list[dict]) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    _, height = LETTER
    y = height - 50

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Patient Chart Export (Single Section)")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Patient ID: {payload.patient_id}")
    y -= 14
    c.drawString(50, y, f"Date Range: {payload.from_date} to {payload.to_date}")
    y -= 22

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, title)
    y -= 14

    c.setFont("Helvetica", 9)
    if not rows:
        c.drawString(60, y, "(0 records)")
        y -= 14
    else:
        for r in rows:
            line = str(r.get("summary") or r.get("event_type") or r.get("id") or "").replace("\n", " ").strip()
            if len(line) > 110:
                line = line[:110] + "…"
            c.drawString(60, y, f"- {line}")
            y -= 12
            if y < 60:
                c.showPage()
                y = height - 50

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


@router.post("/chart-export")
def chart_export(
    payload: ChartExportRequest,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    ✅ Default: Print/Download a single PDF (combined).
    ✅ Optional: Download ZIP if explicitly requested.
    """
    require_admin(user)

    schema_name = getattr(request.state, "tenant_schema_name", None)
    if not schema_name:
        raise HTTPException(status_code=400, detail="Tenant context missing")
    _apply_tenant_search_path(db, schema_name)

    sections = _gather_sections(db, payload)

    # Enforce rules: ZIP is optional, never forced.
    if payload.output_format == "ZIP":
        if payload.output_mode != "DOWNLOAD":
            raise HTTPException(status_code=400, detail="ZIP is DOWNLOAD only")
        # Build ZIP containing one PDF per selected section
        zip_buf = BytesIO()
        with ZipFile(zip_buf, "w", compression=ZIP_DEFLATED) as z:
            # Separate PDFs
            for key, label in SECTION_ORDER:
                if _selected(payload, key):
                    pdf_bytes = _render_single_section_pdf(payload, label, sections.get(key, []))
                    z.writestr(f"{payload.filename_prefix}_{key}.pdf", pdf_bytes)

            # Optional: include combined.pdf too
            if payload.zip_mode == "SEPARATE_PLUS_COMBINED":
                combined_pdf = _render_combined_pdf(payload, sections)
                z.writestr(f"{payload.filename_prefix}_combined.pdf", combined_pdf)

        zip_buf.seek(0)
        return StreamingResponse(
            zip_buf,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={payload.filename_prefix}.zip"},
        )

    # Default: PDF (combined)
    pdf_bytes = _render_combined_pdf(payload, sections)
    disposition = "inline" if payload.output_mode == "PRINT" else "attachment"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"{disposition}; filename={payload.filename_prefix}.pdf"},
    )