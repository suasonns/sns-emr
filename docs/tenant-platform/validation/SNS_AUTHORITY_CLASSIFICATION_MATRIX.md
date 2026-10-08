# SNS Authority Classification Matrix

**Document ID:** SNS-GOV-AUTHORITY-001
**Status:** Product governance baseline, pending legal/compliance confirmation where marked
**Jurisdictions:** United States federal Medicare hospice; California hospice agencies; SNS internal product and operational policy
**Verification date:** October 8, 2026

## Classification key

- **Binding Federal Requirement**: Federal statute or regulation applicable within its stated scope.
- **Binding California Requirement**: California statute or regulation applicable to California hospice agencies within its stated effective period.
- **Medicare/CMS Guidance**: CMS manual, model form, survey guidance, or MAC/LCD guidance. Binding effect depends on the specific source and context.
- **SNS Product Policy**: A product design decision adopted by SNS, not represented as law.
- **SNS Operational Policy**: An agency-configurable operating control implemented by SNS, not represented as law.
- **Proposed Technical Design**: Engineering approach requiring repository and architecture approval.
- **Unresolved Decision**: Requires product, legal/compliance, clinical, privacy/security, or technical approval.

## Authority matrix

| Topic | Classification | Governing scope | Effective date | Requirement or boundary | SNS implementation consequence | Confirmation status |
|---|---|---|---|---|---|---|
| Medicare hospice participation framework | Binding Federal Requirement | Medicare-certified hospices | Current 42 CFR Part 418, verified Oct. 8, 2026 | Part 418 governs hospice eligibility, elections, benefit periods, patient care CoPs, QAPI, coverage, and payment. | Requirements must be mapped to the applicable Part 418 section rather than treated as one undifferentiated compliance rule. | Confirmed |
| Initial RN assessment | Binding Federal Requirement | Medicare-certified hospices | Current 42 CFR 418.54, verified Oct. 8, 2026 | Hospice RN completes the initial assessment within 48 hours after the election is complete, unless an earlier assessment is requested. | Initial Comprehensive RN Assessment must remain a controlled admission/election workflow and must not be confused with Update or Recertification Assessment. | Confirmed |
| Comprehensive assessment completion | Binding Federal Requirement | Medicare-certified hospices | Current 42 CFR 418.54, verified Oct. 8, 2026 | IDG, in consultation with the attending physician if any, completes the comprehensive assessment no later than 5 calendar days after election. | SNS must support the full interdisciplinary comprehensive-assessment obligation. The product label “Initial Comprehensive RN Assessment” must not imply that the RN alone fulfills every federal interdisciplinary requirement. | Confirmed; naming/workflow reconciliation required |
| Comprehensive assessment updates | Binding Federal Requirement | Medicare-certified hospices | Current 42 CFR 418.54, verified Oct. 8, 2026 | Federal CoP contains an Update of the Comprehensive Assessment standard. | SNS Update Assessment must map to the actual federal update requirements and timing before production. | Confirmed at section level; exact timing/text requires final traceability review |
| Certification and recertification for each benefit period | Binding Federal Requirement | Medicare hospice benefit | Current 42 CFR 418.22, verified Oct. 8, 2026 | Written certification is required for each benefit period; recertifications may be completed no more than 15 calendar days before the subsequent period. | Comprehensive RN Assessment (Recertification Assessment) may support evidence gathering but cannot substitute for authorized certification or recertification. | Confirmed |
| Face-to-face encounter from third benefit period onward | Binding Federal Requirement | Medicare hospice recertification | Current 42 CFR 418.22, verified Oct. 8, 2026 | F2F encounter is required before the third benefit-period recertification and every subsequent recertification, subject to current telehealth provisions. | Recertification workflow must link required F2F evidence where applicable and must not infer completion from nursing documentation alone. | Confirmed |
| Physician certification authority | Binding Federal Requirement | Medicare hospice certification/recertification | Current 42 CFR 418.22, verified Oct. 8, 2026 | Authorized physicians perform certification functions; clinical information supports but does not replace physician judgment. | QA, automated logic, Body Systems, and nursing assessments cannot certify terminal illness or generate a binding eligibility decision. | Confirmed |
| LCD terminal-status criteria | Medicare/MAC Guidance | Claims review and documentation support under the applicable contractor/LCD | LCD version/effective period must be verified at use | LCD criteria guide documentation and review; they are not an automatic pass/fail engine and diagnosis alone is insufficient. | SNS may surface evidence and gaps but must not automatically determine eligibility, prognosis, coverage, coding, or certification. | Confirmed as guidance boundary |
| Medicare election statement addendum | Binding Federal Requirement | Medicare hospice elections beginning on or after Oct. 1, 2026 | Oct. 1, 2026 | Election statement addendum is required and contains conditions, items, services, and drugs determined unrelated and not covered by hospice. | SNS must support the election-addendum workflow and preserve the determination and furnishing record. | Confirmed |
| Election addendum furnishing deadline | Binding Federal Requirement / CMS implementation material | Applicable Medicare hospice elections | Oct. 1, 2026 | CMS model materials state furnishing within the first 5 days of the election start date. | SNS deadline service must implement the controlling rule and current CMS corrections/guidance. | Confirmed; final codified text and corrections must be checked at release |
| Updated election addendum after affecting POC change | Binding Federal Requirement / CMS implementation material | Medicare hospice plan-of-care changes affecting addendum determinations | Oct. 1, 2026 | Updated written addendum is due within 3 days when an affecting plan-of-care change changes the determination. | Existing election-addendum task and determination architecture should be reused. | Confirmed; final codified text and corrections must be checked at release |
| Non-covered-items review at every Recertification Assessment | SNS Product Policy | SNS Comprehensive RN Assessment workflow | SNS implementation date, not federal effective date | Every Recertification Assessment contains a current review and cannot be finalized while it is incomplete. | Required SNS finalization gate. Recertification alone must not be represented as a federal furnishing trigger. | Product decision locked |
| Non-covered-items section omitted from Update Assessment | SNS Product Policy | SNS Comprehensive RN Assessment workflow | SNS implementation date | Update Assessment does not display the recertification-specific review section solely because it is an Update. | Toggle changes title, type, section visibility, validation, reporting, and audit classification. Separate legally triggered addendum work remains active. | Product decision locked |
| Initial Comprehensive RN Assessment / Comprehensive RN Assessment terminology | SNS Product Policy | SNS clinician-facing UI, reports, exports, help, training | Immediate product terminology lock | RNICA and related abbreviations remain internal only. Clinicians see Initial Comprehensive RN Assessment and Comprehensive RN Assessment with Update or Recertification purpose. | Central terminology compatibility mapping required. | Product decision locked |
| Draft Workspace | SNS Product Policy | SNS clinician documentation experience | SNS implementation date | Drafts are saved, recoverable, editable, and support real-time documentation, voice dictation, investigation, and refinement. Draft saves are not automatically presented as immutable legal-record versions. | Autosave and recovery are required; ordinary draft edits do not use correction/amendment workflows. | Product decision locked; retention/legal-hold details unresolved |
| Authentication of medical-record entries | Binding California Requirement | California licensed hospices | Emergency regulations effective June 22, 2026 | Medical-record system must protect entries and require authentication; authorized identity is authenticated when making entries. | Signed/authenticated entries require attributable actor, date/time, authorization, and integrity controls. | Confirmed |
| Medical-record quality and content control | Binding California Requirement | California licensed hospices | June 22, 2026 | Medical-record policies must address deficiency analysis and quality/content control. | Quality Review can support these controls but must not be represented as the only way to satisfy the regulation. | Confirmed |
| Alteration/correction of authenticated entries | Binding California Requirement | California licensed hospices | June 22, 2026 | Alteration requires written explanation; correction records reason, discovery date, correction date, and correction authentication. | Post-authentication correction workflow must preserve original content and required metadata. | Confirmed |
| Correction of identified medical-record errors within 48 hours | Binding California Requirement | California licensed hospices | June 22, 2026 | Authorized personnel must correct medical-record errors, including duplicate or wrong-patient documentation, within 48 hours of discovery. | Correction finding must track discovery time, due time, completion, authentication, and overdue escalation. | Confirmed; legal review should confirm application to each correction category |
| Addendum after original entry | Binding California Requirement | California licensed hospices | June 22, 2026 | Added information after original entry must be a distinct, traceable, dated, authenticated addendum. | Generic clinical addendum workflow must preserve original entry and link the addendum. Medicare election addendum remains a separate domain. | Confirmed |
| “Amendment” as a universal post-signature workflow | Unresolved Decision | SNS document families and applicable law/policy | Not yet set | California source explicitly addresses correction and addendum; a universal SNS amendment category requires document-family and policy mapping. | Do not assume every document family supports Amendment. Define allowed post-authentication actions by document family. | Unresolved |
| Finalized / Pending Signature state | SNS Product Policy / Unresolved Decision | SNS clinical record lifecycle | Not yet set | Product direction favors Draft -> Finalized/Pending Signature -> Authenticated, but legal-record status, reversibility, visibility, and QA access remain unresolved. | No schema enum or migration until state semantics and transitions are approved. | Unresolved |
| Immutability after authentication | Binding California control plus SNS Product Policy | California record integrity and SNS lifecycle | California rule June 22, 2026; SNS implementation date TBD | Authenticated entries cannot be silently altered; SNS chooses to make the authenticated version immutable and require formal post-authentication workflows. | RecordVersion snapshot, edit denial, and traceable post-authentication workflows required. | Regulatory boundary confirmed; technical design pending |
| Federal hospice QAPI program | Binding Federal Requirement | Medicare-certified hospices | Current 42 CFR 418.58, verified Oct. 8, 2026 | Hospice must maintain an ongoing, hospice-wide, data-driven QAPI program with documentary evidence and measurable improvement activities. | SNS Quality Review may provide data and workflows, but record-level QA review is not itself the complete federal QAPI program. | Confirmed |
| Record-level Quality Review workflow | SNS Product Policy | SNS clinical documentation | SNS implementation date | SNS provides structured record review, findings, follow-up, resolution, approval, and escalation. | Keep distinct from QAPI program governance and clinical-record status. | Product decision locked |
| QA as capability, not job title | SNS Product Policy | SNS tenant authorization | SNS implementation date | Authorized Reviewer capability supports dedicated QA, Assistant DPCS, DPCS, Clinical Manager, Case Manager when permitted, and other agency-designated reviewers. | Backend capability and tenant policy govern actions; job-title text is non-authoritative. | Product decision locked |
| Dedicated QA department required | Not Required by cited authority | SNS agency configuration | Verified Oct. 8, 2026 | Sources reviewed do not prescribe a dedicated QA department or QA Nurse title for record review. | SNS must support small and large agency staffing models. | Confirmed limitation of sources |
| Self-review | SNS Operational Policy | Tenant-specific Quality Review configuration | Tenant effective date | Self-review may be allowed by tenant policy but is labeled Self-Review and is not independent review by default. | Typed tenant policy, conflict rules, reporting distinction, and audit required. | Product default proposed; tenant policy matrix unresolved |
| Independent review | SNS Operational Policy | Tenant-specific Quality Review configuration | Tenant effective date | Reviewer is separate from the author when policy requires independent review. | Author-exclusion and reviewer-eligibility checks required. | Product concept locked; document/risk matrix unresolved |
| Second reviewer | SNS Operational Policy | Tenant-specific Quality Review configuration | Tenant effective date | A second reviewer may be required for selected documents or risk categories. | State machine and policy schema must define sequence, authority, and closure. | Unresolved configuration matrix |
| Pre-authentication documentation review | SNS Product/Operational Policy | Selected high-risk documents | Tenant effective date | Review occurs before signature without transferring authorship or authentication authority. | Must remain distinct from post-authentication QA and correction history. | Concept approved; document scope unresolved |
| Post-authentication quality audit | SNS Product/Operational Policy | Authenticated documents selected by policy | Tenant effective date | Reviewer examines the exact authenticated version; findings are separate; clinician resolves through approved record workflow. | Exact RecordVersion linkage required. | Concept approved |
| Quality Approved status | SNS Product Policy | SNS Quality Review | SNS implementation date | Means review closure conditions are met; it does not authenticate, certify, sign, approve a POC, or make a coverage determination. | UI, reports, and APIs must preserve this boundary. | Product decision locked |
| Body Systems owned by assessment instance | SNS Product Policy / Proposed Technical Design | SNS Initial, Update, and Recertification assessments | SNS implementation date | Body Systems should be attributable to the owning assessment rather than ambiguous patient-only scope. | Requires safe linkage rollout, historical source attribution, and migration validation. | Product decision locked; technical migration pending |
| Body Systems clinical-detail rollout one system at a time | SNS Product Policy | SNS Body Systems implementation | SNS implementation governance | Each body system is separately discovered, implemented, reviewed, tested, and approved. | No one-pass generation of all system-specific clinical forms. | Product decision locked |
| QualityReview linked to exact RecordVersion | Proposed Technical Design | SNS Quality Review persistence | Not yet set | Review should identify the exact authenticated version and preserve prior-version review history. | Preferred integrity design; requires repository contract and deletion/retention rules. | Proposed, not yet approved |
| Task owns assignment; QualityReview owns review outcome | Proposed Technical Design | SNS routing/state management | Not yet set | Operational routing and clinical review state are separated but must transition transactionally. | Requires state ownership matrix, idempotency, rollback, and reconciliation controls. | Proposed, not yet approved |
| GuardrailPolicy for tenant QA configuration | Proposed Technical Design | SNS per-tenant policy | Not yet set | Existing policy infrastructure may store typed, versioned QA configuration. | Requires namespaced keys, schema validation, fail-closed defaults, revision history, and authorization. | Proposed, not yet approved |
| Use of identifiable historical patient data for testing | SNS Operational Policy subject to privacy/security law | Authorized SNS testing | Per approved test case | Allowed only with organizational authorization, defined purpose, minimum necessary data, isolated environment, access controls, audit, retention, cleanup, and restricted sharing. | If safeguards cannot be confirmed, use de-identified or synthetic data. | Policy locked; each test requires authorization |
| Automatic eligibility/prognosis/certification determination | Prohibited Product Boundary | SNS clinical decision support | Immediate | SNS must not turn LCD criteria, QA approval, Body Systems, or assessment completion into an automatic binding certification or coverage conclusion. | Decision support may surface evidence and gaps only; authorized clinical judgment remains required. | Locked |

## Required source traceability

### Federal

- 42 CFR Part 418, including §§ 418.22, 418.24, 418.54, and 418.58.
- CMS FY 2027 hospice final rule and current CMS election-statement addendum implementation materials.
- Applicable Medicare Benefit Policy Manual, State Operations Manual, and current contractor LCDs.

### California

- Title 22 California hospice emergency regulations effective June 22, 2026, particularly section 74888 for medical-record service, authentication, quality/content control, corrections, and addenda.

### SNS

- Draft Workspace and Finalized Record Requirement.
- Comprehensive RN Assessment Update vs Recertification Requirement.
- Medicare Non-Covered Items Recertification Requirement.
- Scalable Quality Review Requirement and workflow rules.
- Body Systems governance and system-by-system delivery requirements.

## Implementation gate

Before coding, GitHub must add a traceability field to every planned requirement:

- authority classification
- authority citation/section
- jurisdiction
- applicable provider/payer
- effective date
- verification date
- mandatory/advisory/internal
- implementation owner
- acceptance criteria
- unresolved approvals

Any item classified as **Unresolved Decision** or **Proposed Technical Design** remains blocked from implementation until approved.
