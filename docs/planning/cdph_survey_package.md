# CDPH Survey Package Simulation (Phase 56)

Status: verification synthesis, scenario-based. No production code changed. No billing feature or AI
built. Simulates producing a complete CDPH survey package for one patient, against current California
Title 22 hospice-specific requirements (CCR §§74800-74908).

| Requested item | Demonstrable? | Evidence | Deficiency (if any) |
|---|---|---|---|
| Admission | Yes | `Admission` + `AdmissionStatusHistory` (`previous_status`, `new_status`, `changed_by`, `changed_at`, `reason`) | None confirmed |
| Assessment | Not demonstrated this engagement | Outside investigated scope | **Deficiency: unknown, needs dedicated review** |
| Plan of Care | Partial | Physician-approval check is real; version/audit history unconfirmed | Deficiency: audit depth unconfirmed |
| Certification | Yes | `Certification` + `CertificationStatusEvent`, physician-role attributed, narrative-evidenced | None confirmed |
| Clinical Notes | Yes | Note authorship + `Amendment` model for corrections | None confirmed |
| Medical Record (overall) | Yes, for the pieces confirmed above | Referral/Admission/Certification/clinical-note amendments are real, structured | Retention/export capability not evaluated this engagement |
| Addenda | Yes | `Amendment` model — structured, signed, timestamped, `reason` required non-null; `rnica_amendment.py` for RNICA-specific | Confirmed compliant with CDPH's newest structured-addendum requirement |
| Transfer | Not demonstrated this engagement | Outside investigated scope | **Deficiency: unknown, needs dedicated review** |
| Discharge | Not demonstrated this engagement | Outside investigated scope | **Deficiency: unknown, needs dedicated review** |

## Deficiencies identified (only where evidence supports the label)

- **Confirmed deficiency**: none of the CDPH-specific items directly investigated this engagement
  (Admission, Certification, Clinical Notes, Addenda) show a confirmed deficiency — all pass.
- **Unconfirmed / needs dedicated review**: Assessment, Transfer, Discharge, Plan-of-Care audit depth.
  These are not labeled as deficiencies because no evidence supports that label — they are labeled as
  open questions this engagement did not reach, consistent with the standing discipline against
  inferring compliance or non-compliance from absence of investigation.

## Overall read

The package CDPH would actually ask for today is, for every section this engagement directly
investigated, demonstrable and well-evidenced — including the newest, most recently changed
requirement (structured clinical-note addenda), which is a genuine strength worth stating plainly. The
honest gap in this simulation is scope, not failure: three sections (Assessment, Transfer, Discharge)
were never investigated in this engagement and must not be assumed either compliant or deficient.

No production code has changed. No billing feature or AI has been built.
