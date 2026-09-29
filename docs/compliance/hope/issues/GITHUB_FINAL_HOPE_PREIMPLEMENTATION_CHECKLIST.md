# OWNER DIRECTIVE: Correct and Complete the HOPE Pre-Implementation Package

**Status:** Implementation not authorized  
**Branch:** Dedicated HOPE correction branch only  
**PR #165:** Blocked and unmerged  
**Production code/database/schema/migrations:** No changes authorized

## 1. Correct the official item inventory

- [ ] Correct Section A top-level count to **20**.
- [ ] Correct Section F top-level count to **4**.
- [ ] Preserve Section I as **one** official top-level item: I0010.
- [ ] Retract I0600, I6202, and I8005 as HOPE items unless a current official CMS source explicitly contains them.
- [ ] Record the cause of each prior counting or source error.
- [ ] Preserve correction history. Do not silently delete prior claims.

## 2. Build the official, machine-readable inventory

Create:

- `HOPE_OFFICIAL_ITEM_INVENTORY_1.0.csv`
- `HOPE_OFFICIAL_ITEM_INVENTORY_1.0.md`

Requirements:

- [ ] Distinguish top-level items from lettered subitems.
- [ ] Generate all counts from the inventory.
- [ ] Reject duplicate, missing, unknown, and wrong-section item IDs.
- [ ] Record source document, version, location, effective date, and applicable errata.

## 3. Preserve the CMS authority package

Preserve official copies and checksums for:

- [ ] HOPE Guidance Manual v1.02, effective October 1, 2025.
- [ ] Final HOPE Data Submission Specifications v1.00.1, effective October 1, 2025.
- [ ] Errata v1.00.2, including J0915 skip/caret corrections.
- [ ] Errata v1.00.3, including A1400 technical-edit changes effective February 18, 2026.
- [ ] Admission, HUV, Discharge, and all-item item sets.
- [ ] Current HQRP HOPE measure specifications.
- [ ] Current HOPE FAQs and CMS VUT instructions.

Do not modify official source files. HospiceMD and internal crosswalks are comparison aids only.

## 4. Complete the requirements traceability matrix

Trace Sections A, F, I, J, M, N, and Z. For every applicable item, resolve:

- [ ] official concept and title;
- [ ] record type and timepoint;
- [ ] look-back period and role;
- [ ] permitted evidence sources;
- [ ] complete value set, caret, blank, and not-applicable behavior;
- [ ] skip, timing, and trigger rules;
- [ ] correction, audit, export, and technical edits;
- [ ] authoritative SNS field and supporting fields;
- [ ] UI, API, storage, validation, export, and test mappings;
- [ ] historical-data impact and owner decision.

Allowed statuses only: `PASS`, `FAIL`, `PARTIAL`, `NOT IMPLEMENTED`, `NOT APPLICABLE`, `UNVERIFIED`.

## 5. Trace all five timepoints independently

- [ ] Admission
- [ ] HUV1
- [ ] HUV2
- [ ] SFV
- [ ] Discharge

For each, document applicability, window, required/excluded items, skips, triggers, dates, signatures, sequencing, correction, export, technical edits, and tests.

## 6. Complete Section J

- [ ] Trace J0050, J0900, J0905, J0910, J0915, J2030, J2040, J2050, J2051, J2052, and J2053.
- [ ] J2051A-H each support `0`, `1`, `2`, `3`, and `9` where required by the controlling source.
- [ ] Symptom presence, severity, intensity, frequency, or body-system state does not replace Symptom Impact.
- [ ] J2051C Anxiety and J2051H Agitation are independent clinician entries.
- [ ] “At rest” remains respiratory context and does not automatically determine J2051B.
- [ ] Complete J2050/J2052 skips and timing.
- [ ] Trace J2053 correction, export, audit, and tests, not only its value set.

## 7. Complete Section M as one workflow

