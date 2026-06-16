# ADR Audit + Export + Readiness Banner (V2)

This patch aligns service placement with SNS EMR structure:
- Services live in `backend/app/services/`
- API routers live in `backend/app/api/`

## What you get
- ADR_AUDIT_RULES.md under `backend/docs/compliance/`
- Candidate-based schema binding via `app/services/adr_schema_map.py`
- ADR audit engine `app/services/adr_audit_service.py` (full audit, fail closed)
- PDF renderers in `app/services/adr_pdf_utils.py`
- ADR export endpoint: `POST /chart/export/adr`
- Readiness banner endpoint: `GET /patients/{patient_id}/adr-readiness?adr_start=YYYY-MM-DD&adr_end=YYYY-MM-DD&mode=ADR`

## IMPORTANT
- Candidate schema binding is a best-effort auto-bind.
- Replace candidates with your confirmed table/column names when available.
- Manual Print Chart is not touched.
