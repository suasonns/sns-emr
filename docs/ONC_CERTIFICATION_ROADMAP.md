# ONC Certification Roadmap — SNS Hospice Solutions

Status: Tracking document — update phase status as work completes.
This file does not certify anything by itself; it is the running
checklist for ONC Health IT Certification (ONC-ACB, e.g. Drummond
Group / ICSA Labs) so progress is visible at a glance.

See also: `docs/architecture/CERTIFICATION_READINESS_ARCHITECTURE.md`
for the detailed technical-requirements/architecture doc behind
Phase 3, and the current directive governing this work: certification
readiness is required (architecture must not preclude future
certification, and requirements must be documented), but active
certification pursuit is optional/deferred until business conditions
justify the investment — clinical workflow, usability, evidence
attribution, auditability, and clinical accuracy take priority over
chasing certification checkboxes.

**How to use this file:** when a phase is finished, change its status
line from `NOT STARTED` to `IN PROGRESS` to `COMPLETE`, add the date,
and check off the deliverables under it. Do not delete completed
phases or reorder them — this is the audit trail.

---

## When to start each phase — research summary

**Bottom line: certification prep must start BEFORE production go-live,
not after.** Certification is a market-access gateway (providers cannot
use an uncertified EHR for federal programs like Promoting
Interoperability/MIPS), and retrofitting certification requirements
into a live production system is far more costly than building them in
up front. Typical total timeline for a new vendor is **6–12 months
minimum** (3–6 months gap analysis/dev + 3–6 months formal ONC-ACB
testing).

| Phase | Recommended start relative to production go-live |
|---|---|
| 1. Scope | Now / pre-production — this is a planning exercise, zero engineering cost, do it as early as possible |
| 2. Gap Analysis | Pre-production, once core clinical modules (charting, orders, care plan) are functionally stable — do not wait for full feature completeness |
| 3. Development & Remediation | Pre-production — build security, FHIR API, C-CDA, and EHI export as first-class product features, not bolted on after launch |
| 4. Pre-Certification Testing | Pre-production, ideally in a staging environment that mirrors production |
| 5. Certification Body Engagement | Can begin in parallel with late Phase 3/4 — signing the ONC-ACB testing agreement does not require the product to be finished, only close to test-ready |
| 6. Formal ONC Testing | Pre-production strongly preferred; at latest, immediately before general availability — do NOT sell/market as "certified" or use for MIPS/PI-dependent customers before this completes |
| 7. Certification Submission | Marks the transition point — this is what actually unlocks production use for programs requiring certified technology |
| 8. Post-Certification Maintenance | Ongoing, only after go-live — this is the only phase that is inherently post-production by definition |

**Practical implication for SNS:** Phases 1–6 should be treated as
pre-production/pre-GA work streams that run alongside (not after)
tenant platform development. Phase 7 is the gate that allows SNS to be
marketed/sold as ONC-certified. Phase 8 is the only ongoing
post-production obligation.

---

## Phase 1 — Determine Certification Scope

**Status:** NOT STARTED
**Target window:** Pre-production
**Completed on:** _(date)_

Deliverable: A finalized list of ONC criteria SNS will certify under.

- [ ] §170.315(d) — Security (audit logs, access control, integrity, authentication)
- [ ] §170.315(g) — API (FHIR R4, patient access, clinician access)
- [ ] §170.315(h) — EHI Export (full patient record export)
- [ ] §170.315(a) — Clinical documentation
- [ ] §170.315(b) — Interoperability (CCD/C-CDA)
- [ ] §170.315(f) — Care plan
- [ ] §170.315(e) — Patient education (optional)
- [ ] Finalized scope document signed off

---

## Phase 2 — Gap Analysis

**Status:** NOT STARTED
**Target window:** Pre-production
**Completed on:** _(date)_

