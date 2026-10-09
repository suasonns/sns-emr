# HOPE Authority Register

Document ID: HOPE-AUTH-001
Version: 1.0
Status: Draft (10 of 11 required sources registered; 1 not located as a
standalone document — see Source Record 7)
Owner: Pending owner assignment
Last Verified: 2026-09-29 (live URL fetch AND binary download of each
downloadable source below)

## Retrieval-method disclosure (read first)

Every "Official URL" row below was independently re-fetched on the
verification date shown and confirmed to return either the official CMS
page content or a genuine `%PDF-1.x` binary header from `cms.gov` or
`qtso.cms.gov` (not a 404, redirect-to-search, or unrelated page). This
proves the URLs are real and current, not fabricated.

**Update from the prior pass**: the earlier-disclosed tool limitation
("the fetch tool cannot persist a PDF binary to disk, so most sources
have no real SHA-256") has been resolved for six sources this pass using
`Invoke-WebRequest` to download the binaries directly, followed by
`Get-FileHash -Algorithm SHA256` and `pypdf` text/metadata extraction
against the downloaded files themselves — not paraphrased search-engine
summaries. Sources 2, 3, and 4 (Data Specs v1.00.1 and its two errata)
remain page-referenced only; their direct download links sit inside a
CMS "Downloads" widget not resolved by page-text fetch, so no binary was
retrieved for them this pass. All downloaded PDF binaries are retained
outside the git repository at
`session-state/87bc6586-74b5-4640-8dd0-95d380678bcb/files/cms-reference-docs/`
(binary CMS reference files are session artifacts, not repository
content, consistent with existing practice for source #5).

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

- **Official Title**: HOPE Admission (ADM) (PDF-embedded document title, confirmed via `pypdf` metadata)
- **Publisher**: CMS
- **Source Classification**: ITEM SET
- **Version**: v1.01 (per CMS file-naming convention `hope-v101admission508c.pdf`; embedded form header reads "ADMISSION TIMEPOINT - HOPE Version 1", decimal truncated by PDF text extraction, filename is the more reliable version indicator)
- **Publication Date**: 2025-03-19 (PDF `/CreationDate` metadata: `D:20250319130331-04'00'`)
- **Effective Date**: 2025-10-01 (per CMS HOPE Technical Information page general HOPE go-live date; the form itself does not print a distinct effective date — OMB expiration field is a literal `XX/XX/XXXX` placeholder in the published PDF)
- **Verification Date**: 2026-09-29 (binary independently re-downloaded from the live CMS URL this pass)
- **Official URL**: https://www.cms.gov/files/document/hope-v101admission508c.pdf — fetched and downloaded 2026-09-29, confirmed live (`%PDF-1.7`, 315,291 bytes)
- **Local Retained Path**: `session-state/87bc6586-74b5-4640-8dd0-95d380678bcb/files/cms-reference-docs/hope-v1.01_admission.pdf` (pre-existing) and `hope_admission_v101.pdf` (freshly downloaded 2026-09-29 for independent verification)
- **SHA-256**: `821eac5acb41a03b7b85a94b0c0b1e6a6df1af173832cf609c39738953da9417` — **the freshly downloaded copy is byte-identical (same hash) to the pre-existing locally-retained file.** This independently confirms the pre-existing file's provenance and integrity, resolving the "provenance of original retrieval not recorded" gap noted in the prior pass.
- **Applicable Sections**: A (Administrative Information — Admission-applicable subset), F, I, J, M, N (Admission-timepoint applicable items only, per the item set's own timepoint column)
- **Applicable Items**: Not yet cross-referenced item-by-item against the Official Item Inventory CSV (a machine cross-check, not a manual claim, is the next required step and is NOT part of this deliverable)
- **Mandatory or Explanatory**: MANDATORY for determining which items are Admission-required vs. excluded
- **Supersedes**: v1.00 Admission item set (`hope-v100admission508c.pdf`, live-confirmed 2026-09-29, SHA-256 `a43b1cba9c2fe24b9ba7687fea25e3924e1127d59f80384c45f1c8d0a1d9b92d`, PDF `/CreationDate` `D:20240726081155-07'00'`) — both versions independently retained for provenance trail; only v1.01 is treated as current
- **Superseded By**: None known (no `hope-v102admission508c.pdf` exists — confirmed 404 on 2026-09-29)
- **Known Conflicts**: See Conflict Audit section below (version-family gap vs. Guidance Manual v1.02)
- **Conflict Resolution**: See Conflict Audit section below
- **Notes**: v1.01 Admission, v1.01 Discharge (Source 6), and v1.01 All Items (Source 8) share the same `/CreationDate` day (2025-03-19), strongly indicating a single coordinated CMS item-set release batch.

## Source Record 6 — HOPE Discharge Item Set

- **Official Title**: HOPE Discharge (DC) (PDF-embedded document title)
- **Publisher**: CMS
- **Source Classification**: ITEM SET
- **Version**: v1.01 (per filename `hope-v101discharge508c.pdf`)
- **Publication Date**: 2025-03-19 (PDF `/CreationDate`: `D:20250319130515-04'00'`)
- **Effective Date**: 2025-10-01 (same basis as Source 5)
- **Verification Date**: 2026-09-29
- **Official URL**: https://www.cms.gov/files/document/hope-v101discharge508c.pdf — fetched and downloaded 2026-09-29, confirmed live (`%PDF-1.7`, 187,052 bytes)
- **Local Retained Path**: `session-state/87bc6586-74b5-4640-8dd0-95d380678bcb/files/cms-reference-docs/hope_discharge_v101.pdf`
- **SHA-256**: `0f3d0b7ca423da6080e95fdbc0cd6e0bee1dcc988e78414709006845f66a431b`
- **Applicable Sections**: Discharge-timepoint applicable items only (subset of A/F/I/J/M/N/Z)
- **Applicable Items**: Not yet cross-referenced against the Official Item Inventory (same caveat as Source 5)
- **Mandatory or Explanatory**: MANDATORY for determining Discharge-required items
- **Supersedes**: v1.00 Discharge item set (`hope-v100discharge508c.pdf`, live-confirmed 2026-09-29, SHA-256 `77c34bb0f7c609aea88b1b1f47415a7255c7ed7ba9b6b7534c41e4ad9571ada5`, PDF `/CreationDate` `D:20240716091134-07'00'`) — both retained for provenance
- **Superseded By**: None known (`hope-v102discharge508c.pdf` not tested this pass — not required since no v1.02 item-set family was found for Admission or All-Item either)
- **Known Conflicts**: See Conflict Audit section below
- **Conflict Resolution**: See Conflict Audit section below
- **Notes**: None beyond Source 5's batch-release observation.

## Source Record 7 — HOPE HUV Item Set

- **Official Title**: NOT LOCATED as a standalone, single-timepoint document
- **Publisher**: N/A
- **Source Classification**: ITEM SET (sought, not found in this form)
- **Version / Publication Date / Effective Date / Official URL / Local Retained Path / SHA-256**: N/A — no such file was found
- **Applicable Sections / Items**: N/A
- **Mandatory or Explanatory**: N/A
- **Supersedes / Superseded By**: N/A
- **Known Conflicts**: N/A
- **Notes**: Two plausible CMS filename patterns were directly tested and both returned HTTP 404 on 2026-09-29: `hope-v100huv508c.pdf` and `hope-v101huv508c.pdf`. No dedicated single-file HUV item set was located on `cms.gov` this pass. **Source 8 below (HOPE All Items v1.01) is the closest independently-verified substitute** — its own embedded title is "HOPE All Items" and it consolidates items across all timepoints, which per its title and the CMS FAQ's timepoint description should include HUV1/HUV2-applicable items — but this is a substitution, not a confirmed equivalent, and is disclosed as such rather than silently treated as satisfying "HUV item set." This gap remains OPEN.

## Source Record 8 — HOPE All Items (used as HUV-content substitute, see Source 7)

- **Official Title**: HOPE All Items (PDF-embedded document title)
- **Publisher**: CMS
- **Source Classification**: ITEM SET
- **Version**: v1.01 (per filename `hope-v101all-item508c.pdf`)
- **Publication Date**: 2025-03-19 (PDF `/CreationDate`: `D:20250319132315-04'00'`)
- **Effective Date**: 2025-10-01 (same basis as Sources 5-6)
- **Verification Date**: 2026-09-29
- **Official URL**: https://www.cms.gov/files/document/hope-v101all-item508c.pdf — fetched and downloaded 2026-09-29, confirmed live (`%PDF-1.7`, 319,395 bytes)
- **Local Retained Path**: `session-state/87bc6586-74b5-4640-8dd0-95d380678bcb/files/cms-reference-docs/hope_all_item_v101.pdf`
- **SHA-256**: `e1384c7344356f9009b9cf6268432164d25e3a3bd0dddd5009c57f7f1dcf65b1`
- **Applicable Sections**: All (A, F, I, J, M, N, Z) — consolidated reference across all timepoints
- **Applicable Items**: All 45 top-level + 8 J2051 subitems, per its own title — not yet field-by-field cross-checked against the Official Item Inventory
- **Mandatory or Explanatory**: MANDATORY for determining HUV-applicable items (substitute source; see Source 7 caveat)
- **Supersedes**: Presumably a v1.00 All-Item equivalent; no `hope-v100all-item508c.pdf` was tested this pass
- **Superseded By**: None known
- **Known Conflicts**: See Conflict Audit section below
- **Conflict Resolution**: See Conflict Audit section below
- **Notes**: OMB control number printed in this file (`0938-1153`) matches the number printed in Source 5's file, confirming both are genuine parts of the same OMB-approved HOPE collection instrument, not unrelated documents.

## Source Record 9 — Current HQRP HOPE Measure Specifications

- **Official Title**: Hospice Quality Reporting Program Quality Measure Specifications User's Manual, Version 1.03 (exact PDF-embedded title, confirmed via `pypdf` metadata and page-1 text)
- **Publisher**: CMS
- **Source Classification**: QUALITY-MEASURE SPECIFICATION
- **Version**: v1.03
- **Publication Date**: UNVERIFIED (not distinctly printed from the effective date on page 1; PDF `/CreationDate` is `D:20250514101626-04'00'`, treated as a lower-confidence proxy for publication date, not asserted as the actual publication date)
- **Effective Date**: 2025-10-01 (printed verbatim on the cover page: "Version 1.03 — Effective October 1, 2025")
- **Verification Date**: 2026-09-29
- **Official URL**: https://www.cms.gov/files/document/hqrp-qm-users-manual-v103-hope508.pdf — fetched and downloaded 2026-09-29, confirmed live (`%PDF-1.7`, 1,003,223 bytes, 51 pages)
- **Local Retained Path**: `session-state/87bc6586-74b5-4640-8dd0-95d380678bcb/files/cms-reference-docs/hqrp_qm_users_manual_v103.pdf`
- **SHA-256**: `06a862f803d072db00aadbacd5a30b5e8aa9167a0bd454f69d444a797ad8488a`
- **Applicable Sections**: Quality-measure calculation logic drawing on HOPE-sourced items (not yet mapped item-by-item this pass)
- **Applicable Items**: UNVERIFIED which specific HOPE items feed which measures — requires a dedicated trace, out of scope for this deliverable
- **Mandatory or Explanatory**: MANDATORY — controls HQRP measure calculation, numerator/denominator definitions, and public-reporting rules
- **Supersedes**: An earlier HQRP measure-specifications document dated November 2023 (`hqrp-current-measuresnov2023.pdf-0`, independently confirmed live 2026-09-29 but not downloaded — predates HOPE's 2025-10-01 go-live and is superseded for any HOPE-sourced measure)
- **Superseded By**: None known
- **Known Conflicts**: See Conflict Audit section below
- **Conflict Resolution**: See Conflict Audit section below
- **Notes**: This document has NOT yet been cross-checked against Section J/M/N item definitions for measure-calculation dependencies (e.g., which J2051 codes feed which HOPE-based quality measure). That trace is a distinct, not-yet-authorized deliverable.

## Source Record 10 — Current CMS HOPE FAQ

- **Official Title**: HOPE Implementation Frequently Asked Questions (FAQs) (PDF-embedded document title)
- **Publisher**: CMS, Hospice Quality Reporting Program
- **Source Classification**: FAQ/TRAINING CLARIFICATION
- **Version**: Not separately version-numbered in the document (no "vX.XX" string found in the title or table of contents)
- **Publication Date**: 2025-07-31 (PDF `/CreationDate`: `D:20250731092601-04'00'`, treated as a reasonable proxy; not explicitly printed as a "publication date" in the document body)
- **Effective Date**: N/A — explanatory document, not itself an effective-dated requirement
- **Verification Date**: 2026-09-29
- **Official URL**: https://www.cms.gov/files/document/hope-implementation-faqs.pdf — fetched and downloaded 2026-09-29, confirmed live (`%PDF-1.6`, 241,129 bytes, 11 pages)
- **Local Retained Path**: `session-state/87bc6586-74b5-4640-8dd0-95d380678bcb/files/cms-reference-docs/hope_faq_implementation.pdf`
- **SHA-256**: `c55f4a29f81c1bde2b27f8f93a8f6226edfdd949096cc25b15db2514d1d4f9c2`
- **Applicable Sections**: General (HIS-to-HOPE transition, submission, timepoints, SFVs, vendor/iQIES, reports, HQRP compliance, public reporting — per its own table of contents)
- **Applicable Items**: General guidance, not item-specific per its table of contents
- **Mandatory or Explanatory**: EXPLANATORY — per the constitution's authority hierarchy, this FAQ clarifies but does not override the Guidance Manual or Data Specs
- **Supersedes**: An older, differently-named "HOPE Frequently Asked Questions" document dated December 2019 (`hope-faqfinaldecember-2019.pdf`, identified via search but NOT independently fetched/downloaded this pass — predates HOPE's 2025 implementation entirely and is presumed superseded, not confirmed)
- **Superseded By**: None known
- **Known Conflicts**: See Conflict Audit section below
- **Conflict Resolution**: See Conflict Audit section below
- **Notes**: Table of contents includes a dedicated "Symptom Follow-up Visits (SFVs)" section (page 6) — directly relevant to the still-blocked J2051/J2052/J2053 remediation and should be read in full before that remediation is ever authorized.

## Source Record 11 — Current CMS VUT Instructions

- **Official Title**: Assessment Submitter User Manual (cover title: "CMS iQIES Assessment Management User Manual — Assessment Management Version 2.2 — Assessment Submitter")
- **Publisher**: CMS / iQIES (Internet Quality Improvement & Evaluation System)
- **Source Classification**: TECHNICAL SPECIFICATION (submission/vendor-testing workflow, not a HOPE item/value specification)
- **Version**: v2.2
- **Publication Date**: 2025-10-28 (printed verbatim on the cover page: "Version 2.2 — October 28, 2025")
- **Effective Date**: 2025-10-28 (same as publication date; no separate effective date printed)
- **Verification Date**: 2026-09-29
- **Official URL**: https://qtso.cms.gov/system/files/qtso/iQIES%20Assessment%20Managment%20Manual%20for%20Assessment%20Submitter%20v2.2%20FINAL%2010.28.25_508.pdf — fetched and downloaded 2026-09-29, confirmed live (`%PDF-1.6`, 2,074,975 bytes, 34 pages)
- **Local Retained Path**: `session-state/87bc6586-74b5-4640-8dd0-95d380678bcb/files/cms-reference-docs/iqies_assessment_submitter_manual_v2.2.pdf`
- **SHA-256**: `0ac09a07133a9cb733cedf9af50a5a3f34c4cbd4e6c7a689c2b89e939097fd0d`
- **Applicable Sections**: Submission workflow, not clinical item content — applies to all sections' exported records
- **Applicable Items**: N/A (workflow/tooling document, not item-level)
- **Mandatory or Explanatory**: MANDATORY for vendor test-file submission and Final Validation report interpretation
- **Supersedes**: Any prior version of this manual (version history not independently checked this pass)
- **Superseded By**: None known
- **Known Conflicts**: None identified this pass
- **Conflict Resolution**: N/A
- **Notes**: **Directly confirmed via full-text extraction** (not inferred): the document contains "Appendix B: Validation Utility Tool (VUT)" (page 27-28 per its own table of contents), including the literal instruction "Go to https://iqies.cms.gov/vut" — this is genuine primary-source VUT usage documentation, not a paraphrase. This is the authoritative source the not-yet-authorized VUT Test File Plan execution (Gate 3) must be built against.

## SNS-internal sources (explicitly labeled, not treated as CMS authority)

- `docs/compliance/hope-sfv-guide.md` — **SNS POLICY / internal crosswalk reference only.** Per standing owner rule, never controlling authority for architecture, value sets, or CMS requirements. Used only to identify candidate documentation areas for comparison against Sources 1-11 above.

## Conflict Audit

For each newly added source (6-11) this pass, per owner's required format:

- **Source 6 (Discharge Item Set v1.01)**: CONFLICTS WITH EXISTING REGISTER ENTRY
  - **Competing text**: Source 6 is versioned v1.01 (filename + creation-date evidence); Source 1 (Guidance Manual) is versioned v1.02.
  - **Controlling source**: NOT DETERMINED. The most likely explanation — that CMS increments the Guidance Manual's version number for narrative/clarification updates independently of the Item Set's version number, which only changes when the actual data-collection fields change — is a **plausible hypothesis, not a CMS-confirmed fact**. No CMS crosswalk or version-correspondence table has been located that states this explicitly.
  - **Effective dates**: Both carry the same 2025-10-01 effective date basis (Item Set per general HOPE go-live; Guidance Manual per its own page).
  - **Resolution**: UNRESOLVED. Treat the Item Set (structure/fields) as authoritative for what fields exist, and the Guidance Manual (v1.02) as authoritative for how to complete them, until CMS publishes an explicit version-correspondence statement or a v1.02-versioned Item Set is located. Same conflict and same resolution apply to Source 5 (Admission) and Source 8 (All Items) — all three share the v1.01 item-set / v1.02 guidance-manual gap.

- **Source 7 (HUV Item Set)**: N/A — source not located, no text to compare.

- **Source 9 (HQRP Measure Specifications v1.03)**: NONE identified this pass. Domain does not overlap with item-level clinical guidance; no contradictory statement found. **Not yet exhaustively cross-checked** against Sections J/M/N item definitions — absence of a found conflict is not proof of no conflict.

- **Source 10 (HOPE FAQ)**: NONE identified this pass, same caveat as Source 9 — this FAQ has not yet been read in full against the Guidance Manual for contradictions; only its table of contents was reviewed. Its SFV section (page 6) is a candidate for a future dedicated conflict check before any J2051/J2052/J2053 remediation is authorized.

- **Source 11 (VUT Instructions v2.2)**: NONE identified this pass. Distinct domain (submission/vendor-testing workflow vs. clinical item content).

## Register completeness status

| Required source | Status |
|---|---|
| 1. Guidance Manual v1.02 | REGISTERED — page/version verified live; binary not hashed |
| 2. Data Specs v1.00.1 | REGISTERED — page/version verified live; binary not retained |
| 3. Errata v1.00.2 | REGISTERED — page/version verified live; binary not retained |
| 4. Errata v1.00.3 | REGISTERED — page/version verified live; binary not retained |
| 5. Admission item set | REGISTERED — binary downloaded and hashed; version-family conflict open (see Conflict Audit) |
| 6. Discharge item set | REGISTERED — binary downloaded and hashed; same version-family conflict open |
| 7. HUV item set | NOT LOCATED as a standalone document — see Source Record 7 |
| 8. All-item reference (HUV substitute) | REGISTERED — binary downloaded and hashed; same version-family conflict open |
| 9. HQRP measure specifications | REGISTERED — binary downloaded and hashed |
| 10. Implementation FAQs | REGISTERED — binary downloaded and hashed |
| 11. VUT instructions | REGISTERED — binary downloaded and hashed; VUT content directly confirmed via full-text search |

**10 of 11 required sources registered with downloaded, hashed binaries.
1 (a standalone HUV item set) is NOT LOCATED and is substituted with a
disclosed, lower-confidence alternative (Source 8).** The version-family
gap between v1.01 item sets and the v1.02 Guidance Manual remains
UNRESOLVED and must not be silently assumed compatible. This register is
substantially, but not completely, populated and must not be reported as
fully satisfying the owner's "authority package preserved and
checksummed" acceptance criterion until the HUV gap and version-family
conflict are closed.
