
# SNS Hospice EMR — ICA Architecture & Implementation Map (CMS‑Governed)

**Version:** 2.0  
**Status:** Canonical / Survey‑Defensible  
**Scope:** RN Initial Comprehensive Assessment (ICA) with Integrated CMS Modules (HOPE + Future)

---

## 0. Governing Philosophy (LOCKED)

1. **CMS is the governing authority**. Accrediting bodies are deeming entities.
2. **Surveyors are human and inconsistent** — the system must eliminate interpretation.
3. **Posted Date is the single source of clinical truth**.
4. **One ICA screen for nurses** — no additional pages for CMS add‑ons.
5. **CMS rules must be configuration‑driven and versioned**.

---

## 1. ICA Architectural Model (Single Screen, Modular Engine)

```
Integrated ICA (Single RN Screen)
│
├── A. RN Clinical Core (Stable)
├── B. CMS Instrument Sections (Dynamic)
│     ├── HOPE (Current)
│     └── Future CMS Module (Placeholder)
├── C. Discipline Integration & Discrepancy Tracking
└── D. Posting, Signatures, Audit
```

---

## 2. A. RN Clinical Core (STABLE – DO NOT HARD‑CODE CMS)

This section represents **true nursing judgment** and rarely changes.

### Contents:
- Physical assessment
- Symptom burden
- Skin / wounds
- Safety & fall risk
- Pain assessment
- Nursing problems & interventions
- Education provided
- Patient / caregiver response

**Table:** `rn_assessment_core`
- `posted_date` ✅ **SOURCE OF TRUTH**
- `cms_rules_version_used`
- `form_definition_version_used`

---

## 3. B. CMS Instrument Sections (INTEGRATED, NOT SEPARATE)

### Key Rule
CMS instruments **appear inside the ICA screen** but are **stored as modules**.

### Current Module: HOPE
- Rendered inline in ICA
- Required based on CMS rules
- Stored as JSON

### Future CMS Modules
- Placeholder section always exists
- Activated by CMS rules only
- No new ICA page ever added

**Table:** `assessment_modules`
- `parent_assessment_id`
- `instrument_type` (HOPE, FUTURE_X)
- `instrument_version`
- `data_json`
- `posted_date`

---

## 4. CMS Rules Engine (CRITICAL)

### Rules Location
```
/backend/app/compliance/cms/
├── v2026_01.json
├── v2026_07.json
└── active_rules.json
```

### Rules Control:
- Which CMS modules appear
- Required fields
- Signature enforcement
- Timing windows

**Rules are NEVER fetched live from CMS websites.**
CMS websites are reference only.

---

## 5. ICA Posting & Signatures (STRICT POLICY)

### Posting Action (RN)
When RN clicks **POST ICA**:

✅ Sets:
- `posted_date` (clinical truth)
- `cms_rules_version_used`

✅ Locks:
- Required CMS sections
- Same‑day signature window

---

## 6. Signature Rules (CMS‑Anchored, Survey‑Safe)

### Mandatory Same‑Day Policy (Agency‑Defined)
- All required disciplines must sign **same calendar day as posted_date**
- Signature timestamps retained for audit only

### Required Signers
- RN (ICA author)
- MD / Medical Director (attendance + attestation)
- MSW / SC / LVN as applicable

### Exception Workflow
Late signature requires:
- Documented reason
- Supervisor approval
- Audit trail

---

## 7. IDG Integration & Signatures (INCLUDED)

### IDG Posted Date Rule
- IDG `posted_date` is the clinical anchor
- Attendance ≠ concurrence
- Attestation required

### Dual Oversight Model
- **Physician Oversight** (MD only)
- **Clinical Oversight Review** (RN facilitator)

### Same‑Day Enforcement
- IDG signatures required same day as IDG posted_date

---

## 8. Discrepancy Tracking (FIRST IDG GATE)

Discrepancies across:
- RN vs MSW
- RN vs SC
- CMS module vs clinical core

✅ Must be resolved before first IDG finalization

---

## 9. Why This Survives CMS Changes

When CMS adds new nursing documentation:

✅ Add new CMS rules JSON
✅ Add new module schema
✅ ICA screen auto‑renders new section

❌ No DB refactor
❌ No ICA redesign

---

## 10. Survey Defense Script (SYSTEM‑READY)

> “This ICA was posted under CMS rules version v2026_01. All required CMS instruments and signatures were completed the same day. Later CMS changes do not apply retroactively.”

---

**This document is canonical and governs ICA implementation moving forward.**
