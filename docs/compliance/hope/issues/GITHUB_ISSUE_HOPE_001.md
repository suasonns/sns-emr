# HOPE-001: Complete CMS HOPE Requirements Inventory and Implementation-Ready Design

## Priority
P1, Blocking

## Status
OPEN

## Objective
Create an authoritative, machine-checkable HOPE requirements inventory; complete all seven section and five timepoint traces; design correction, audit, and historical-compatibility behavior; enumerate requirements-based tests; and define CMS VUT test files before production remediation begins.

## Current blockers

- Section A previously miscounted as 19 instead of 20.
- Section F previously reduced to one item instead of four.
- Sections A, F, and Z are unverified.
- Sections I, J, M, and N are partial.
- No timepoint is fully traced.
- J2050/J2052/skip/timing logic is unverified.
- Final technical specifications and current errata are not fully incorporated.
- Canonical registry is proposed only.
- Schema capability is unverified.
- Exact test matrix and VUT plan are absent.
- Runtime is unavailable.
- PR #165 is blocked.

## Required deliverables

- [ ] Authority register
- [ ] Official item inventory CSV and Markdown
- [ ] Complete traceability matrix CSV and Markdown
- [ ] Canonical registry contract
- [ ] CI validator design
- [ ] Schema-capability review
- [ ] Correction and audit model
- [ ] Historical-compatibility model
- [ ] Requirements test matrix CSV and Markdown
- [ ] VUT test-file plan
- [ ] Document-conflict report
- [ ] Updated README and checksum manifest

## Acceptance criteria

### Authority and inventory
- [ ] Guidance Manual v1.02, Data Specs v1.00.1, Errata v1.00.2/v1.00.3, item sets, measure specifications, FAQs, and VUT materials are preserved and checksummed.
- [ ] Section A count is 20.
- [ ] Section F count is 4.
- [ ] Section I contains I0010 as its one top-level item.
- [ ] Top-level and expanded-subitem counts are generated automatically.
- [ ] No duplicate, unknown, missing, or wrong-section IDs remain.

### Traceability
- [ ] Sections A, F, I, J, M, N, and Z are fully traced.
- [ ] Admission, HUV1, HUV2, SFV, and Discharge are fully traced.
- [ ] Values, carets, blanks, skips, triggers, timing, corrections, audit, exports, technical edits, and tests are mapped.

### Section J
- [ ] J2050, J2051, J2052, and J2053 are completely traced.
- [ ] J2051A-H support all required values.
- [ ] Patient findings do not silently determine Symptom Impact.
- [ ] Anxiety and Agitation are independent clinician entries.
- [ ] “At rest” does not automatically determine J2051B.

### Sections M, N, and Z
- [ ] M1190/M1195/M1200 are designed as one workflow; M1190 does not map to PPS.
- [ ] N0500/N0510/N0520 do not map to BIMS; structured medication evidence plus clinician confirmation is defined.
- [ ] Z0350/Z0400/Z0500 completion, signature, verification, correction, audit, and export rules are defined.

### Design
- [ ] Registry contract and CI validator design are complete.
- [ ] Schema-capability conclusion is issued.
- [ ] Correction/audit model is complete.
- [ ] Historical provenance categories A-G are complete.

### Testing and VUT
- [ ] Stable-ID test matrix covers every applicable item/timepoint/value/skip/trigger/correction/export/audit requirement.
- [ ] VUT plan defines valid and invalid synthetic files for all record types and required edge cases.
- [ ] Expected fatal edits, warnings, and final results are documented.

### Reporting and controls
- [ ] Reports distinguish proposed, designed, implemented, statically verified, tested, runtime verified, and CMS VUT validated.
- [ ] No unexecuted plan is called PASS.
- [ ] Prior incorrect claims remain in correction history.
- [ ] No production code/database/schema/migration/API/UI change occurs in this issue.
- [ ] PR #165 remains blocked.

## Exit gate

This issue closes only when Gates 1-3 are complete, all applicable requirements are resolved or explicitly excluded with owner approval, and owner approval is recorded. Production implementation remains unauthorized until then.
