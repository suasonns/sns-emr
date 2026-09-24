# Authority Applicability Register (Phase 2)

**Document Status:** AUDIT BASELINE / REMEDIATION REQUIRED — NOT_VERIFIED rows remain unresolved. See `RNICA_PHASE3_REMEDIATION_REGISTER.md` (P3-012), Phase H.

**Purpose:** every place where this pass's findings touch on regulatory or
compliance framing, recorded with the authority that *would* have to be
consulted, and an explicit, uniform verification status.

## Environment limitation (applies to every row without exception)

This pass had **no access to external regulatory sources**. There is no
`web_search` or `web_fetch` capability in this environment, and no copy of
the CMS HOPE technical specifications, the CMS Hospice Quality Reporting
Program (HQRP) manual, the iQIES submission specifications, the Medicare
Conditions of Participation for hospice, or California hospice licensing
regulations exists in this repository. Accordingly:

- **Every row below is `NOT VERIFIED — external regulatory source not
  accessible this pass`.**
- Only the repository's own code, configuration, comments, and tests were
  verified. Repository comments that *describe* CMS rules were treated as
  claims made by the code, not as evidence about CMS.
- **No citation number, publication date, version, or "currently
  effective" claim for any external source appears anywhere in this pass's
  documents.** Where the repository itself names a code or rule, that is
  reported as "the repository asserts X", never as "CMS requires X".
- Every row requires **human compliance/legal review** before any of it is
  treated as a regulatory obligation.

---

