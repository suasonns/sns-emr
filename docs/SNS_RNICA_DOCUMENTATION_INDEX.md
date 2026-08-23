# SNS RNICA Documentation Index

Authoritative index of all RNICA governance/design documents recovered from an
untracked, gitignored subfolder (`copilot-worktrees/...`) and committed into
`C:\dev\SNS EMR\docs\`. Status classification is derived from explicit
statements found inside each document — precedence is not inferred from
filenames or version numbers alone.

## Controlling precedence (explicit, quoted from source)

`SNS_RNICA_MASTER_MAP_1.1.md` line 42: **"Version 1.1 supersedes the
lightweight Section 1-12 descriptions from Version 1.0 below."** This is a
self-declared supersession inside the controlling document itself, not an
inference. `SNS_RNICA_MASTER_MAP_1.0.md` remains present for historical
traceability only, per the existing `SNS_RNICA_SECTION_1_IMPLEMENTATION_CONTRACT.md`
document (already committed, not part of this recovery), which independently
records the same conclusion in its own precedence table.

## Index

| File | Version | Status | Superseded by | Purpose | SHA-256 |
|---|---|---|---|---|---|
| SNS_RNICA_MASTER_MAP_1.1.md | 1.1 | CONTROLLING | — | Complete, unabridged RN ICA build specification (Global Facesheet Frame, Sections 1-12 full clinical detail, Admission Action Center, navigation behavior, Definition of Done). Confirms its own controlling status at line 42. | 8CF9F5EE24602A8D189FF4BA5A2FC7D3CAFD3AF094A0D289661CC302E22C79EB |
| SNS_RNICA_MASTER_MAP_1.0.md | 1.0 | SUPERSEDED | SNS_RNICA_MASTER_MAP_1.1.md | Original lightweight Section 1-12 descriptions plus Master Sync Rules, Admission Action Center summary, Dependency Flow, Parallel Workflow, and Status/Next Steps — the latter sections are explicitly preserved unmodified as an addendum inside 1.1, so 1.0 is kept only for historical traceability of the addendum provenance. | AC4CF193A0C12DFA5F3BA2C9A8EFC2C55C23A5F4C9496D9E4F16B0CEFCB5D1F2 |
| SNS_RNICA_MASTER_MAP_MAPPING_2.0.md | 2.0 | SUPPORTING | — | Phase 2 Step 1 field-to-section mapping (e.g., Patient Demographics → Section 1). Frozen; not superseded. | BD9B5EE9261AA4E5F47DC693FCAD2E04EFE6C35A0AE01E519770E63BF40A1039 |
| SNS_RNICA_BUILD_SEQUENCING_2.0.md | 2.0 | SUPPORTING | — | **Governs build sequencing.** Defines the dependency-ordered build sequence (Sequence 1 Foundational, Sequence 2 Section Architecture Migration, etc.) referenced throughout this session's implementation-order decisions. | 12C5613AE79CF9B69280EFE392A7D9F5EE5C82752D80B198C2DA77714C1D4209 |
| SNS_RNICA_GAP_VALIDATION_2.0.md | 2.0 | SUPPORTING | — | The 19-item validated gap baseline (9 HOPE-derivation + 10 non-HOPE structural) used as the finite completion-ledger scope this session. | 6BC5B95C8A44D8E798FB3410397D18F5904442FCB1CFF108FA0563C6EC6E162D |
| SNS_RNICA_FIELD_INVENTORY_1.0.md | 1.0 | SUPPORTING | — | **Governs field mapping.** Full field-by-field inventory (field name, type, requiredness, source) referenced for Section 1 and finalization field contracts. | AFF2E478CA547B2E3E29FA104DAC9BCD352A7972D06F7009ABB16EBD2FB47A11 |
| SNS_RNICA_API_MAPPING_1.0.md | 1.0 | SUPPORTING | — | **Governs API mapping.** Maps Master Map requirements to existing backend endpoints/services. | EED3F05F34FBBFAF68F2088669BAFED82F907FE1C4C2172A4E4A354B18BB4F6C |
| SNS_RNICA_DATABASE_MAPPING_1.0.md | 1.0 | SUPPORTING | — | **Governs database mapping.** Maps Master Map fields/sections to ORM models, tables, and migrations. | 844C298CD44EC50AA43D0089BE022100FA8D004B98F23562EB81FF48ED7143A4 |
| SNS_RNICA_SECTION_INVENTORY_1.0.md | 1.0 | SUPPORTING | — | Per-section implementation status inventory (Implemented / Partial / Missing / Deprecated), largest document (200KB); cross-checked against live code this session and found partially stale (see Gap Validation 2.0 for the corrected baseline). | 0D50C39C2502DE8E4A11783852BBDBB588566E4088DD8CB9036945F12871D531 |
| SNS_RNICA_VALIDATION_INVENTORY_1.0.md | 1.0 | SUPPORTING | — | **Governs validation.** Catalog of required field-level and section-level validation rules. | D616897256B17CB009EC18C2DFFAE1D3ACEAE78125CBA0E36479B04EA495DBE6 |
| SNS_RNICA_AUDIT_INVENTORY_1.0.md | 1.0 | SUPPORTING | — | **Governs audit behavior.** Defines required audit-trail fields/events (created_by, updated_by, locked_by, amendment/correction events). | 660927DFBE64F40EA8EBC631CF87F05F467BDFF39737687D3ECEAC93748A4BE9 |
| SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0.md | 1.0 | SUPPORTING | — | **Governs narrative sources.** Enumerates the documented source fields a generated clinical narrative must draw from. | 240D40561AE7194498009ACC14DE11D2F3676000F7481ECE34881CFFB1028D86 |
| SNS_RNICA_HOPE_CROSSWALK_VERIFICATION_2.0.md | 2.0 | SUPPORTING | — | Verifies HOPE item crosswalk coverage against CMS HOPE guidance. | B650D497CBD3F3E8CE15C9914B2253C7D1514B9F19ED938E494DDAC3ACB55FC1 |
| SNS_ACTION_CENTER_TRIGGER_INVENTORY_1.0.md | 1.0 | SUPPORTING | — | **Governs Action Center triggers.** Defines the intended finding→trigger rule inventory for the Admission Action Center (confirmed this session: manual POST triggers exist and are wired to RNICA; the automatic rule-engine described here has no caller yet — PARTIAL). | 142794F1F9956B818602E684D66C6972C7F889332055BDB974751E11558E029F |
| SNS_POC_GENERATION_MATRIX_1.0.md | 1.0 | SUPPORTING | — | **Governs POC generation.** Defines the finding→problem/goal/intervention/discipline/frequency generation rule matrix (confirmed this session: `poc_generation_service.py` implements this matrix, but `generate_and_apply_poc_from_assessment()` has zero callers — PARTIAL/dead code). | 5BA2A774CE948D4C46FC0200EF3CD305BE83C6A35CDF08BB3702910F47659E56 |
| SNS_POC_EVIDENCE_INVENTORY_1.0.md | 1.0 | SUPPORTING | — | Defines the evidence-linkage contract between assessment findings and POC problems (confirmed this session: `rnica_poc_adapter.py` + `rnica_poc.py` implement manual/linked evidence — EXISTS AND WIRED). | 57EAE117A4F5745FB38ADB87922BE560B6A5AA424874F647993D1903F7F701BF |
| SNS_DESIGN_SYSTEM_1.0.md | 1.0 | SUPPORTING | — | UI design tokens, spacing, sizing hierarchy (Level 1-4 zones) referenced for Section 1 Care Team grid alignment. Does not specify keyboard/ARIA/breakpoint/density requirements — those are engineering discretion, not governed. | 85625410480CCF5D198651A9CD22BA9318F61C34246ADB867EBBC560734F6275 |
| SNS_HOPE_HARVEST_RECONCILIATION_1.0.md | 1.0 | SUPPORTING | — | Reconciles which HOPE items are in-scope vs explicitly out-of-scope for RNICA (e.g., A0600 SSN/Medicare identifiers confirmed out of RNICA scope, sourced from Facesheet/Payer instead). | 843979C03D915FE9F67651DDB4179AEC31D5328DBA381733D33D5734AF23520B |
| SNS_IMPLEMENTATION_GAP_REPORT_1.0.md | 1.0 | HISTORICAL | — | Earlier gap report; superseded in practice by SNS_RNICA_GAP_VALIDATION_2.0.md as the active baseline, but kept for historical traceability (no explicit supersession statement found in-document, so it is not marked SUPERSEDED). | CC14C2CA75E1203A7B1550D5CD1272B12FEECEF283E761FA4512C25585BFC94F |
| SNS_MIGRATION_COMPLEXITY_RATINGS_1.0.md | 1.0 | SUPPORTING | — | Rates the migration/implementation complexity of remaining Master Map items; used for sequencing risk assessment. | A98D9204F1534BC4887805AF4333C35125BD5D19CE5B975A86331B9DAA89AEEF |
| rnica-poc-lock-no-autogen-disposition.md | n/a | SUPPORTING | — | Decision record: POC does not auto-generate on assessment lock; generation requires an explicit clinician-triggered action. Directly explains why `generate_and_apply_poc_from_assessment()` has no callers (see SNS_POC_GENERATION_MATRIX_1.0.md row above) — this is a deliberate disposition, not a defect. | 3C88C3F1709F220F942310020A7F3F51EDFF01E107A6B856652B29AE5C224438 |

## Dependency order (per SNS_RNICA_BUILD_SEQUENCING_2.0.md)

1. Foundational (Section Architecture Migration)
2. Field/API/Database mapping alignment (FIELD_INVENTORY, API_MAPPING, DATABASE_MAPPING)
3. Validation rules (VALIDATION_INVENTORY)
4. Section-by-section implementation (SECTION_INVENTORY, GAP_VALIDATION 2.0 as corrected baseline)
5. Action Center trigger wiring (ACTION_CENTER_TRIGGER_INVENTORY)
6. POC generation + evidence linkage (POC_GENERATION_MATRIX, POC_EVIDENCE_INVENTORY, rnica-poc-lock-no-autogen-disposition)
7. Narrative generation (NARRATIVE_SOURCE_INVENTORY)
8. Finalization, audit, and lock behavior (AUDIT_INVENTORY)

## Not included in this recovery/index

`docs/_tmp_hope/admission.txt`, `all_items.txt`, `sfv_guide.txt` — scratch
working notes, not authoritative documents. Preserved only at
`C:\dev\SNS-EMR-RECOVERY\governance-docs\_tmp_hope\`, not committed.
