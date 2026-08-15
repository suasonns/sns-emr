from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List

from app.services.pdf_signature import compute_document_hash


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _build_patient_name(patient: Dict[str, Any]) -> str:
    return " ".join(
        filter(
            None,
            [
                patient.get("first_name"),
                patient.get("middle_name"),
                patient.get("last_name"),
            ],
        )
    ) or "UNKNOWN PATIENT"


def generate_chart_summary_pdf(
    chart: Dict[str, Any],
    signed_by: str,
    signed_role: str,
) -> BytesIO:

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER

    y = height - 40

    # --------------------------------------------------
    # ✅ Safe line writer
    # --------------------------------------------------
    def line(text: str):
        nonlocal y
        c.drawString(40, y, text)
        y -= 14
        if y < 40:
            c.showPage()
            y = height - 40

    # --------------------------------------------------
    # ✅ Extract data safely
    # --------------------------------------------------
    patient = chart.get("patient", {})
    visits: List[Dict[str, Any]] = chart.get("visits", [])
    notes: List[Dict[str, Any]] = chart.get("clinical_notes", [])
    amendments: List[Dict[str, Any]] = chart.get("amendments", [])
    medications: List[Dict[str, Any]] = chart.get("medications", [])

    patient_name = _build_patient_name(patient)

    # --------------------------------------------------
    # ✅ Chart Header
    # --------------------------------------------------
    line("SNS Hospice EMR - Patient Chart Summary")
    line("=" * 80)
    line("")

    line(f"Patient Name: {_safe_str(patient_name)}")
    line(f"MRN: {_safe_str(patient.get('mrn'))}")
    line(f"DOB: {_safe_str(patient.get('date_of_birth'))}")
    line(f"Primary Diagnosis: {_safe_str(patient.get('primary_diagnosis'))}")
    line(f"Status: {_safe_str(patient.get('status'))}")

    if patient.get("status") == "DISCHARGED":
        line(f"Discharge Date: {_safe_str(patient.get('discharge_date'))}")
        line(f"Discharge Reason: {_safe_str(patient.get('discharge_reason'))}")

    # --------------------------------------------------
    # ✅ Visits
    # --------------------------------------------------
    line("")
    line("Visits")
    line("-" * 40)

    if not visits:
        line("No visits recorded")
    else:
        for v in visits:
            line(
                f"{_safe_str(v.get('visit_datetime'))} - "
                f"{_safe_str(v.get('visit_type'))} "
                f"({_safe_str(v.get('status'))})"
            )

    # --------------------------------------------------
    # ✅ Clinical Notes
    # --------------------------------------------------
    line("")
    line("Clinical Notes")
    line("-" * 40)

    if not notes:
        line("No clinical notes")
    else:
        for n in notes:
            line(
                f"Note {_safe_str(n.get('note_id'))} | "
                f"Type: {_safe_str(n.get('note_type'))} | "
                f"Status: {_safe_str(n.get('status'))}"
            )

    # --------------------------------------------------
    # ✅ Amendments
    # --------------------------------------------------
    line("")
    line("Amendments")
    line("-" * 40)

    if not amendments:
        line("No amendments")
    else:
        for a in amendments:
            line(f"{_safe_str(a.get('created_at'))} - {_safe_str(a.get('reason'))}")
            line(f"  {_safe_str(a.get('content'))}")

    # --------------------------------------------------
    # ✅ Medications
    # --------------------------------------------------
    line("")
    line("Medications")
    line("-" * 40)

    if not medications:
        line("No medications")
    else:
        for m in medications:
            line(
                f"{_safe_str(m.get('name'))} "
                f"{_safe_str(m.get('dosage'))} "
                f"{_safe_str(m.get('route'))} "
                f"{_safe_str(m.get('frequency'))} "
                f"({_safe_str(m.get('status'))})"
            )

    # --------------------------------------------------
    # ✅ Signature Page
    # --------------------------------------------------
    c.showPage()
    y = height - 40

    doc_hash = compute_document_hash(chart)
    signed_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    c.drawString(40, y, "Digital Signature")
    y -= 14
    c.drawString(40, y, "-" * 60)
    y -= 14

    c.drawString(40, y, f"Signed by: {_safe_str(signed_by)}")
    y -= 14
    c.drawString(40, y, f"Role: {_safe_str(signed_role)}")
    y -= 14
    c.drawString(40, y, f"Signed at: {_safe_str(signed_at)}")
    y -= 14

    c.drawString(40, y, "Document Integrity Hash (SHA-256):")
    y -= 14

    for i in range(0, len(doc_hash), 64):
        c.drawString(40, y, doc_hash[i:i + 64])
        y -= 14

    # --------------------------------------------------
    # ✅ Finalize
    # --------------------------------------------------
    c.save()
    buffer.seek(0)

    return buffer