| # | Claim touched by this pass | Repository evidence for the claim | Authority that would have to be cited to verify it | Jurisdiction | Verification status |
|---|---|---|---|---|---|
| 1 | The listed A-section codes (A0050…A2115) are the correct HOPE administrative items | `form_registry.py:341-362` | CMS HOPE item set / technical specifications | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 2 | A0215 site-of-service code values `01`-`09`, `99` are the official CMS set | `hopeReportMapper.js:59-70` (comment says "official CMS codes") | CMS HOPE item set | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 3 | A1805 admitted-from values `01`-`11`, `99` are official | `hopeReportMapper.js:77-89` | CMS HOPE item set | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 4 | A1905 living-arrangement values `1`-`5` are official | `hopeReportMapper.js:95-101` | CMS HOPE item set | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 5 | A1910 availability-of-assistance codes `1`-`5` are official (no `officialCodeLookup` is used for this item) | `hopeReportMapper.js:182-190` | CMS HOPE item set | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 6 | A1005/A1010 race and ethnicity response sets are complete | `RNICA.jsx:7992-7995` (6 race, 3 ethnicity options) | CMS HOPE item set (and any OMB race/ethnicity standard it adopts) | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 7 | A1400 payer-source letters A-Y are the official multi-select set | `hopeReportMapper.js:138-150` | CMS HOPE item set | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 8 | F2000/F2100/F2200/F3000 "asked" statuses `0`/`1`/`2` are the official response set | `hopeReportMapper.js:307-311` | CMS HOPE item set | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 9 | I0010 principal-diagnosis categories `01`-`09`, `99` are official | `hopeReportMapper.js:124-137` | CMS HOPE item set | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 10 | The comorbidity code list I0100…I6202 + I8005 is the official Section I set | `hopeReportMapper.js:440-453`; `RNICA.jsx:2499-2512` | CMS HOPE item set | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 11 | "Do not check a category already coded as the Principal Diagnosis, except a second distinct cancer" | `RNICA.jsx:2598-2601` (UI guidance text), carve-out logic `:2624-2626` | CMS HOPE guidance manual | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 12 | J0900 pain-screening sub-items A/C/D and their value sets | `hopeReportMapper.js:200-219` | CMS HOPE item set | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 13 | J0915 neuropathic pain is a distinct item from J0900 | `hopeReportMapper.js:273-277` | CMS HOPE item set | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 14 | J2051 is reported per-symptom (A-H) rather than as one code | `form_registry.py:386-394` vs `hopeReportMapper.js:617` | CMS HOPE item set | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 15 | **SFV is required within 2 calendar days of a moderate/severe J2051 symptom** | `hope_phase_b_engine.py:356`; `hopeReportMapper.js:421, 439-440` | CMS HOPE guidance / HQRP requirements | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 16 | **SFV must be an in-person visit, by RN or LPN/LVN, separate from the triggering visit** | `hope_phase_b_engine.py:417-426` | CMS HOPE guidance | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 17 | **HUV1 falls on days 6-15 and HUV2 on days 16-30 after election, RN only** | `hope_phase_b_engine.py:158-181, 259-260` | CMS HOPE guidance | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 18 | Which HOPE items apply at Admission vs HUV vs Discharge | `form_registry.py:420-441`; exporter filters `hopeReportMapper.js:654-655` | CMS HOPE item set / timepoint specifications | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 19 | N0500/N0510/N0520 are medication (opioid/bowel-regimen) items — **or** BIMS cognitive items | Contradictory: `form_registry.py:408-412` + `hopeReportMapper.js:633-635` vs `RNICA.jsx:9030-9033` + `structured_findings.py:1224-1270` | CMS HOPE item set (and, for BIMS, the MDS/BIMS instrument specification) | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass. **This is the single highest-priority external verification need identified by this pass** |
| 20 | M1190/M1195/M1200 belong to the skin section (not performance status) | `form_registry.py:402-406` vs sidebar tagging `RNICA.jsx:209` | CMS HOPE item set | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 21 | Z0350/Z0400/Z0500 completion/attestation semantics, and whether Z0400 is mandatory | `form_registry.py:414-418`; Z0400 never emitted | CMS HOPE item set | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 22 | `I0000` is a real CMS item code | `hopeReportMapper.js:603` | CMS HOPE item set | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 23 | A "clinical narrative" is a required element of a comprehensive assessment prior to lock | `RNICA.jsx:1091-1092` (frontend error), `clinical_note_validation_engine.py:412-419` | Medicare hospice Conditions of Participation (comprehensive assessment/plan of care), plus professional documentation standards | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 24 | A clinician signature + attestation is required before lock | `rnica_finalization_service.py:103-116` | Medicare hospice CoPs; state licensing | Federal + California | NOT VERIFIED — external regulatory source not accessible this pass |
| 25 | "CDPH: Caregiver ability to administer meds required" | `RNICA.jsx:998-999` (the repository's own warning text names CDPH) | California Department of Public Health hospice licensing regulations | California | NOT VERIFIED — external regulatory source not accessible this pass |
| 26 | LCD eligibility support narrative is required before lock | `rnica_finalization_service.py:130-135`; `docs/tenant-platform/L33393_VALIDATION_CHECKLIST.md` | The applicable Medicare Administrative Contractor LCD for hospice determination of terminal status | Federal (US) / MAC jurisdiction | NOT VERIFIED — external regulatory source not accessible this pass |
| 27 | Post-lock edits must be captured as an authenticated addendum rather than silent mutation | `RNICA.jsx:489-506` (design comment); `backend/app/models/rnica_amendment.py:78` | Medicare CoPs / professional documentation standards | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |
| 28 | HOPE submission must be re-validated server-side rather than client-side only (Finding A's compliance implication) | `rnica_finalization_service.py:5-8` states the backend is the enforcement boundary for locking; no equivalent exists for HOPE | CMS HQRP submission requirements; agency-level QA policy | Federal (US) | NOT VERIFIED — external regulatory source not accessible this pass |

---

## Standing caveat

Nothing in this register, and nothing in the companion Phase 2 documents,
establishes what any external authority currently requires. Each row states
only what **this repository implements or asserts**. Determining whether
those implementations are correct, current, and binding — and what the
consequences of the N0500/N0510/N0520 contradiction are for an actual HOPE
submission — requires review by a qualified human compliance/legal
reviewer with access to the controlling sources.
