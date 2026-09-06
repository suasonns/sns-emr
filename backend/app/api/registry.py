from fastapi import FastAPI

# SYSTEM / AUTH ROUTES
from app.api import auth, auth_whoami

# OWNER / SUPPORT
from app.api.support_reference import router as support_reference_router
from app.api.owner_admin import router as owner_admin_router
from app.api.owner_billing_licensing import router as owner_billing_licensing_router

# ADMIN
from app.api.admin.chart_export import router as admin_chart_export_router

# COMMUNICATIONS LOG
from app.api.communications_log.router import router as communications_log_router
from app.api.routes import forms
from app.api.notifications import router as notifications_router

# CORE TENANT ROUTES
from app.api import (
    patients,
    visits,
    notes,
    medications,
    chha_pocs,
    f2f,
    certifications,
    benefits,
    compliance,
    survey,
    documents,
    admin_reminders,
    admission_authorization,
    med_reconciliation,
    physicians,
    staff,
    vendors,
    visit_recordings,
)
from app.api.agency_profile import router as agency_profile_router
from app.api.hospice_cap import router as hospice_cap_router
from app.api.noe import router as noe_router
from app.api.election_addendum import router as election_addendum_router

# PHYSICIAN IDENTITY MAPPING / SHARED PATIENT-CONTACT-DECISION-MAKER RECORDS
from app.api.physician_identity import router as physician_identity_router
from app.api.patient_code_status import router as patient_code_status_router
from app.api.patient_contacts import router as patient_contacts_router
from app.api.patient_physicians import router as patient_physicians_router

# DOMAIN / WORKFLOW
from app.api.eligibility.routes import router as eligibility_router
from app.api.rules.routes import router as rules_router
from app.api.regulatory.reports import router as regulatory_router
from app.api.safety_assessments import router as safety_assessments_router
from app.api.routes.plan_of_care import router as poc_router
from app.api.routes.rnica_poc import router as rnica_poc_router
from app.api.routes.admission_action_center import router as admission_action_center_router
from app.api.patient_allergies import router as patient_allergies_router
from app.api.patient_issues import router as patient_issues_router
from app.api.referrals import router as referrals_router
from app.api.bereavement import router as bereavement_router
from app.api.bereavement_poc import router as bereavement_poc_router
from app.api.post_death_bereavement import router as post_death_bereavement_router
from app.api.bereavement_letters import router as bereavement_letters_router
from app.api.bereavement_support import router as bereavement_support_router

# ENGINE LAYER
from app.api.clinical_notes.router import router as clinical_notes_router
from app.api.idg.router import router as idg_router
from app.api.dashboard.router import router as dashboard_router
from app.api.audit_dashboard import router as audit_dashboard_router
from app.api.clinical_translation import router as clinical_translation_router
from app.api.patient_charts import router as patient_charts_router

# ✅ NEW TASK ROUTER (THIS IS THE FIX)
from app.api.tasks import router as tasks_router

# TASK ENGINE (existing)
from app.api.task_completion import router as task_completion_router
from app.api.task_scheduling import router as task_scheduling_router

# WORKFLOW
from app.api.patient_assignments import router as patient_assignments_router
from app.api.supervisory_schedule import router as supervisory_schedule_router
from app.api.soc_orders import router as soc_orders_router
from app.api.admission import router as admission_router
from app.api.admissions import router as admissions_router
from app.api.print import router as print_router
from app.api.auth_reauth import router as auth_reauth_router
from app.api.internal_superuser import router as internal_superuser_router
from app.api.admission_diagnosis import router as admission_diagnosis_router
from app.api.icd10 import router as icd10_router

# ORDERS HUB (order templates / generic patient orders / fax / lab catalog)
from app.api.order_templates import router as order_templates_router
from app.api.patient_orders import router as patient_orders_router
from app.api.fax import router as fax_router
from app.api.lab_catalog import router as lab_catalog_router

# PHYSICIAN ORDERS (MD-approval-gated compliant order workflow)
from app.api.physician_orders import router as physician_orders_router

# EXTERNAL
from app.api.coverage import router as coverage_router
from app.api.external_substances import router as external_substances_router

