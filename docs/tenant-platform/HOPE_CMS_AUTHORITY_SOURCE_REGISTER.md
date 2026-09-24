# HOPE CMS Authority Source Register

Evidence labels used in this document follow the SNS Review Rule:
`VERIFIED BY CMS` / `VERIFIED BY REPOSITORY TRACE` / `VERIFIED BY PRODUCTION CODE` /
`NOT_VERIFIED` / `OPEN QUESTION` / `REQUIRES ROMEL DECISION`.

## Status

Current CMS HOPE version:
**HOPE Guidance Manual v1.02 — VERIFIED BY CMS**

Current effective date:
**October 1, 2025 — VERIFIED BY CMS**

Repository copy present:
**NO** (policy decision below — URLs, versions, dates, and checksums retained instead)

Last verified: **2026-09-24**
Verified against commit: `1955016` (this register is added on the forward commit created immediately after this verification)

## Official Sources

### Source 1 — HOPE Guidance Manual v1.02

- Official title: *Hospice Outcomes and Patient Evaluation (HOPE) Guidance Manual*
- Issuer: Centers for Medicare & Medicaid Services (CMS), Hospice Quality Reporting Program (HQRP)
- Version: v1.02
- Publication/revision date: printed on cover/footer of every page as "HOPE Guidance Manual v1.02 Effective October 1, 2025"
- Effective date: **October 1, 2025** (unchanged from v1.01 — v1.02 is a corrective/clarifying revision, not a new implementation period)
- Official URL: `https://www.cms.gov/files/document/hope-guidance-manual-v1-02.pdf`
  - Retrieved directly from the `cms.gov` domain via HTTP GET on 2026-09-24; response was a valid 138-page PDF (`%PDF-1.7` header confirmed).
- Repository path, if retained: none (see Repository Gaps / Restrictions)
- SHA-256 checksum (of the file downloaded and inspected on 2026-09-24, retained only in this verification record, not committed): `9A6D058F047C2516B347F80686E0143A0F3566ABA680D4439DBFFA2E7766ABBC`
- Scope: full HOPE item set instructions (Admission, HUV1, HUV2, Discharge), Sections A–M, coding tips, examples, definitions
- Mandatory or advisory status: Mandatory — CMS-required assessment instrument under the Hospice Quality Reporting Program, effective for all patient admissions on/after October 1, 2025
- Supersedes: HOPE Guidance Manual v1.01 (effective October 1, 2025 — same date; v1.02 corrects/clarifies v1.01 text, it does not change the collection start date)
- Superseded by: none identified as of verification date
- Items relevant to SNS: I0010 (p.55), Section J (J0050–J2053) (p.56–75+), full Admission/HUV/Discharge item sets
- Evidence status: **VERIFIED BY CMS**
- Verification date: 2026-09-24

### Source 2 — HOPE v1.01 to v1.02 Guidance Manual and Item Set Change Table

- Official title: *HOPE v1.01 to HOPE v1.02 Guidance Manual and Item Set Change Table*
- Issuer: CMS, HQRP
- Version: covers the v1.01→v1.02 transition, "Effective October 1, 2025"
- Publication/revision date: not separately dated on the document beyond the effective-date banner
- Effective date: October 1, 2025
- Official URL: `https://www.cms.gov/files/document/hope-v1-01-1-02-guidance-manual-item-set-change-table.pdf`
  - Retrieved directly from the `cms.gov` domain via HTTP GET on 2026-09-24; response was a valid 4-page PDF (`%PDF-1.6` header confirmed).
- Repository path, if retained: none
- SHA-256 checksum (verification-only, not committed): `AF3C052ED33ECCAECA553ABAF6C7C4D86D3E043F95B69552B49057F4CFEFDA21`
- Scope: itemized list of every textual change between v1.01 and v1.02
- Mandatory or advisory status: Advisory reference document (not itself a collection instrument)
- Supersedes: n/a
- Superseded by: none identified
- Items relevant to SNS: J2052 (item text), J2053 (item-specific instructions, coding tips, example rationale)
- Evidence status: **VERIFIED BY CMS**
- Verification date: 2026-09-24

### Source 3 — CMS HOPE program page

