# HOPE High-Value Blockers

Status: Post-SFV-ownership-remediation targeted blocker list. SFV
ownership/cross-timepoint leakage is CLOSED (see
`P0_SFV_OWNERSHIP_REMEDIATION.md`, commit `c540e277`) and is intentionally
**excluded** from this document. This list only covers the remaining
item-level HOPE generation blockers, per instruction: no re-discovery, no
architecture/ownership redesign — targeted, individually-resolvable gaps
only, sourced from prior repository-trace work already on file
(`HOPE_ITEM_PROVENANCE_MATRIX.md`, `J2052C_SOURCE_DISCOVERY.md`,
`DC_PROVENANCE_TRACE.md`, `HUV1_PROVENANCE_TRACE.md`,
`HUV2_PROVENANCE_TRACE.md`).

Rule in effect: SNS Review Rule. `STATUS` values are restricted to
`VERIFIED`, `NOT_VERIFIED`, `OPEN_QUESTION` and cited to their source
document — no new claims are made in this file.

**Post-commit verification correction (2026-09-23, re-verified against
commit `e3806cb`):** J2052C, I0000, and J2050 below were re-traced with
an expanded candidate search and are now cross-linked to
`J2052C_DECISION_RECORD.md`, `I0010_PRINCIPAL_DIAGNOSIS_PROVENANCE_
TRACE.md`, and `J2050_PROVENANCE_TRACE.md` (the canonical, more detailed
traces) rather than restating their conclusions here. A duplicate
editable primary-diagnosis authority (`Patient.primary_diagnosis` vs.
RNICA's `diagnoses.primaryDiagnosis`) is surfaced below — this is not a
new defect: it is already documented in the pre-existing
`RNICA_HOPE_SFV_FIELD_PLACEMENT_MAP.md:1363` as an accepted by-design
separation, though whether that guidance is sufficient against
cross-validation risk remains open (see
`I0010_PRINCIPAL_DIAGNOSIS_PROVENANCE_TRACE.md` Section B.4).

---

## 1. J2052C — Reason SFV Not Completed

| | |
|---|---|
| CMS Requirement | Required only when J2052A = No. Codes: 1 = declined, 2 = unavailable, 3 = unable to contact, 9 = none of the above |
| Current SNS Source | None authoritative. Only candidate is `RNICA.jsx` `sfv.reasonNotCompleted` — free text, self-attestation at trigger time, not CMS-coded |
| Verification Status | **NOT_VERIFIED** — no authoritative source exists after an expanded candidate search (see `J2052C_DECISION_RECORD.md`, which supersedes `J2052C_SOURCE_DISCOVERY.md` as the canonical trace) |
| Risk | Field would export as placeholder/blank or an unvalidated free-text value if wired without a fix; low risk of silent wrong-code export since no code mapping exists to misfire, but the item cannot be completed today |
| Fix Required | Structural — no backend field/endpoint captures "why an SFV was not completed" at all today. Requires new capture workflow (Option A), or an explicit decision to leave it unexported (Option B) |
| Blocked By | Romel decision (Option A vs. B) — already escalated, unresolved |
| Priority | P1 |
| Estimate Size | **Medium** (Option A: new field/endpoint + UI) or **Small** (Option B: document as permanent placeholder) |

---

## 2. I0000 / I0010 — Diagnosis Items

| | |
|---|---|
| CMS Requirement | I0010 (Principal Diagnosis) is registry-confirmed as a declared HOPE code (`form_registry.py`); I0000 ("Comorbidities and Co-existing Conditions") is not in that registry and its CMS legitimacy is unconfirmed |
| Current SNS Source | I0010: `RnicaAssessment.form_data.diagnoses.primaryDiagnosis`. I0000: `diagnosisList(diagnoses)` (corrected function citation — see `I0010_PRINCIPAL_DIAGNOSIS_PROVENANCE_TRACE.md`) |
| Verification Status | I0000: **OPEN_QUESTION** (corroborated by pre-existing `ITEM_CODE_CONFLICT_MATRIX.md` Conflict 5). I0010: **NOT_VERIFIED** (CMS accuracy) + newly found **DUPLICATE_EDITABLE_AUTHORITY** vs. `Patient.primary_diagnosis` (Facesheet) |
| Risk | I0000: mis-tagged data if exported under a non-real CMS code. I0010: the Facesheet's `primary_diagnosis` and RNICA's `diagnoses.primaryDiagnosis` can diverge with no reconciliation — only the RNICA value reaches the HOPE export |
| Fix Required | I0000: CMS-authority lookup only. I0010: policy decision on single source of truth between Facesheet and RNICA diagnosis fields (no reconciliation implemented) |
| Blocked By | CMS authority confirmation (I0000); Clinical Operations/Romel decision on diagnosis ownership (I0010) |
| Priority | P3 (I0000) / P2 (I0010 duplicate-authority question, newly surfaced) |
| Estimate Size | **Small** (I0000) / **Small–Medium** (I0010 policy decision + possible cross-validation) |

---

## 3. J2050 — Symptom Impact Screening Completed

| | |
|---|---|
| CMS Requirement | Boolean: was symptom-impact screening completed (and on what date) |
| Current SNS Source | `RnicaAssessment.form_data` → `sfv.symptomImpactScreeningCompleted`/`.Date` OR `symptomImpact.assessmentDate` — reads RNICA **self-attestation**, not `SFVRequirement` |
| Verification Status | **OPEN_QUESTION** — expanded trace completed post-commit; corrected finding: J2050 does **not** carry the cross-timepoint SFVRequirement-leak defect (it never reads `SFVRequirement`), but does carry an unvalidated OR-fallback and an unverified within-record staleness question (see `J2050_PROVENANCE_TRACE.md`, which supersedes the summary previously here) |
| Risk | Not a cross-timepoint SFV leak (ruled out this pass — J2050 reads only the exported record's own `RnicaAssessment.form_data`, same isolation mechanism confirmed for the mapper generally). Residual risk: no CMS-authority confirmation of the response set, and an unvalidated OR between two independently-settable fields |
| Fix Required | CMS-authority confirmation of the response set; decide whether the OR-fallback between `sfv.symptomImpactScreeningCompleted` and `symptomImpact.assessmentDate` needs validation/reconciliation |
| Blocked By | Nothing external — this is a self-contained repository trace + possible reuse of the J2052/J2053 fix pattern |
| Priority | P1 |
| Estimate Size | **Small–Medium** |

---

## 4. ADM Item Completeness

| | |
|---|---|
| CMS Requirement | Full ADM item set (57 items in the mapper) |
| Current SNS Source | Per-item, see `HOPE_ITEM_PROVENANCE_MATRIX.md` ADM table |
| Verification Status | 3 VERIFIED (A0250, J2052 A/B, J2053) / 2 OPEN_QUESTION (I0000, J2050) / remainder **NOT_VERIFIED** — the majority of ADM items were never independently re-derived against primary CMS text this engagement; matrix explicitly flags this as the expected, honest state, not an assumption of correctness |
| Risk | Field-level export correctness for ~52 items has not been independently confirmed against CMS source requirements (values are traced to repository code, not validated against CMS text) |
| Fix Required | Per-item CMS re-derivation pass (no code change implied unless a mismatch is found) |
| Blocked By | Nothing — CMS-authority documentation work only |
| Priority | P2 |
| Estimate Size | **Large** (57 items, one-by-one) |

---

## 5. HUV1 Item Completeness

| | |
|---|---|
| CMS Requirement | Same item set as ADM minus F2000/F2100/F2200/F3000, plus Z0350 (54 items) |
| Current SNS Source | Confirmed sourced from the matched Update Assessment's own `form_data`, never the admission's (`HUV1_PROVENANCE_TRACE.md`) |
| Verification Status | Same distribution as ADM (3 VERIFIED / 2 OPEN_QUESTION / rest NOT_VERIFIED), plus Z0350 (NOT_VERIFIED, new item) |
| Risk | Same as ADM — CMS-text-level correctness unconfirmed for the majority of items |
| Fix Required | Same per-item CMS re-derivation pass |
| Blocked By | Nothing |
| Priority | P2 |
| Estimate Size | **Large** |

---

## 6. HUV2 Item Completeness

| | |
|---|---|
| CMS Requirement | Same as HUV1 (54 items) |
| Current SNS Source | Confirmed sourced from the matched HUV2 assessment's own `form_data` (`HUV2_PROVENANCE_TRACE.md`) |
| Verification Status | Same distribution as HUV1 |
| Risk | Same as ADM/HUV1 |
| Fix Required | Same per-item CMS re-derivation pass |
| Blocked By | Nothing |
| Priority | P2 |
| Estimate Size | **Large** |

---

## 7. Discharge (DC) Item Completeness

| | |
|---|---|
| CMS Requirement | Section A (18 items, same as ADM) + A0270 + A2115 + Z0500 (21 items total) |
| Current SNS Source | Per-item, see `HOPE_ITEM_PROVENANCE_MATRIX.md` DC table; A2115 has real write-time validation (`finalize_patient_discharge` rejects unregistered `reason_code`, HTTP 422) but its CMS-code accuracy was not independently cross-checked |
| Verification Status | 20 **NOT_VERIFIED**, 0 VERIFIED, 0 OPEN_QUESTION — Discharge does not emit J2052/J2053 at all (Section A + Z0500 only, confirmed via `DC_PROVENANCE_TRACE.md`), so it did not benefit from the SFV ownership fix |
| Risk | Same category as ADM/HUV1/HUV2 — CMS-text-level correctness unconfirmed. A2115's registry-vs-CMS-code accuracy is the single highest-value item to check first (validated capture, but crosswalk unverified) |
| Fix Required | Per-item CMS re-derivation pass; prioritize A2115 registry-to-CMS-code crosswalk check |
| Blocked By | Nothing |
| Priority | P2 |
| Estimate Size | **Medium** (21 items, smaller set than ADM/HUV1/HUV2) |

---

## Top 5 Blockers (priority order)

1. **J2052C** — no authoritative source exists after expanded candidate search; structural gap; requires Romel decision before any fix (see `J2052C_DECISION_RECORD.md`)
2. **I0010 duplicate editable authority** — `Patient.primary_diagnosis` (Facesheet) and RNICA's `diagnoses.primaryDiagnosis` are independently editable with no cross-validation; only RNICA's value reaches HOPE export. Not newly discovered — already documented in pre-existing `RNICA_HOPE_SFV_FIELD_PLACEMENT_MAP.md:1363` as an accepted by-design separation, but that guidance's sufficiency against cross-validation risk is unre-affirmed (see `I0010_PRINCIPAL_DIAGNOSIS_PROVENANCE_TRACE.md`)
3. **J2050** — ruled out for cross-timepoint leakage this pass, but carries an unvalidated OR-fallback and CMS-authority gap; self-contained fix, no external blocker (see `J2050_PROVENANCE_TRACE.md`)
4. **I0000** — CMS-authority confirmation only; fastest to close
5. **A2115 (Discharge)** — validated capture exists, but CMS-code crosswalk accuracy unconfirmed; highest-value single item in the completeness backlog

## HOPE Generation Readiness

**Blocking reason has changed**, per instruction:
- ~~Ownership uncertainty~~ — **RESOLVED** (commit `c540e277`)
- **Item completeness — OPEN** (this document's items)
- **Update (post-CMS-authority-research):** A CMS HOPE Item Set
  authority document is now **VERIFIED BY CMS to exist and has been
  directly read** — HOPE Guidance Manual v1.02, effective October 1,
  2025, fetched and checksummed from `cms.gov` (see
  `HOPE_CMS_AUTHORITY_SOURCE_REGISTER.md`). It is not stored in this
  repository (deliberate policy: citations/checksums only, no vendored
  PDFs), and only I0010, J2050, J2051, and Section J (J2052A/B/C,
  J2053) were individually read against it this pass — the full
  ADM/HUV1/HUV2/DC applicable-item counts were **not** re-derived
  page-by-page. Every completeness figure in
  `ADM/HUV1/HUV2/DC_COMPLETENESS_MATRIX.md` therefore remains stated as
  `COMPLETENESS: NOT_VERIFIED` / `DENOMINATOR: NOT_VERIFIED` rather than
  a raw percentage — the gap is now "per-item re-derivation not yet
  done," not "no CMS document exists."

HOPE generation is not yet safe to begin. Earliest safe start requires,
at minimum: J2052C decision (Romel), the I0010 duplicate-authority policy
decision, and J2050's OR-fallback/CMS-response-set confirmation, since
all three are P1/P2 and touch fields already inside the exported item
set today. ADM/HUV1/HUV2/DC bulk completeness does not need to fully
complete before a first generation attempt, provided its NOT_VERIFIED
status is explicitly disclosed as a known limitation rather than
silently treated as verified.
