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

---

## 1. J2052C — Reason SFV Not Completed

| | |
|---|---|
| CMS Requirement | Required only when J2052A = No. Codes: 1 = declined, 2 = unavailable, 3 = unable to contact, 9 = none of the above |
| Current SNS Source | None authoritative. Only candidate is `RNICA.jsx` `sfv.reasonNotCompleted` — free text, self-attestation at trigger time, not CMS-coded |
| Verification Status | **NOT_VERIFIED** — no authoritative source exists (`J2052C_SOURCE_DISCOVERY.md`) |
| Risk | Field would export as placeholder/blank or an unvalidated free-text value if wired without a fix; low risk of silent wrong-code export since no code mapping exists to misfire, but the item cannot be completed today |
| Fix Required | Structural — no backend field/endpoint captures "why an SFV was not completed" at all today. Requires new capture workflow (Option A in `J2052C_SOURCE_DISCOVERY.md`), or an explicit decision to leave it unexported (Option B) |
| Blocked By | Romel decision (Option A vs. B) — already escalated, unresolved |
| Priority | P1 |
| Estimate Size | **Medium** (Option A: new field/endpoint + UI) or **Small** (Option B: document as permanent placeholder) |

---

## 2. I0000 — Diagnosis List Summary

| | |
|---|---|
| CMS Requirement | Not confirmed as a real, distinct CMS item code — not seen cited elsewhere in this engagement's CMS references |
| Current SNS Source | `RnicaAssessment.form_data` → `diagnosisEntries(diagnoses)` (list join, internal summary row) |
| Verification Status | **OPEN_QUESTION** — whether `I0000` is a genuine CMS item or an internal-only summary was never resolved (`HOPE_ITEM_PROVENANCE_MATRIX.md`) |
| Risk | If exported under a real CMS item code without CMS confirmation, mis-tagged data could be submitted; if it's internal-only, no clinical risk but wastes an export slot |
| Fix Required | CMS-authority lookup only — confirm whether `I0000` exists in the CMS HOPE item set; if not, remove/rename the export row (no code change beyond a decision) |
| Blocked By | CMS authority confirmation (no repository ambiguity — this is a documentation/reference lookup, not a code trace) |
| Priority | P3 |
| Estimate Size | **Small** |

---

## 3. J2050 — Symptom Impact Screening Completed

| | |
|---|---|
| CMS Requirement | Boolean: was symptom-impact screening completed (and on what date) |
| Current SNS Source | `RnicaAssessment.form_data` → `sfv.symptomImpactScreeningCompleted`/`.Date` OR `symptomImpact.assessmentDate` — reads RNICA **self-attestation**, not `SFVRequirement` |
| Verification Status | **OPEN_QUESTION** — same self-attestation shape the P1A/P1B directives required removing for J2052/J2053, but J2050 itself was never in scope and was never fixed (`HOPE_ITEM_PROVENANCE_MATRIX.md`) |
| Risk | Same category of risk J2052/J2053 had pre-fix: the screening-completed flag could reflect the RNICA form's self-report rather than the actual completed SFV/ClinicalNote record. Cross-timepoint leakage risk not yet ruled out for this specific field |
| Fix Required | Trace whether `SFVRequirement`/`ClinicalNote` already carries an equivalent "screening completed" signal; if so, apply the same trigger-scoped ownership pattern used for J2052/J2053. If not, this is a smaller decision (documentation) than J2052C since no CMS code-set validation is involved (boolean + date only) |
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

1. **J2052C** — no authoritative source exists at all; structural gap; requires Romel decision before any fix
2. **J2050** — still reads RNICA self-attestation, same defect class as pre-fix J2052/J2053; self-contained fix, no external blocker
3. **I0000** — CMS-authority confirmation only; fastest to close
4. **A2115 (Discharge)** — validated capture exists, but CMS-code crosswalk accuracy unconfirmed; highest-value single item in the completeness backlog
5. **ADM/HUV1/HUV2/DC bulk item-level CMS re-derivation** — large, non-blocking-individually, but is the largest remaining share of NOT_VERIFIED rows

## HOPE Generation Readiness

**Blocking reason has changed**, per instruction:
- ~~Ownership uncertainty~~ — **RESOLVED** (commit `c540e277`)
- **Item completeness — OPEN** (this document's 7 items)

HOPE generation is not yet safe to begin. Earliest safe start requires,
at minimum: J2052C decision (Romel) and J2050 fix, since both are P1 and
touch fields already inside the exported item set today. ADM/HUV1/HUV2/DC
bulk completeness (P2) does not need to fully complete before a first
generation attempt, provided its NOT_VERIFIED status is explicitly
disclosed as a known limitation rather than silently treated as verified.
