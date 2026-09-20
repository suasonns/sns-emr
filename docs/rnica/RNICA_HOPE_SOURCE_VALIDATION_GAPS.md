# RNICA HOPE Source Validation Gaps

**STATUS:** DISCOVERY / AUTHORITY REFERENCE ONLY. NOT IMPLEMENTATION AUTHORIZATION.

## 1. Purpose

Track unresolved HOPE, SFV, HUV, and iQIES questions before implementation.
Nothing in this document should be treated as a finding that described
behavior currently exists in the application unless explicitly marked
`REPOSITORY_CURRENT_STATE` with a citation.

## 2. Controlling Sources

- CMS HOPE webpage
- Current HOPE Guidance Manual
- HOPE v1.01 to v1.02 change table
- HOPE item sets
- HOPE data-submission specifications
- iQIES technical guidance
- CMS vendor-training materials
- Repository: `docs/compliance/hope-sfv-guide.md`,
  `backend/app/services/sfv_engine.py`,
  `backend/app/services/hope_phase_b_engine.py`,
  `backend/app/models/sfv_requirement.py`

## 3. HUV1 Validation

| Question | Status |
| --- | --- |
| Official date window | Days 6-15 after election (per supplied authority rules) — `PENDING_SOURCE_VALIDATION` against a controlling HOPE manual citation |
| Day-counting convention | Not confirmed (calendar days assumed) |
| Applicable patients | Not confirmed — assumed all admitted hospice patients |
| Required clinician discipline | RN (per rules doc §7.2); CHHA supervisory fallback exists as `SNS_INTERNAL_WORKFLOW` (§8.1) |
| Required visit type | In-person RN visit assumed; not confirmed |
| Required items | Not enumerated in this discovery pass beyond `docs/compliance/hope-sfv-guide.md` general HOPE item set |
| Late HUV handling | Preserve actual visit date, no backdating, compliance-review item (rules doc §7.2) — not yet code-confirmed |
| Modification and inactivation | Not confirmed |
| Submission deadline | Not confirmed |
| Duplicate-record behavior | Target rule: one HUV1 per election episode — not yet code-confirmed |

## 4. HUV2 Validation

| Question | Status |
| --- | --- |
| Official date window | Days 16-30 after election (per supplied authority rules) — `PENDING_SOURCE_VALIDATION` |
| Applicability by length of stay | Not confirmed |
| Required clinician discipline | RN; CHHA/LVN supervisory fallback exists as `SNS_INTERNAL_WORKFLOW` (§8.2) |
| Required items | Not enumerated beyond general HOPE item set |
| Late HUV handling | Same as HUV1 (§3) — not yet code-confirmed |
| Modification and inactivation | Not confirmed |
| Submission deadline | Not confirmed |
| Duplicate-record behavior | Target rule: one HUV2 per election episode — not yet code-confirmed |

## 5. SFV Validation

| Question | Status |
| --- | --- |
| Triggering symptoms | J2051A-H, `MODERATE`/`SEVERE` — `REPOSITORY_CURRENT_STATE` (`sfv_engine.py` `TRIGGER_LEVELS`) |
| Triggering timepoints | HOPE Admission, HUV1, HUV2 (rules doc §7.4) |
| Follow-up timing | Trigger + 2 calendar days — `REPOSITORY_CURRENT_STATE` (`sfv_engine.py`) |
| RN or LPN/LVN authority | Confirmed in `docs/compliance/hope-sfv-guide.md` (J2052/J2053 rows) |
| Required symptom-impact items | J2053A-H per `docs/compliance/hope-sfv-guide.md` |
| Completion evidence | `SFVRequirement.status` PENDING/COMPLETE — `REPOSITORY_CURRENT_STATE`; "reason not completed" (J2052C) field not yet confirmed on the model |
| Multiple-symptom handling | One requirement per patient+symptom, duplicate-prevented — `REPOSITORY_CURRENT_STATE` |
| Modification and inactivation | Not confirmed |
| iQIES submission behavior | Not confirmed |

## 6. HOPE Admission Validation

| Question | Status |
| --- | --- |
| Admission record definition | Not fully traced in this discovery pass |
| Assessment evidence relationship | RNICA/HUV/Update UI shares underlying documentation UI per `docs/compliance/hope-sfv-guide.md` |
| Required items | See `docs/compliance/hope-sfv-guide.md` sections A/F/I/J/M/N |
| Completion date | Not confirmed to a specific field |
| Submission date | Not confirmed |
| Correction behavior | Not confirmed |

## 7. iQIES Validation

| Question | Status |
| --- | --- |
| Record types | Not confirmed |
| Submission status | Not confirmed |
| Fatal edits | Not confirmed |
| Warning edits | Not confirmed |
| Rejected records | Not confirmed |
| Modified records | Not confirmed |
| Inactivated records | Not confirmed |
| Resubmission | Not confirmed |
| Authoritative receipt evidence | Not confirmed |

Note: rules doc §7.5 confirms HOPE submission is through **iQIES**, not
legacy QIES; legacy QIES terminology should only appear when documenting
historical HIS behavior that predates iQIES.

## 8. SNS Internal Rules That Must Not Be Misclassified

- Referral expiration (`SNS_INTERNAL_WORKFLOW`, `PENDING_SOURCE_VALIDATION`)
- Day-14 supervisory fallback (`SNS_INTERNAL_WORKFLOW`)
- Day-28 supervisory fallback (`SNS_INTERNAL_WORKFLOW`)
- Hidden RNICA-to-HOPE map until finalization (`SNS_INTERNAL_WORKFLOW`)
- Internal compliance alerts (`SNS_INTERNAL_WORKFLOW`)

## 9. Gap Register

| Gap ID | Topic | Question | Source Reviewed | Status | Blocking | Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| G-01 | HUV1 window | Where is Days 6-15 computed in code, if anywhere? | `hope_phase_b_engine.py` | OPEN | Yes — for any HUV1 UI wiring | Further repository discovery required |
| G-02 | HUV2 window | Where is Days 16-30 computed in code, if anywhere? | `hope_phase_b_engine.py` | OPEN | Yes — for any HUV2 UI wiring | Further repository discovery required |
| G-03 | Election vs. admission anchor | Federal rules anchor to election; CA source (rules doc §5.4) anchors to admission — which governs SNS due-date calculation? | Supplied authority rules | OPEN | Yes — blocks any due-date logic | Requires controlling-source reconciliation, not a code fix |
| G-04 | Referral expiration source | Is 48-hour referral expiration established by any controlling authority, or purely SNS policy? | None located | OPEN | No (labeled SNS_INTERNAL_WORKFLOW pending validation) | Confirm with agency policy owner |
| G-05 | iQIES submission code path | What code, if any, submits HOPE/SFV records to iQIES? | Not located | OPEN | Yes — for iQIES-readiness UI wiring | Further repository discovery required |
| G-06 | Discipline-authority enforcement | What RBAC/authorization check enforces rules doc §9 today? | Not located | OPEN | Yes — for discipline-mismatch UI wiring | Further repository discovery required |
| G-07 | Recertification due-date source | What service/model computes benefit-period and recertification due date? | Not located | OPEN | Yes — for recertification UI wiring | Further repository discovery required |
| G-08 | SFV "reason not completed" field | Does `SFVRequirement` support a J2052C-equivalent reason field? | `backend/app/models/sfv_requirement.py` | OPEN | No (documentation gap only) | Confirm model fields during future discovery |

## 10. Implementation Gate

Implementation remains blocked until all required HOPE gaps above are
resolved. `NOT_AUTHORIZED`.