- [ ] Data model completeness reviewed (FHIR resources, C-CDA sections)
- [ ] Security controls evaluated
- [ ] Audit logging evaluated
- [ ] API endpoints evaluated
- [ ] Export capabilities evaluated
- [ ] Clinical documentation structure evaluated
- [ ] Interoperability workflows evaluated (referrals, transitions of care)
- [ ] Gap analysis report produced
- [ ] Development roadmap produced
- [ ] Compliance checklist produced

---

## Phase 3 — Development & Remediation

**Status:** IN PROGRESS (security sub-items already complete pre-existing; FHIR/C-CDA/EHI export deferred — see `CERTIFICATION_READINESS_ARCHITECTURE.md`)
**Target window:** Pre-production
**Completed on:** _(date)_

**Security**
- [x] Role-based access control — `backend/app/core/roles.py`, `role_guards.py`, `permissions.py` (pre-existing, tested)
- [ ] Multi-factor authentication
- [x] Audit log generation — `backend/app/models/audit_log.py`, `audit_log_service.py` (pre-existing, tested); server-side certified-format export still NOT built (current export is client-side CSV of the UI table only)
- [x] Data integrity checks (hashing) — `backend/app/core/crypto.py`, `security.py` (pre-existing)

**FHIR API**
- [ ] Patient
- [ ] Practitioner
- [ ] Encounter
- [ ] Condition
- [ ] CarePlan
- [ ] Observation
- [ ] DocumentReference
- [ ] Binary (for C-CDA)

**Interoperability**
- [ ] Generate C-CDA documents
- [ ] Accept C-CDA documents
- [ ] Reconciliation workflows

**EHI Export**
- [ ] Full patient record export
- [ ] Machine-readable format
- [ ] Human-readable format

Deliverables:
- [ ] Updated EMR features
- [ ] API documentation
- [ ] Security documentation
- [ ] Data model documentation

---

## Phase 4 — Pre-Certification Testing

**Status:** NOT STARTED
**Target window:** Pre-production (staging environment mirroring production)
**Completed on:** _(date)_

- [ ] Security test suite run
- [ ] FHIR API test suite run
- [ ] C-CDA validation run
- [ ] EHI export validation run
- [ ] Clinical workflow validation run
- [ ] Test results documented
- [ ] Remediation fixes applied
- [ ] Final readiness report produced

---

## Phase 5 — Certification Body Engagement

**Status:** NOT STARTED
**Target window:** Can start in parallel with late Phase 3/4, pre-production
**Completed on:** _(date)_

- [ ] ONC-ACB selected (e.g. Drummond Group, ICSA Labs)
- [ ] Testing agreement signed
- [ ] Certification session scheduled

---

## Phase 6 — Formal ONC Testing

**Status:** NOT STARTED
**Target window:** Pre-production strongly preferred; at latest, immediately before general availability
**Completed on:** _(date)_

Demonstrated live with an ONC proctor:
- [ ] Security
- [ ] FHIR API
- [ ] C-CDA generation
- [ ] C-CDA ingestion
- [ ] EHI export
- [ ] Clinical documentation
- [ ] Care plan workflows

Deliverables:
- [ ] Passing test results
- [ ] ONC certification package

---

## Phase 7 — Certification Submission

**Status:** NOT STARTED
**Target window:** Gate to production use / marketing as "ONC-certified" — do not use for MIPS/PI-dependent customers before this completes
**Completed on:** _(date)_

- [ ] Submitted to ONC CHPL
- [ ] Submitted to CMS programs (if applicable)
- [ ] Official ONC Certification ID received
- [ ] Public CHPL listing confirmed
- [ ] Certification seal available for marketing

---

## Phase 8 — Post-Certification Maintenance

**Status:** NOT STARTED (only begins after Phase 7 is complete and product is live)
**Target window:** Ongoing, post-production
**Completed on:** N/A — ongoing

- [ ] Annual surveillance scheduled
- [ ] API uptime reporting process in place
- [ ] EHI export compliance monitoring in place
- [ ] Version update process defined
- [ ] Security patch documentation process defined

---

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Initial roadmap created; all phases NOT STARTED |
