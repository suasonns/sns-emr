from fastapi import FastAPI
from app.core.audit_middleware import audit_middleware
from app.api import auth, patients
from app.api import visits
from app.api import notes
from app.api import medications
from app.api import chha_pocs
from app.api import idg_meetings
from app.api import f2f, certifications
from app.api import benefits
from app.api import compliance
from app.api import survey
from app.utils.med_normalization import normalize_text, normalize_dose 

app = FastAPI(
    title="SNS Hospice EMR",
    version="0.1.0",
    openapi_tags=[
        {
            "name": "auth",
            "description": "Authentication and access control",
        },
        {
            "name": "patients",
            "description": "Patient management and census",
        },
        {
            "name": "visits",
            "description": "Clinical visits and supervision",
        },
        {
            "name": "notes",
            "description": "Clinical documentation and amendments",
        },
        {
            "name": "medications",
            "description": "Medication reconciliation and orders",
        },
        {
            "name": "CHHA Plan of Care",
            "description": "RN-authored hospice aide plans of care",
        },
        {
            "name": "idg_meetings",
            "description": "Interdisciplinary Group reviews",
        },
        {
            "name": "f2f",
            "description": "Face-to-face encounters",
        },
        {
            "name": "certifications",
            "description": "Physician certifications and recertifications",
        },
        {
            "name": "benefits",
            "description": "Medicare benefit periods and eligibility",
        },
        {
            "name": "compliance",
            "description": "Compliance monitoring and audits",
        },
        {
            "name": "survey",
            "description": "Survey readiness and oversight",
        },
    ],
)

app.middleware("http")(audit_middleware)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(visits.router)
app.include_router(notes.router)
app.include_router(medications.router)
app.include_router(chha_pocs.router)
app.include_router(idg_meetings.router)
app.include_router(f2f.router)
app.include_router(certifications.router)
app.include_router(benefits.router)
app.include_router(compliance.router)
app.include_router(survey.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "SNS EMR Backend",
        "environment": "development"
    }
