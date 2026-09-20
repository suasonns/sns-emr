# RNICA Authority Matrix

**STATUS:** DISCOVERY / AUTHORITY REFERENCE ONLY. NOT IMPLEMENTATION AUTHORIZATION.
**CODE:** BLOCKED
**SCHEMA:** BLOCKED
**MIGRATIONS:** BLOCKED
**AUTOMATIC VISIT CLASSIFICATION:** BLOCKED

This document is the single consolidated authority-classification reference
for RNICA/HOPE assessment and visit classification. It extracts and
supersedes the "Appendix A" table previously embedded in
[`RNICA_ASSESSMENT_VISIT_CLASSIFICATION_RULES.md`](./RNICA_ASSESSMENT_VISIT_CLASSIFICATION_RULES.md),
which now links here instead of duplicating it.

## Full Authority Classification Table

| Topic | Authority Label | Rule / Source |
| --- | --- | --- |
| RN Initial Assessment (48 hours after hospice election) | `FEDERAL_CMS_REQUIRED` | `42 CFR §418.54`. Separate assessment completed by RN within federal Initial Assessment timeframe. Do not merge with Comprehensive Assessment. |
| Initial Comprehensive Assessment (within 5 calendar days) | `FEDERAL_CMS_REQUIRED` | `42 CFR §418.54`. Separate interdisciplinary assessment completed within the federal Comprehensive Assessment timeframe. |
| Comprehensive Assessment Updates | `FEDERAL_CMS_REQUIRED` | `42 CFR §418.54`. Updated as condition requires; tracked separately from Initial Comprehensive Assessment. |
| Initial Assessment within 48 hours of admission | `CALIFORNIA_REQUIRED` | `DPH-18-002E`, §74864(a). RN assessment within 48 hours of admission. |
| Comprehensive Assessment within 5 days of admission | `CALIFORNIA_REQUIRED` | `DPH-18-002E`, §74864(b). IDT assessment within 5 days of admission. |
| Plan of Care derived from assessment findings | `CALIFORNIA_REQUIRED` | `DPH-18-002E`, §§74864, 74868. Assessment evidence supports development of individualized Plan of Care. |
| Referral Received Date | `SNS_INTERNAL_WORKFLOW` | SNS operational policy. Internal operational tracking field. |
| Referral Expiration Rule | `SNS_INTERNAL_WORKFLOW` | SNS operational policy, unless a controlling authority explicitly requires otherwise. |
| Hospice Election Date | `FEDERAL_CMS_REQUIRED` | `42 CFR §418.54`. Regulatory start point for federal assessment timing. |
| Admission Effective Date | `REPOSITORY_CURRENT_STATE` | Discovery mapping required; must be preserved separately from election date. |
| Start of Care Date | `REPOSITORY_CURRENT_STATE` | Discovery mapping required; must remain independently traceable. |
| RNICA | `SNS_INTERNAL_WORKFLOW` | SNS discipline contribution to comprehensive assessment package. |
| MSW ICA | `SNS_INTERNAL_WORKFLOW` | SNS discipline contribution to comprehensive assessment package. |
| SC ICA | `SNS_INTERNAL_WORKFLOW` | SNS discipline contribution to comprehensive assessment package. |
| Comprehensive Assessment Package Completion | `SNS_INTERNAL_WORKFLOW` | Complete only when required discipline contributions are completed or exempted. |
| Authenticated Discipline Validation | `SNS_INTERNAL_WORKFLOW` | Discipline source derived from authenticated user and verified credential. |
| Discipline Mismatch Blocking | `SNS_INTERNAL_WORKFLOW` | Classification blocked until mismatch resolved. |
| HOPE Admission | `OFFICIAL_HOPE_REQUIRED` | HOPE Guidance Manual v1.02, CMS HOPE overview. Separate HOPE timepoint. |
| HUV1 (Days 6-15) | `OFFICIAL_HOPE_REQUIRED` | Official HOPE Update Visit 1 timing. |
| HUV2 (Days 16-30) | `OFFICIAL_HOPE_REQUIRED` | Official HOPE Update Visit 2 timing. |
| HUV1 Candidate Prompt | `OFFICIAL_HOPE_REQUIRED` | HOPE timing requirement; may prompt, never auto-classify. |
| HUV2 Candidate Prompt | `OFFICIAL_HOPE_REQUIRED` | HOPE timing requirement; may prompt, never auto-classify. |
| Day-14 CHHA Supervisory Fallback | `SNS_INTERNAL_WORKFLOW` | Internal review prompt for possible HUV1. |
| Day-28 CHHA/LVN Supervisory Fallback | `SNS_INTERNAL_WORKFLOW` | Internal review prompt for possible HUV2. |
| SFV | `OFFICIAL_HOPE_REQUIRED` | HOPE Guidance Manual v1.02. Separate symptom follow-up workflow. |
| SFV Trigger Logic | `OFFICIAL_HOPE_REQUIRED` | HOPE v1.01-v1.02 change table. Driven by qualifying symptoms identified during HOPE Admission or HUV. |
| SFV Eligibility Window | `OFFICIAL_HOPE_REQUIRED` | HOPE Guidance Manual v1.02, HOPE v1.01-v1.02 change table. SFV can occur during the first 30 days of hospice service, since its triggering source records are HOPE Admission, HUV1, and HUV2. SFV is not triggered solely by time; it requires a qualifying symptom finding in a triggering HOPE record. A patient within the first 30 days may have no SFV requirement if no qualifying finding exists. |
| SFV May Be Performed by RN or LPN/LVN | `OFFICIAL_HOPE_REQUIRED` | HOPE v1.01-v1.02 change table; not restricted to RN. |
| LVN Identifies Qualifying HOPE Symptom | `SNS_INTERNAL_WORKFLOW` | SNS escalation workflow (see `RNICA_VISIT_CLASSIFICATION_DECISION_TABLE.md` §6.1). |
| LVN Finding Creates RN Review Recommendation | `SNS_INTERNAL_WORKFLOW` | SNS escalation workflow; displays "RN Assessment Review Recommended" and a compliance alert. |
| LVN Finding Automatically Creates SFV | `PROHIBITED_ASSUMPTION` | Not established in CMS source; an LVN finding may only recommend RN review, never auto-create or auto-complete an SFV. |
| RN Initial Assessment = SFV | `PROHIBITED_ASSUMPTION` | Not supported by HOPE guidance. Must not be treated as equivalent. |
| RNICA = Entire Comprehensive Assessment | `PROHIBITED_ASSUMPTION` | SNS workflow contribution only. Must not be treated as equivalent. |
| HOPE Submission Platform | `OFFICIAL_HOPE_REQUIRED` | HOPE technical information. iQIES. |
| Legacy QIES References | `LEGACY_REFERENCE` | Historical compatibility only. |
| Recertification Assessment | `FEDERAL_CMS_REQUIRED` | `42 CFR §418.54`, CMS LCD guidance. Supports physician recertification review; does not replace certification. |
| LCD Clinical Picture Documentation | `LCD_DOCUMENTATION_GUIDANCE` | CMS LCD guidance materials. |
| Functional, ADL, and Decline Evidence | `LCD_DOCUMENTATION_GUIDANCE` | Hospice terminal-prognosis, non-disease-specific documentation guidance. |
| Automated Eligibility Decision | `PROHIBITED` | RNICA must not determine eligibility automatically; physician judgment required. |
| Automated Physician Certification | `PROHIBITED` | RNICA must not create physician certification; remains a physician responsibility. |
| Diagnosis Alone = Eligibility | `PROHIBITED` | Documentation must support prognosis and clinical picture, not diagnosis alone. |
| HOPE/SFV Visibility Map | `SNS_INTERNAL_WORKFLOW` | Hidden until RNICA finalization (SNS design decision). |
| RNICA Finalization | `SNS_INTERNAL_WORKFLOW` | Preserves classifications, timestamps, actor, and source links (SNS design decision). |
| Post-Finalization Silent Overwrite | `PROHIBITED` | Must use correction, amendment, or re-finalization workflow (audit integrity requirement). |
| Audit Trail Preservation | `CALIFORNIA_REQUIRED` + `SNS_INTERNAL_WORKFLOW` | Preserve users, dates, evidence, classifications, and source records. |

