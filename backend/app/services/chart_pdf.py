from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime

from app.services.pdf_signature import compute_document_hash


def generate_chart_summary_pdf(
    chart: dict,
    signed_by: str,
    signed_role: str,
) -> BytesIO:

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER

    y = height - 40

    def line(text):
        nonlocal y
        c.drawString(40, y, text)
        y -= 14
        if y < 40:
            c.showPage()
            y = height - 40

    # ---------- Chart Content ----------
    line("SNS Hospice EMR - Patient Chart Summary")
    line("=" * 80)
    line("")

    patient = chart["patient"]
    line(f"Patient Name: {patient['full_name']}")
    line(f"MRN: {patient['mrn']}")
    line(f"DOB: {patient['date_of_birth']}")
    line(f"Primary Diagnosis: {patient['primary_diagnosis']}")
    line(f"Status: {patient['status']}")

    if patient["status"] == "discharged":
        line(f"Discharge Date: {patient['discharge_date']}")
        line(f"Discharge Reason: {patient['discharge_reason']}")

    line("")
    line("Visits")
    line("-" * 40)

    for v in chart["visits"]:
        line(f"{v['visit_datetime']} - {v['visit_type']} ({v['status']})")

    line("")
    line("Clinical Notes")
    line("-" * 40)

    for n in chart["clinical_notes"]:
        line(f"Note {n['note_id']} | Type: {n['note_type']} | Status: {n['status']}")

    line("")
    line("Amendments")
    line("-" * 40)

    for a in chart["amendments"]:
        line(f"{a['created_at']} - {a['reason']}")
        line(f"  {a['content']}")

    line("")
    line("Medications")
    line("-" * 40)

    for m in chart["medications"]:
        line(f"{m['name']} {m['dosage']} {m['route']} {m['frequency']} ({m['status']})")

    # ---------- Signature Page ----------
    c.showPage()
    y = height - 40

    doc_hash = compute_document_hash(chart)
    signed_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    c.drawString(40, y, "Digital Signature")
    y -= 14
    c.drawString(40, y, "-" * 60)
    y -= 14

    c.drawString(40, y, f"Signed by: {signed_by}")
    y -= 14
    c.drawString(40, y, f"Role: {signed_role}")
    y -= 14
    c.drawString(40, y, f"Signed at: {signed_at}")
    y -= 14

    c.drawString(40, y, "Document Integrity Hash (SHA-256):")
    y -= 14

    for i in range(0, len(doc_hash), 64):
        c.drawString(40, y, doc_hash[i:i+64])
        y -= 14

    # ---------- Finalize ----------
    c.save()
    buffer.seek(0)
    return buffer