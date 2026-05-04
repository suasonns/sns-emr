from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import date

def generate_idg_report_pdf(records: list) -> BytesIO:
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

    line("SNS Hospice EMR – IDG Compliance Report")
    line(f"Generated on: {date.today()}")
    line("=" * 70)
    line("")

    for r in records:
        line(f"Patient: {r['patient_name']}")
        line(f"Last IDG Review: {r['last_idg_review']}")
        line("-" * 40)

    c.save()
    buffer.seek(0)
    return buffer