## Discovery Status

| Area | Status |
| --- | --- |
| Regulatory Discovery | AUTHORIZED |
| Workflow Discovery | AUTHORIZED |
| HOPE Discovery | AUTHORIZED |
| RNICA Assessment Discovery | AUTHORIZED |
| Source Validation | AUTHORIZED |
| UI Development | NOT_AUTHORIZED |
| JSX / Tailwind Generation | NOT_AUTHORIZED |
| API Development | NOT_AUTHORIZED |
| Database Changes | NOT_AUTHORIZED |
| Schema Changes | NOT_AUTHORIZED |
| Production Workflow Changes | NOT_AUTHORIZED |

## Controlling Sources

- **`FEDERAL_CMS_REQUIRED`** — `42 CFR §418.54` (Initial and Comprehensive
  Assessment requirements):
  https://www.ecfr.gov/current/title-42/chapter-IV/subchapter-B/part-418/subpart-C/section-418.54
- **`CALIFORNIA_REQUIRED`** — California `DPH-18-002E` (Hospice Agencies),
  §§74864, 74868 — assessment, Plan of Care, IDT, and documentation
  requirements.
- **`OFFICIAL_HOPE_REQUIRED`** — HOPE Guidance Manual v1.02
  (https://www.cms.gov/files/document/hope-guidance-manual-v1-02.pdf), CMS
  HOPE overview (https://www.cms.gov/medicare/quality/hospice/hope), HOPE
  v1.01-v1.02 item-set change table
  (https://www.cms.gov/files/document/hope-v1-01-1-02-guidance-manual-item-set-change-table.pdf),
  HOPE technical information
  (https://www.cms.gov/medicare/quality/hospice-quality-reporting-program/hope-technical-information).
- **`LCD_DOCUMENTATION_GUIDANCE`** — CMS LCD guidance and hospice
  terminal-prognosis, non-disease-specific documentation guidance
  materials referenced during this discovery pass; specific LCD number(s)
  remain `PENDING_SOURCE_VALIDATION` for this document's scope (see
  P2-001, issue #101, for the dedicated LCD L33393 validation track).

## Source Priority

When sources appear to conflict, controlling order for this document is:

1. California `DPH-18-002E` (Hospice Agencies), §74864 and related sections.
2. `42 CFR §418.54`.
3. CMS HOPE Guidance Manual v1.02 and related HOPE materials.
4. CMS LCD guidance and terminal-prognosis documentation references.
5. Disease-specific LCD support guides (tracked separately, e.g. P2-001).

This priority order governs documentation authorship only. It does not
authorize automatic conflict resolution in code, and no such code exists
or is authorized by this document.

## Open Discovery Item: Date-Anchor Conflict

`42 CFR §418.54` anchors the federal 48-hour/5-day assessment clock to
**hospice election**, while `DPH-18-002E §74864` anchors the same clock to
**admission**. This discrepancy is `PENDING_SOURCE_VALIDATION` and must not
be silently resolved by assuming the two dates are identical. See
`RNICA_HOPE_SOURCE_VALIDATION_GAPS.md` (Gap G-03).

## Implementation Boundary

`NOT_AUTHORIZED`. This document is discovery/documentation only. No
application behavior, JSX, Tailwind, routes, APIs, migrations, schemas,
enums, or production data are introduced or implied by this document.