- [ ] M1190 Skin Conditions
- [ ] M1195 Types of Skin Conditions
- [ ] M1200 Skin and Ulcer/Injury Treatments
- [ ] Remove the conceptual mapping from M1190 to PPS.
- [ ] Define authoritative skin/wound source, clinician confirmation, multiple-condition handling, treatment linkage, correction, export, audit, and tests.

## 8. Complete Section N

- [ ] N0500 Scheduled Opioid
- [ ] N0510 PRN Opioid
- [ ] N0520 Bowel Regimen
- [ ] Remove all conceptual association with BIMS.
- [ ] Use structured active medication/order data plus explicit clinician confirmation.
- [ ] Free-text matching is supportive only, never authoritative.
- [ ] Trace active dates, discontinued status, scheduled/PRN status, routes, duplicates, aliases, imports, corrections, export, audit, and tests.

## 9. Complete Section Z

- [ ] Z0350 completion date
- [ ] Z0400 completer signatures
- [ ] Z0500 verifier signature
- [ ] Define role, date ordering, correction, submission readiness, audit, export, technical edits, and tests.

## 10. Define the canonical registry and CI validator

- [ ] Complete `HOPE_CANONICAL_REGISTRY_CONTRACT_1.0.md`.
- [ ] Complete `HOPE_CI_VALIDATOR_DESIGN_1.0.md`.
- [ ] CI fails for unknown/duplicate/wrong-section IDs, wrong concepts/value sets/timepoints, missing exports/corrections/tests, and registry mismatches.
- [ ] No permanent exceptions.

## 11. Complete schema, correction, and historical-compatibility design

- [ ] Complete the 12-question schema-capability review.
- [ ] Issue one conclusion: `NO SCHEMA CHANGE REQUIRED`, `SCHEMA CHANGE REQUIRED`, `AUDIT TABLE REQUIRED`, `EVENT MODEL REQUIRED`, `MULTIPLE CHANGES REQUIRED`, or `NOT VERIFIED`.
- [ ] Complete correction/audit design for draft, prefill, confirmation, derivation, import, corrections, modification, inactivation, rejected/accepted submissions, resubmission, export, and SFV effects.
- [ ] Complete historical provenance categories A-G.
- [ ] Do not rewrite historical records.

## 12. Create the exact test matrix and VUT plan

- [ ] Complete `HOPE_REQUIREMENTS_TEST_MATRIX_1.0.csv` and `.md`.
- [ ] Every test has a stable ID and expected persistence, audit, export, and VUT result.
- [ ] Complete `HOPE_VUT_TEST_FILE_PLAN_1.0.md`.
- [ ] Plan synthetic Admission, HUV1, HUV2, SFV, Discharge, skip, trigger, correction, invalid-value, sequencing, A1400, and J0915 cases.
- [ ] No production patient information.

## 13. Reconcile documentation

- [ ] Complete a cross-document conflict sweep.
- [ ] Identify one canonical file for authority, inventory, traceability, defects, design, tests, confidence, VUT, and checksums.
- [ ] Preserve prior incorrect statements in correction history.
- [ ] Update checksums after every approved documentation update.

## 14. Reporting discipline

Every report distinguishes:

`PROPOSED` → `DESIGNED` → `IMPLEMENTED` → `STATICALLY VERIFIED` → `TESTED` → `RUNTIME VERIFIED` → `CMS VUT VALIDATED`

Do not equate planned with executed, implemented with tested, tested with runtime verified, or “Ready to merge” with compliance readiness.

## 15. Exit gates

- [ ] Gate 1: Requirements complete
- [ ] Gate 2: Design complete
- [ ] Gate 3: Test/VUT planning complete
- [ ] Applicable unverified items equal zero or have explicit owner-approved exclusions
- [ ] Owner approval recorded

Implementation remains unauthorized until all gates pass.

## Required final response

Return the corrected counts, source package/checksums, section/timepoint statuses, schema conclusion, document paths, test counts, VUT file counts, unresolved conflicts, gates, change status, PR #165 status, and owner-approval request.
