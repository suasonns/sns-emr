# HOPE Authority Register

Document ID: HOPE-AUTH-001
Version: 1.0
Status: Draft (5 of 11 required sources registered; 6 not yet located)
Owner: Pending owner assignment
Last Verified: 2026-09-29 (live URL fetch of each source below)

## Retrieval-method disclosure (read first)

Every "Official URL" row below was independently re-fetched on the
verification date shown and confirmed to return either the official CMS
page content or a genuine `%PDF-1.x` binary header from `cms.gov` (not a
404, redirect-to-search, or unrelated page). This proves the URLs are
real and current, not fabricated.

**Limitation, disclosed and not glossed over**: the available fetch tool
converts HTML to text but cannot download and persist a PDF binary to
disk. For PDF sources this means the *URL and page-level metadata* (title,
version, dates, described edit changes) are independently verified, but
the **local retained path and SHA-256 of the official PDF binary are NOT
YET achievable** with available tools. Only one CMS PDF (the HOPE v1.01
Admission item-set excerpt, source #5 below) and one extracted plain-text
copy of the Guidance Manual (source #1) are actually present on local
disk with a computable hash. This gap is called out per-row below rather
than claimed as satisfied.

## Source Record 1 — HOPE Guidance Manual

- **Official Title**: Hospice Outcomes and Patient Evaluation (HOPE) Guidance Manual
- **Publisher**: CMS
- **Source Classification**: GUIDANCE MANUAL
- **Version**: v1.02
- **Publication Date**: Not independently confirmed this pass (page does not date-stamp the manual itself)
- **Effective Date**: 2025-10-01
- **Verification Date**: 2026-09-29
- **Official URL**: https://www.cms.gov/files/document/hope-guidance-manual-v1-02.pdf — fetched 2026-09-29, confirmed live (`%PDF-1.7` header returned from cms.gov)
- **Local Retained Path**: `session-state/87bc6586-74b5-4640-8dd0-95d380678bcb/files/hope-pdf-text/guidance_manual.txt` (extracted plain text, 3,665 lines — NOT the original PDF binary)
- **SHA-256**: `a5b3b853a5f09ff8584bd79223d3d5645aff6b98fb37e989e10cd7f36757b846` (of the retained plain-text extract, computed 2026-09-29). This hashes the local text file only — it is **not** the official PDF's own checksum (tool limitation, see disclosure above), so this hash cannot be used to prove the extract matches CMS's published binary, only to detect future tampering/drift of this local copy.
- **Applicable Sections**: A, F, I, J, M, N, Z (all)
- **Applicable Items**: All 45 top-level items + J2051 A-H
- **Mandatory or Explanatory**: MANDATORY — controls item-level clinical completion guidance
- **Supersedes**: Prior HIS (Hospice Item Set) completion guidance for items HOPE replaced, as of 2025-10-01
- **Superseded By**: None known
- **Known Conflicts**: None identified this pass
- **Conflict Resolution**: N/A
- **Notes**: This is the primary source used to derive the corrected Section A (20) / F (4) / I (1) counts and item titles in the Official Item Inventory.

## Source Record 2 — Final HOPE Data Submission Specifications

- **Official Title**: HOPE Data Submission Specifications (FINAL)
- **Publisher**: CMS
- **Source Classification**: TECHNICAL SPECIFICATION
- **Version**: v1.00.1
- **Publication Date**: 2025-04-16 (per CMS HOPE Technical Information page, "HOPE Data Specs (FINAL) Effective October 1, 2025" update dated April 16, 2025)
- **Effective Date**: 2025-10-01
- **Verification Date**: 2026-09-29
- **Official URL**: https://www.cms.gov/medicare/quality/hospice-quality-reporting-program/hope-technical-information — fetched 2026-09-29, confirmed live; page states this version "consists of the following files: HOPE data specs overview (v1.00.1) FINAL 04-05-2025.pdf, HOPE data specs CSV files ... .zip, HOPE data specs HTML files ... .zip, HOPE data specs PDF files ... .zip", packaged as "HOPE Data Specs (v1.00.1) FINAL 04-05-2025.zip" in the page's Downloads section
- **Local Retained Path**: NOT RETAINED — the direct download link is in a CMS "Downloads" widget not resolved by page-text fetch; only the referencing page was retrieved
- **SHA-256**: NOT COMPUTED (file not retained)
- **Applicable Sections**: A, F, I, J, M, N, Z (submission structure, technical edits) — NOT clinical completion guidance (that is Source 1)
- **Applicable Items**: All submitted items
- **Mandatory or Explanatory**: MANDATORY — controls submission structure and fatal/warning technical edits
- **Supersedes**: v1.00.0 DRAFT (2024-10-01)
- **Superseded By**: Errata v1.00.2 (Source 3), then v1.00.3 (Source 4) — errata correct specific edits within v1.00.1, they do not replace the whole document
- **Known Conflicts**: None identified this pass
- **Conflict Resolution**: N/A
- **Notes**: Per the same CMS page, notable v1.00.1 changes vs draft: A0810 (Sex) replaced A0800; new warning edit -3110 (HUV timing rules); new edit -3111 (Z0350 handling for inactivation records) — not yet cross-checked against SNS field implementation this pass.

## Source Record 3 — HOPE Data Specs Errata v1.00.2

- **Official Title**: Hospice Vendor Update and Errata (V1.00.2) for HOPE Data Specs (FINAL)
- **Publisher**: CMS
- **Source Classification**: ERRATA
- **Version**: v1.00.2
- **Publication Date**: 2025-06-24
- **Effective Date**: 2025-10-01 (same as base v1.00.1 — errata rolled in before go-live, not a later cutover)
- **Verification Date**: 2026-09-29
- **Official URL**: https://www.cms.gov/files/document/errata-v1002-hope-data-specs-v1001-final-05-22-2025.pdf — fetched 2026-09-29, confirmed live (`%PDF-1.6` header returned from cms.gov)
- **Local Retained Path**: NOT RETAINED (binary; see disclosure above)
- **SHA-256**: NOT COMPUTED
- **Applicable Sections**: J (J0915 specifically)
- **Applicable Items**: J0915
- **Mandatory or Explanatory**: MANDATORY
- **Supersedes**: The J0915-related skip-edit definitions in v1.00.1 as originally published
- **Superseded By**: v1.00.3 (Source 4) only for the unrelated A1400 edits — the J0915 correction is not stated to be altered by v1.00.3
- **Known Conflicts**: None identified this pass
- **Conflict Resolution**: N/A
- **Notes**: CMS page text (verified 2026-09-29): "The errata document contains three issues (two edit changes, and the addition of caret as an allowed value for item J0915), which address item J0915 not being previously included in two skip pattern edits." This directly confirms the owner's prior directive language ("adds J0915 to applicable skip edits, allows caret for J0915 when skips apply") as independently corroborated CMS text, not merely owner assertion.

## Source Record 4 — HOPE Data Specs Errata v1.00.3

- **Official Title**: Hospice Vendor Update and Errata (V1.00.3) for HOPE Data Specs (FINAL)
- **Publisher**: CMS
- **Source Classification**: ERRATA
- **Version**: v1.00.3
- **Publication Date**: 2026-01-29
- **Effective Date**: 2026-02-18
- **Verification Date**: 2026-09-29
- **Official URL**: https://www.cms.gov/files/document/hope-data-specs-errata-v1-00-3-01-16-2026.pdf — fetched 2026-09-29, confirmed live (`%PDF-1.6` header returned from cms.gov)
- **Local Retained Path**: NOT RETAINED (binary; see disclosure above)
- **SHA-256**: NOT COMPUTED
- **Applicable Sections**: A (A1400 specifically)
- **Applicable Items**: A1400
- **Mandatory or Explanatory**: MANDATORY
- **Supersedes**: The A1400 edit -3083/-3084 definitions in effect since 2025-10-01
- **Superseded By**: None known
- **Known Conflicts**: None identified this pass
- **Conflict Resolution**: N/A
- **Notes**: CMS page text (verified 2026-09-29): "The errata document contains one additional issue, regarding the edits for item A1400: edit -3083 will be removed and edit -3084 will be changed from a FATAL edit to a WARNING edit. These revisions will go into effect on February 18, 2026." Matches the owner's prior directive verbatim.

## Source Record 5 — HOPE Admission Item Set

- **Official Title**: HOPE v1.01 Admission item set (locally retained excerpt)
- **Publisher**: CMS
- **Source Classification**: ITEM SET
- **Version**: v1.01 (note: this is a different version line than the v1.02 Guidance Manual; the version mismatch has NOT been reconciled this pass and is flagged as an open conflict below)
- **Publication Date**: UNVERIFIED (not stated in the retained file itself)
- **Effective Date**: UNVERIFIED
- **Verification Date**: 2026-09-29 (local file confirmed present; not re-fetched from a live CMS URL this pass)
- **Official URL**: NOT RE-VERIFIED THIS PASS — file was retained in a prior session from an unrecorded original URL
- **Local Retained Path**: `session-state/87bc6586-74b5-4640-8dd0-95d380678bcb/files/cms-reference-docs/hope-v1.01_admission.pdf`
- **SHA-256**: `821eac5acb41a03b7b85a94b0c0b1e6a6df1af173832cf609c39738953da9417` (computed 2026-09-29, of the locally retained binary itself — this IS the actual PDF checksum, unlike Sources 2-4 above)
- **Applicable Sections**: Admission-timepoint applicable items only (subset of A/F/I/J/M/N/Z)
- **Applicable Items**: Not yet cross-referenced against the Official Item Inventory
- **Mandatory or Explanatory**: MANDATORY for determining which items are Admission-required vs. excluded
- **Supersedes**: Unknown
- **Superseded By**: Possibly a v1.02-aligned item set not yet located
- **Known Conflicts**: **Version mismatch (v1.01 item set vs. v1.02 Guidance Manual) — UNRESOLVED.** Do not treat this file as authoritative for any item added or changed between v1.01 and v1.02 without independent confirmation.
- **Conflict Resolution**: PENDING — requires locating the current, officially-versioned Admission item set from CMS's HOPE Technical Information downloads
- **Notes**: Retained from an earlier session; provenance of original retrieval (exact URL, exact date) was not recorded at the time and cannot be reconstructed with certainty this pass.

## Sources NOT YET LOCATED (honestly disclosed, not fabricated)

The following six required sources from the owner's list have **not been
located, fetched, or verified** this pass. No URL, date, or content is
asserted for them. They remain open register gaps:

6. **HOPE HUV item set** — NOT LOCATED
7. **HOPE Discharge item set** — NOT LOCATED
8. **HOPE all-item reference** (if officially supplied) — NOT LOCATED; unknown whether CMS publishes this as a single document distinct from the per-timepoint item sets
9. **Current HQRP HOPE measure specifications** — NOT LOCATED
10. **Current HOPE implementation FAQs** — NOT LOCATED
11. **Current CMS VUT materials** — partially identified only: the VUT tool itself is linked from the Technical Information page as `https://iqies.cms.gov/vut` (confirmed present in the page fetch above), but no separate "VUT materials/instructions" document has been located or fetched

## SNS-internal sources (explicitly labeled, not treated as CMS authority)

- `docs/compliance/hope-sfv-guide.md` — **SNS POLICY / internal crosswalk reference only.** Per standing owner rule, never controlling authority for architecture, value sets, or CMS requirements. Used only to identify candidate documentation areas for comparison against Sources 1-5 above.

## Register completeness status

| Required source | Status |
|---|---|
| 1. Guidance Manual v1.02 | REGISTERED — page/version verified live; binary not hashed |
| 2. Data Specs v1.00.1 | REGISTERED — page/version verified live; binary not retained |
| 3. Errata v1.00.2 | REGISTERED — page/version verified live; binary not retained |
| 4. Errata v1.00.3 | REGISTERED — page/version verified live; binary not retained |
| 5. Admission item set | REGISTERED — local file present; SHA-256 pending; version-mismatch conflict open |
| 6. HUV item set | NOT LOCATED |
| 7. Discharge item set | NOT LOCATED |
| 8. All-item reference | NOT LOCATED |
| 9. HQRP measure specifications | NOT LOCATED |
| 10. Implementation FAQs | NOT LOCATED |
| 11. VUT materials | PARTIAL — tool URL only |

**5 of 11 required sources registered. 6 not yet located.** This register
is NOT COMPLETE and must not be reported as satisfying the owner's
"authority package preserved and checksummed" acceptance criterion.