- Official title: *HOPE* (Hospice Outcomes and Patient Evaluation program page)
- Issuer: CMS
- Official URL: `https://www.cms.gov/medicare/quality/hospice/hope`
- Scope: program background, finalization citation (FY 2025 Hospice Wage Index Final Rule, CMS-1810-F), October 1, 2025 collection start date, HUV1/HUV2 timepoint overview
- Evidence status: **VERIFIED BY CMS**
- Verification date: 2026-09-24 (content confirmed present and consistent with the manual's own effective-date banner)

### Rejected candidate URL (documented for audit trail)

- `https://www.cms.gov/files/document/hope-guidance-manual-v102.pdf` — returned HTTP 404 on direct fetch on 2026-09-24. This URL pattern was surfaced by an AI web-search summary and is **not a valid CMS source**. It is recorded here only so a future reviewer does not re-cite it. The correct, verified URL uses hyphenated version segments: `hope-guidance-manual-v1-02.pdf`.

## Version Determination

- v1.01 status: **VERIFIED BY CMS** — superseded (see change table)
- v1.02 status: **VERIFIED BY CMS** — operative
- Operative version: **v1.02**
- Effective period: October 1, 2025 forward (both v1.01 and v1.02 share this effective date; CMS's own footer explicitly states the version/footer text was corrected — "Updated footer to correct version number" — meaning v1.01 material in circulation after the correction was already superseded in substance, not just cosmetically)
- v1.02 supersedes v1.01: **YES — VERIFIED BY CMS** (row 1–2 of the change table: cover page and footer explicitly updated "to correct version number")
- Unresolved version questions: none identified for v1.01→v1.02. Whether a v1.03 or later exists was not searched beyond confirming no such reference appears on the current CMS HOPE program page as of the verification date — **NOT_VERIFIED** for any version beyond v1.02.

## Complete v1.01→v1.02 Change Table Contents (VERIFIED BY CMS, full enumeration — 7 rows, all in Section J)

| # | Section/Item | What changed | SNS-relevant? |
|---|---|---|---|
| 1 | Cover page | "HOPE v1.01" → "HOPE – v1.02" (version number correction) | No (cosmetic) |
| 2 | All footers | "HOPE v1.01 Effective October 1, 2025" → "HOPE Guidance Manual – v1.02 Effective October 1, 2025" | No (cosmetic) |
| 3 | J2053 Item-Specific Instructions | Wording only: "assessment of" → "determination of"; "clinical judgment" → "and/or clinical judgment"; explicit note that RN **or LPN/LVN** may conduct SFV symptom-impact follow-up | Yes — LPN/LVN role clarification is relevant to SFV completion actor tracking |
| 4 | J2053 Coding Tips | Wording only: adds "observations and/or" before "clinical judgment" / "clinical assessment" | No functional change |
| 5 | J2053 Example Rationale | Wording only, no coding/skip-pattern change | No |
| 6 | J2052 item text | Adds the word "impact" to "for any moderate or severe pain of non-pain symptom **impact**" | No functional/coding change — text clarity only |
| 7 | J2053 stem text | Adds "observations and/or" before "clinical assessment" in the item stem | No functional change |

**Conclusion — VERIFIED BY CMS**: The v1.01→v1.02 change table contains **zero changes to response codes, skip patterns, timepoints, or roles for J2052, J2052A, J2052B, J2052C, or J2053**. Every change is wording/clarity only. **J2052C's four response codes (1/2/3/9) and its skip target (M1190, Skin Conditions) are textually identical in both versions.** The manual body confirms this: J2052A/B/C code text captured directly from the v1.02 manual (p.73) reads:

> A. Was an in-person SFV completed?
> &nbsp;&nbsp;0. No — Skip to J2052C. Reason SFV Not Completed.
> &nbsp;&nbsp;1. Yes
>
> C. Reason SFV Not Completed – Skip to M1190, Skin Conditions.
> &nbsp;&nbsp;1. Patient and/or caregiver declined an in-person visit.
> &nbsp;&nbsp;2. Patient unavailable (e.g., in ED, hospital, travel outside of service area, expired).
> &nbsp;&nbsp;3. Attempts to contact patient and/or caregiver were unsuccessful.
> &nbsp;&nbsp;9. None of the above.

**J2050, J2051, and I0010 do not appear anywhere in the change table** — this means, per CMS's own documentation, they are **unchanged** between v1.01 and v1.02. This has been independently cross-checked by extracting and reading the full v1.02 manual text for both items directly (not inferred solely from change-table silence):

- **I0010. Principal Diagnosis** (v1.02 manual, p.55, Timepoint: Admission only): "The principal diagnosis is defined as the condition established after reviewing all available information to be chiefly responsible for the patient's admission... This item should be completed based on the patient's principal diagnosis **at the time of admission to hospice**... Item completion must be based on what is indicated in the clinical record. Do not use sources external to the clinical record." Single-select coded response (e.g., 01=Cancer, 02=Dementia, 06/07=split cardiac codes, 99=None of the above).
- **J2050. Symptom Impact Screening** (v1.02 manual, p.73–74, Timepoints: ADM, HUV1, HUV2): "A. Was a symptom impact screening completed? — Code 0, No... and Skip to Item M1190... Code 1, Yes, if the patient was screened for symptom impact. B. Date of symptom impact screening — Enter the date the symptom impact screening was performed." This is the **exact two-operand structure** (a completion Boolean, item A, and a completion date, item B) that the repository's OR-fallback finding concerns.

## Item Authority Map

| CMS Item | Manual Page | Timepoint(s) | v1.01→v1.02 changed? |
|---|---|---|---|
| I0010 | p.55 | ADM only | No |
| J2050 | p.73–74 | ADM, HUV1, HUV2 | No |
| J2051 | p.74 | ADM, HUV1, HUV2 | No |
| J2052A | p.73 (change table row 6) | ADM, HUV1, HUV2 | Wording only |
| J2052B | p.73 | ADM, HUV1, HUV2 | No |
| J2052C | p.73 | ADM, HUV1, HUV2 | No (codes/skip unchanged) |
| J2053 | p.75 (change table rows 3–5,7) | ADM, HUV1, HUV2 | Wording only |
| Admission item set | full manual, ADM-tagged items | ADM | Per-item, mostly unchanged |
| HUV1 item set | full manual, HUV1-tagged items | HUV1 | Per-item, mostly unchanged |
| HUV2 item set | full manual, HUV2-tagged items | HUV2 | Per-item, mostly unchanged |
| Discharge item set | full manual, DC-tagged items | Discharge | **NOT_VERIFIED** — Discharge-tagged item pages were not individually re-extracted in this pass; only I0010/J2050/J2052x/J2053 were directly read from the manual text |
| Submission specifications | not retrieved | n/a | **NOT_VERIFIED** — no HOPE Data Submission Specifications document was retrieved or reviewed this pass |
| Validation specifications | not retrieved | n/a | **NOT_VERIFIED** — no HOPE Validation Specifications document was retrieved or reviewed this pass |

## Repository Gaps

The following official CMS materials are required for full item-set authority coverage but are **not** stored, indexed, or fully reviewed in this repository:

- HOPE Data Submission Specifications (not retrieved this pass)
- HOPE Validation Specifications, if separately published (not retrieved this pass)
- Full Discharge item-set page-by-page text (only cross-referenced via table of contents; individual item pages not re-extracted this pass)
- Any CMS errata/correction notices issued after v1.02 (not searched beyond the current CMS HOPE program page, which shows no such notice as of verification date)

## Restrictions

- CMS authority determines **what CMS requires**. It does not determine **where or how SNS stores, captures, or attributes** that data — SNS storage/ownership decisions remain product decisions requiring Romel's authorization (see `J2052C_DECISION_RECORD.md`, `I0010_PRINCIPAL_DIAGNOSIS_PROVENANCE_TRACE.md`).
- Test results and production-code traces prove SNS repository behavior. They do not, by themselves, prove CMS compliance — CMS compliance additionally requires that the SNS behavior correctly implements the cited CMS rule, which is a separate verification not fully completed for every item in this pass.
- No production implementation, schema change, or clinical workflow change is authorized by the creation of this register.

## Repository Storage Policy Decision

This repository does not currently store any PDF documents anywhere under `docs/` (confirmed via `git ls-files | Select-String "\.pdf$"` — zero matches) and has no `.gitattributes` entry configured for binary/PDF handling. Per the CMS manual's own copyright/reproduction posture (a full federal guidance manual, hundreds of KB, with CMS branding and formatting), this register **does not store the PDFs in-repository**. Instead it retains:

- exact official URLs (independently verified live via direct HTTP fetch on 2026-09-24)
- version numbers and effective dates
- SHA-256 checksums of the files as retrieved during this verification (for future reproducibility/diffing against a re-download, not for repository storage)
- item-level page citations and verbatim short excerpts (fair-use-scale quotations only, not full-manual reproduction)

This is a documentation-only decision; it does not require a Romel decision to reverse but should be revisited if the team decides authoritative source PDFs must be vendored into the repository for offline/air-gapped audit purposes.