# BILLING
from app.billing.api.billing_queue_router import router as billing_queue_router
from app.billing.api.tenant_router import router as tenant_router
from app.billing.api.claim_status_router import router as claim_status_router
from app.billing.api.audit_router import router as audit_router
from app.billing.api.billing_router import router as billing_router  # legacy last
from app.api.billing_835 import router as billing_835_router
from app.billing.api.eligibility_check_router import router as eligibility_check_router
from app.billing.api.visits_notes_router import router as visits_notes_router
from app.billing.api.poc_certification_router import router as poc_certification_router
from app.billing.api.noe_tracking_router import router as noe_tracking_router
from app.billing.api.claims_router import router as claims_router
from app.billing.api.denials_router import router as denials_router
from app.billing.api.payment_posting_router import router as payment_posting_router
from app.billing.api.aging_report_router import router as aging_report_router
from app.billing.api.credit_balance_router import router as credit_balance_router

# ADR / TPE (OPTIONAL)
try:
    from app.api.adr_exports import router as adr_exports_router
    from app.api.adr_readiness import router as adr_readiness_router
except Exception:  # pragma: no cover
    adr_exports_router = None
    adr_readiness_router = None


def register_routers(app: FastAPI) -> None:
    """
    Canonical router registry.
    """

    # =====================================================
    # Auth / system
    # =====================================================
    app.include_router(auth.router)
    app.include_router(auth_whoami.router)

    # =====================================================
    # Owner / support
    # =====================================================
    app.include_router(support_reference_router)
    app.include_router(owner_admin_router)
    app.include_router(owner_billing_licensing_router)

    # =====================================================
    # Admin
    # =====================================================
    app.include_router(admin_chart_export_router)

    # =====================================================
    # Optional ADR/TPE
    # =====================================================
    if adr_exports_router is not None:
        app.include_router(adr_exports_router)

    if adr_readiness_router is not None:
        app.include_router(adr_readiness_router)

    # =====================================================
    # Tenant + application routes
    # =====================================================
    tenant_routes = [
        patients.router,
        visits.router,
        visit_recordings.router,
        forms.router,
        notes.router,
        communications_log_router,
        notifications_router,
        clinical_notes_router,
        idg_router,
        dashboard_router,
        clinical_translation_router,  # ✅ ADD THIS

        poc_router,
        rnica_poc_router,
        admission_action_center_router,
        patient_charts_router,
        patient_issues_router,
        referrals_router,
        bereavement_router,
        bereavement_poc_router,
        post_death_bereavement_router,
        bereavement_letters_router,
        bereavement_support_router,

        # ✅ ADD YOUR TASKS ROUTER HERE (CRITICAL)
        tasks_router,

        audit_dashboard_router,
        medications.router,
        patient_allergies_router,
        chha_pocs.router,
        f2f.router,
        certifications.router,
        benefits.router,
        compliance.router,
        survey.router,
        documents.router,
        admin_reminders.router,
        admission_authorization.router,
        med_reconciliation.router,
        physicians.router,
        staff.router,
        agency_profile_router,
        hospice_cap_router,
        noe_router,
        election_addendum_router,
        vendors.router,
        soc_orders_router,
        admission_router,
        admissions_router,
        print_router,
        auth_reauth_router,
        internal_superuser_router,
        admission_diagnosis_router,
        icd10_router,

        # Existing task system
        task_completion_router,
        task_scheduling_router,

        patient_assignments_router,
        supervisory_schedule_router,
        eligibility_router,
        rules_router,
        regulatory_router,
        safety_assessments_router,
        coverage_router,
        external_substances_router,
        billing_queue_router,
        tenant_router,
        claim_status_router,
        audit_router,
        billing_router,
        billing_835_router,
        eligibility_check_router,
        visits_notes_router,
        poc_certification_router,
        noe_tracking_router,
        claims_router,
        denials_router,
        payment_posting_router,
        aging_report_router,
        credit_balance_router,
        patient_orders_router,
        fax_router,
        lab_catalog_router,
        physician_orders_router,

        # Physician Identity Mapping / shared patient contact-decision-maker records
        physician_identity_router,
        patient_code_status_router,
        patient_contacts_router,
        patient_physicians_router,
    ]

    for router in tenant_routes:
        app.include_router(router)