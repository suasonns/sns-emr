# services/idg_pdf.py
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime


def generate_idg_report_pdf(records: list) -> BytesIO:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)

    width, height = LETTER
    margin_x = 40
    margin_y = 40

    y = height - margin_y

    # -----------------------------------------------------
    # FONT SETUP
    # -----------------------------------------------------
    c.setFont("Helvetica", 10)

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------
    def draw_header():
        nonlocal y
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin_x, y, "SNS Hospice EMR – IDG Compliance Report")

        y -= 16
        c.setFont("Helvetica", 9)
        c.drawString(
            margin_x,
            y,
            f"Generated on: {datetime.now().strftime('%m/%d/%Y %H:%M')}",
        )

        y -= 18
        c.line(margin_x, y, width - margin_x, y)
        y -= 12

    # -----------------------------------------------------
    # SAFE TEXT WRAPPER
    # -----------------------------------------------------
    def wrap_text(text: str, max_chars: int = 80):
        if not text:
            return ["-"]

        text = str(text)

        return [
            text[i:i + max_chars]
            for i in range(0, len(text), max_chars)
        ]

    # -----------------------------------------------------
    # LINE WRITER WITH PAGE MANAGEMENT
    # -----------------------------------------------------
    def draw_line(text: str):
        nonlocal y

        lines = wrap_text(text)

        for line in lines:
            if y < margin_y:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = height - margin_y
                draw_header()

            c.drawString(margin_x, y, line)
            y -= 14

    # -----------------------------------------------------
    # INITIAL HEADER
    # -----------------------------------------------------
    draw_header()

    # -----------------------------------------------------
    # TABLE HEADER
    # -----------------------------------------------------
    c.setFont("Helvetica-Bold", 10)
    draw_line("Patient Name | Last IDG Review")
    draw_line("-" * 90)

    c.setFont("Helvetica", 10)

    # -----------------------------------------------------
    # DATA ROWS
    # -----------------------------------------------------
    for r in records:
        patient_name = r.get("patient_name", "UNKNOWN")
        last_review = r.get("last_idg_review")

        if last_review:
            try:
                last_review = str(last_review)
            except Exception:
                last_review = "INVALID DATE"
        else:
            last_review = "N/A"

        row = f"{patient_name} | {last_review}"

        draw_line(row)

    # -----------------------------------------------------
    # FINALIZE
    # -----------------------------------------------------
    c.save()
    buffer.seek(0)

    return buffer

