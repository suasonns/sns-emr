from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# ---------------------------------------------------------
# NAMING CONVENTION
# ---------------------------------------------------------

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


# ---------------------------------------------------------
# BASE
# ---------------------------------------------------------

class Base(DeclarativeBase):
    metadata = metadata


# ---------------------------------------------------------
# 🔥 CRITICAL: LOAD ALL MODELS
# ---------------------------------------------------------

# CORE PATIENT DOMAIN
import app.models.patient
import app.models.patient_assignment
import app.models.patient_diagnosis
import app.models.task
import app.models.benefit_period

# CLINICAL + SUPPORT
import app.models.clinical_note
import app.models.external_substance
import app.models.service_coverage_decision

# FORM ENGINE
import app.models.form_registry_model
import app.models.form_module
import app.models.form_package_module
import app.models.form

# OPTIONAL BUT SAFE
import app.models.patient_payer
import app.models.patient_insurance
import app.models.physician
import app.models.medication
import app.models.drug_alias
import app.models.patient_allergy
import app.models.patient_order
import app.models.order_template
import app.models.fax_log
import app.models.physician_order
import app.models.scica_assessment
import app.models.certification
import app.models.f2f_encounter
