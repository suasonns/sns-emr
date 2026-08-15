MASTER BACKLOG UPDATE RULE

When updating the master backlog:

1. Do NOT write patch instructions inside the backlog.
2. Do NOT write "add this" or "replace that" inside the backlog.
3. Generate a complete replacement block for the affected section.
4. Keep completed work separate from open defects.
5. Keep current phase separate from next phase queue.
6. Keep evidence/results separate from future work.
7. Only one CURRENT PHASE is active at a time.

🔒 NEW DEVELOPMENT RULE (PERMANENT)
✅ Any file we touch must leave with ONE source of truth + zero hidden logic

# ✅ GLOBAL ENFORCEMENT RULE

## PURPOSE
Ensure:
- No schema drift
- No unsafe automigrations
- No fake alignment (NO STAMP)
- Forward-only repair
- Audit-safe system behavior
- Tenant-safe data isolation

MINIMUM DATA PRINCIPLE

SNS should never require additional documentation,
additional clicks,
additional assessment fields,
additional validations,
or additional workflows

unless:

1. Existing data is insufficient

and

2. Testing proves a real workflow gap exists.

The purpose of SNS is to reduce workload
while improving evidence quality.

---------------------------------------------------------
DISEASE INTELLIGENCE FIRST RULE
---------------------------------------------------------

STATUS:
PERMANENT ✅

Documentation is not the source of truth.

Documentation is a storage layer,
presentation layer,
communication layer,
and regulatory output layer.

SNS Architecture:

AI Knowledge
↓
Evidence Gathering
↓
Disease Intelligence
↓
Clinical Reasoning
↓
Transcript Validation
↓
Documentation

Documentation consumes intelligence.

Documentation does not define intelligence.

---------------------------------------------------------
CLINICAL TRUTH EXPOSURE RULE
---------------------------------------------------------

STATUS:

PERMANENT ✅

PURPOSE:

SNS exists to expose clinical truth already present
inside records received by the hospice agency.

SNS SHALL:

- organize evidence
- correlate evidence
- classify evidence
- expose missing evidence
- expose conflicting evidence
- expose source traceability

SNS SHALL NOT:

- determine eligibility
- determine prognosis
- approve admission
- replace physician judgment

RN validates assessment truth.

Physician validates prognosis truth.

Agency validates admission readiness.

The objective is visibility.

Not decision replacement.

---------------------------------------------------------
ONCOLOGY REFERENCE ARCHITECTURE RULE
---------------------------------------------------------

STATUS:
PERMANENT ✅

Oncology is the SNS Disease Intelligence
Reference Architecture.

The purpose of Oncology was to expose
all major architecture requirements before
other disease families were expanded.

All future disease families must follow the
Oncology pattern whenever clinically appropriate.

STANDARD FLOW:

AI Knowledge
↓
Evidence Gathering
↓
Disease Process Intelligence
↓
Findings
↓
Interpretations
↓
Recommendations
↓
Eligibility Support
↓
POC Support
↓
Documentation Support

RULE:

Before creating a new architecture pattern:

1. Verify Oncology
2. Verify reusable pattern exists
3. Reuse before redesign

Disease content may differ.

Architecture should remain consistent.

Future disease families should align to Oncology
so system-wide alignment can be performed in batches
without compromising integrity.

PURPOSE:

Consistency allows future alignment work
to occur in controlled batches without
compromising integrity.

---------------------------------------------------------
POST-DISEASE ALIGNMENT RULE
---------------------------------------------------------

STATUS:
DEFERRED ✅

ACTIVATION:

Major disease families completed
or formally blocked.

RULE:

If development can continue safely:

Add discovery to:

POST-DISEASE ALIGNMENT

Continue disease development.

Do not interrupt disease-family completion
for non-blocking architectural improvements.

BLOCKER EXCEPTION:

Immediate repair permitted only if:

- development cannot continue
- duplicate source of truth exists
- schema conflict exists
- compliance blocker exists
- patient-safety risk exists
- data-integrity risk exists

Otherwise:

Document discovery
↓
POST-DISEASE ALIGNMENT
↓
Continue disease work

POST-DISEASE ALIGNMENT includes:

- documentation architecture alignment
- metadata alignment
- audit enhancements
- lineage enhancements
- workflow normalization
- documentation normalization
- transcript traceability
- recommendation traceability
- architecture cleanup
- infrastructure cleanup

---------------------------------------------------------
DISEASE FAMILY COMPLETION RULE
---------------------------------------------------------

A disease family must be completed before
moving to another workflow layer unless
formally blocked.

Finish:

AI Knowledge
↓
Evidence
↓
Disease Intelligence
↓
Findings
↓
Interpretations
↓
Recommendations
↓
Eligibility Support

before moving to:

- narrative automation
- recommendation automation
- Medical Director automation
- IDG automation
- recertification automation
- documentation optimization
- audit alignment

The objective is completion.

Not perpetual redesign.

---
=========================================================
✅ CMS / NGS / CDPH / TJC / CHAP / ACHC / DHS
AUDIT-SURVIVAL BUILD RULE
=========================================================

PURPOSE

SNS Hospice EMR is not being built to satisfy database
integrity alone.

SNS Hospice EMR is being built to survive:

- CMS review
- NGS review
- CDPH survey
- DHS review
- TJC accreditation review
- CHAP accreditation review
- ACHC accreditation review
- Medical Director review
- IDG review
- External audit review
- Legal record review

RULE

No workflow, ontology branch, evidence engine,
recommendation engine, assessment process,
care plan process, eligibility process, or narrative
generation process may be considered COMPLETE
unless it is capable of supporting audit-survival use.

DATABASE VALIDITY IS NOT SUFFICIENT

The following do NOT equal completion:

- tables exist
- nodes exist
- parent relationships exist
- validation queries pass
- orphan check returns zero rows

Those are foundation requirements only.

COMPLETION STANDARD

A feature is complete only when it supports:

1. Clinical documentation
2. Evidence traceability
3. Medical necessity support
4. Eligibility support
5. Plan-of-care support
6. Survey defensibility
7. Interdisciplinary review
8. Clinical reasoning
9. Recommendation support
10. Audit reconstruction

=========================================================
DISEASE AUDIT-SURVIVAL STANDARD
=========================================================

Every disease family must contain:

A. Disease Identity
- primary site
- subtype classification
- disease hierarchy
- high-risk variants

B. Symptom Intelligence
- common symptoms
- uncommon symptoms
- advanced symptoms
- hospice decline symptoms

C. Complication Intelligence
- local disease effects
- organ compromise
- obstruction syndromes
- bleeding syndromes
- infection syndromes
- metastatic complications

D. Prognostic Intelligence
- disease burden
- decline indicators
- treatment failure indicators
- poor prognosis indicators

E. Treatment Intelligence
- prior therapies
- failed therapies
- treatment limitations
- no-further-treatment indicators

F. Functional Intelligence
- ADL decline
- mobility decline
- PPS indicators
- ECOG indicators

G. Nutritional Intelligence
- weight loss
- poor intake
- cachexia
- malnutrition

H. End-Stage Findings
- refractory symptoms
- progressive decline
- imminent death indicators

I. Hospice Eligibility Support
- disease-specific eligibility indicators
- progression indicators
- treatment limitation indicators

J. Evidence Architecture
- diagnosis evidence
- imaging evidence
- symptom evidence
- complication evidence
- treatment evidence
- decline evidence
- prognostic evidence
- additional evidence categories where clinically appropriate

K. Validation
- inventory validation
- evidence validation
- hierarchy validation
- orphan validation
- audit-support validation

A disease family is COMPLETE only when
all categories above are validated.

=========================================================
PRODUCTION-GRADE DEFINITION
=========================================================

PRODUCTION_GRADE means:

- clinically meaningful
- evidence traceable
- survey defensible
- eligibility supportable
- recommendation capable
- physician review capable
- IDG review capable
- audit reconstructable

PRODUCTION_GRADE does NOT mean:

- SQL inserted successfully
- node count threshold reached
- hierarchy exists
- orphan query returned zero rows

=========================================================
WORKFLOW RULE
=========================================================

When a disease family is started:

COMPLETE the disease family to the audit-survival
standard before moving to:

- recommendation automation
- narrative generation
- eligibility generation
- Medical Director automation
- IDG automation
- recertification automation
- downstream AI workflows

unless formally BLOCKED.

# 🚨 HARD RULES (NON-NEGOTIABLE)

NEVER:
- [x] use alembic stamp
- [x] delete migration history
- [x] rewrite revisions
- [x] blindly drop tables
- [x] trust autogenerate without review

ALWAYS:
- [x] VERIFY-FIRST
- [x] forward-only migrations
- [x] repair via migration
- [x] manual inspection
- [x] runtime verification

NO assumption-driven development 

BEFORE any change: 

1. Verify what exists (DB, code, files) 
2. Verify what is missing 
3. Verify what is actually being used 
4. THEN decide if change is necessary

=========================================================
DISEASE BUILD COMPLETION RULE
=========================================================

RULE:
When a disease family is started, it must be completed before moving to another workflow layer unless the work is blocked.

COMPLETE means:

1. Root ontology nodes exist ✅
2. Disease/subtype nodes exist ✅
3. Prognostic factor nodes exist ✅
4. Functional decline nodes exist where applicable ✅
5. Treatment limitation nodes exist where applicable ✅
6. Cachexia/nutritional decline nodes exist where applicable ✅
7. Eligibility categories exist ✅
8. Keyword → eligibility mappings exist ✅
9. Validation query completed ✅
10. Only root/container nodes remain unmapped ✅

BLOCKED means:

- schema conflict prevents continuation
- missing source-of-truth table prevents continuation
- unclear clinical model requires decision
- implementation would create duplicate source of truth
- required verification cannot be completed

DO NOT:

- leave disease families partially implemented
- jump to narrative generation before disease library is complete
- assume RN ICA keyword coverage equals disease intelligence coverage
- create duplicate ontology logic in compiler code

DO:

- finish one disease family at a time
- validate before moving on
- keep evidence/results separate from future work
- keep current phase separate from next phase queue

---

# ✅ MASTER FLOW

1. VERIFY  
2. IDENTIFY  
3. CLASSIFY  
4. REPAIR  
5. VERIFY AGAIN  

# 🚨 GLOBAL HARD RULES (PERMANENT)
- NEVER generate random tenants
- NEVER generate random patients
- ONLY use controlled dataset (5 patients per tenant)
- Juan Dela Cruz (PERMANENT)
- Juana Dela Cruz (PERMANENT)

# ✅ TENANT CONTROL
REAL:
- 01271980-0000-0000-0000-000005101977 (LOVE AND FAITH)

TRAINING:
- aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa (ANGELA)
- bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb (SILVA)

TEMP (REMOVE BEFORE PROD):
- 5224ceb6-e29d-4841-858e-e77f1b67fe65
- 85282f8b-fd5b-45e6-bb82-45394ef7a2f8

# ✅ CURRENT STATUS
## STABLE
- Tenant system ✅
- Database aligned ✅
- Core APIs exist ✅

------------------------------------------------------------
## 🔒 SECURITY + COMPLIANCE (ACTIVATE AFTER FIELD TESTING)
------------------------------------------------------------

STATUS:
⚠️ NOT IMPLEMENTED DURING BUILD OR FIELD TESTING
✅ IMPLEMENT ONLY AFTER FIELD TESTING IS COMPLETE

DEFINITION OF "AFTER FIELD TESTING":
- system actively used in field with real users ✅
- bugs identified and resolved ✅
- workflows working correctly in real world ✅
- team ready to fully transition from Hospicemd ✅

------------------------------------------------------------
## 🚫 DISABLED DURING FIELD TESTING
------------------------------------------------------------

DO NOT IMPLEMENT:

- permanent locks ❌
- immutable records ❌
- irreversible transitions ❌
- prevention of edits ❌
- prevention of deletes ❌

SYSTEM MUST ALLOW:

- edit any record ✅
- delete any record ✅
- correct mistakes ✅
- rerun workflows ✅

RATIONALE:
Field testing requires full flexibility to fix real-world issues
without blocking clinical operations or testing workflows.

------------------------------------------------------------
## ✅ REQUIRED BEFORE PRODUCTION CUTOVER
------------------------------------------------------------

AFTER FIELD TESTING IS COMPLETE:

### ✅ 1. CLINICAL RECORD FINALIZATION
- finalized notes become read-only ✅
- no direct edits after finalization ✅

---

### ✅ 2. AMENDMENT-ONLY CORRECTIONS
- all changes must be additive ✅
- original content preserved ✅

---

### ✅ 3. AUDIT TRAIL (MANDATORY)
- track all:
  - create ✅
  - edit ✅
  - delete ✅
- preserve prior values ✅
- changes must not overwrite history ✅

---

### ✅ 4. DATA INTEGRITY PROTECTION
- enforce authorship ✅
- enforce timestamps ✅
- prevent silent overwrites ✅

---

### ✅ 5. SECURITY CONTROLS
- role-based access ✅
- permission enforcement ✅
- audit logging ✅

---

------------------------------------------------------------
## ⚠️ PRODUCTION CUTOVER RULE
------------------------------------------------------------

BEFORE MIGRATION FROM HOSPICEMD:

1. REMOVE TEST DATA ✅
2. ENABLE SECURITY LAYER ✅
3. ENABLE AUDIT TRAIL ✅
4. ENABLE FINALIZATION RULES ✅
5. VERIFY SYSTEM WITH CLEAN DATA ✅

------------------------------------------------------------

------------------------------------------------------------
## 🧠 TENANT + DATA CONTROL MODEL
------------------------------------------------------------

### ✅ TENANT TYPES

#### 🟢 TRAINING TENANTS (ALWAYS FLEXIBLE)
- Angela Hospice ✅
- Silva Hospice ✅

RULES:
- allow edit ✅
- allow delete ✅
- allow recreate ✅
- NO immutability ❌
- NO irreversible transitions ❌

PURPOSE:
- training
- testing
- development validation

---

#### 🟡 PRODUCTION TENANTS
(example: Love and Faith Hospice)

RULE:
Data control depends on PATIENT STATUS

---

### ✅ PATIENT STATE CONTROL

#### 🟢 PENDING PATIENT
- editable ✅
- deletable ✅
- no restrictions ✅

---

#### 🔴 ACTIVE PATIENT
(ONLY AFTER FIELD TESTING IS COMPLETE)

REQUIREMENTS TO ACTIVATE:

- system stable ✅
- testing complete ✅
- ready for production cutover ✅
- Hospicemd being retired ✅

THEN ENABLE:

- immutable finalized notes ✅
- amendment-only changes ✅
- audit trail ✅
- restricted deletion ✅

---

### 🚫 CURRENT SYSTEM RULE (FIELD TESTING)

DO NOT ENABLE:

- immutability ❌
- locking ❌
- irreversible transitions ❌

SYSTEM MUST ALLOW:

- edit any record ✅
- delete any record ✅
- fix mistakes ✅
- rerun workflows ✅

---

### 🔐 FUTURE IMPLEMENTATION (TRACK ONLY)

ENFORCE ONLY WHEN:

✅ field testing complete  
✅ ready to migrate from Hospicemd  
✅ production deployment begins  

---

FINAL GOAL:

SYSTEM TRANSITIONS FROM:

flexible testing system ✅

TO:

audit-safe clinical system ✅

=========================================================
SNS HOSPICE EMR — MASTER BACKLOG V9
=========================================================

MODE:
VERIFY-FIRST / CLINICAL-FIRST / ONTOLOGY-FIRST / AUDIT-READY / COMPLIANCE-FIRST

PLANNER MODE:
LOCKED ✅

=========================================================
MASTER BACKLOG UPDATE RULE
=========================================================

When updating the master backlog:

1. Do NOT write patch instructions inside the backlog.
2. Do NOT write "add this" or "replace that" inside the backlog.
3. Generate a complete replacement block for the affected section.
4. Keep completed work separate from open defects.
5. Keep current phase separate from next phase queue.
6. Keep evidence/results separate from future work.
7. Only one CURRENT PHASE is active at a time.

=========================================================
GLOBAL ENFORCEMENT RULE
=========================================================

PURPOSE:

Ensure:

- No schema drift
- No unsafe automigrations
- No fake alignment
- No alembic stamp shortcuts
- Forward-only repair
- Audit-safe system behavior
- Tenant-safe data isolation
- One source of truth
- Zero hidden logic

NEW DEVELOPMENT RULE:

Any file touched must leave with:

- ONE source of truth
- ZERO hidden logic

MINIMUM DATA PRINCIPLE:

SNS should never require additional documentation,
additional clicks,
additional assessment fields,
additional validations,
or additional workflows unless:

1. Existing data is insufficient

AND

2. Testing proves a real workflow gap exists.

The purpose of SNS is to reduce workload while improving evidence quality.

=========================================================
HARD RULES — NON-NEGOTIABLE
=========================================================

NEVER:

- use alembic stamp
- delete migration history
- rewrite revisions
- blindly drop tables
- trust autogenerate without review
- create duplicate ontology logic in compiler code
- create duplicate disease intelligence engines
- create duplicate symptom engines
- create duplicate ICD logic engines
- create duplicate oncology source of truth
- assume RN ICA keyword coverage equals disease intelligence coverage
- generate random tenants
- generate random patients

ALWAYS:

- VERIFY-FIRST
- forward-only migrations
- repair via migration
- manual inspection
- runtime verification
- verify what exists before changing
- verify what is missing before changing
- verify what is actually being used before changing
- preserve one ontology authority
- preserve clinical traceability
- preserve source-of-truth ownership
- use controlled dataset only during testing

NO ASSUMPTION-DRIVEN DEVELOPMENT.

BEFORE any change:

1. Verify what exists.
2. Verify what is missing.
3. Verify what is actually being used.
4. Then decide if change is necessary.

=========================================================
ONCOLOGY BUILD PREREQUISITES
=========================================================

Before Building Any New Cancer

STEP 1
VERIFY disease root exists

STEP 2
VERIFY evidence inventory exists

STEP 3
RUN gap query:
evidence vs ontology coverage

STEP 4
COMPARE against completed peer disease

STEP 5
Build:
A Disease Identity
B Symptomology
C Complications
D Prognostic Factors
E Treatment Limitations
F Functional Decline
G Nutritional Decline
H End Stage Findings
I Hospice Eligibility
J Evidence Architecture
K Validation

### Mandatory Validation
Duplicate Query
Orphan Query
Evidence Inventory Query
Hierarchy Export
Keyword Group Inventory
### Disease Completion Levels
NOT BUILT
BUILT
VALIDATED
PRODUCTION GRADE
AUDIT-SURVIVAL COMPLETE
### Hard Rule
Never start a new cancer until:

Evidence Inventory
Gap Inventory
Peer Pattern Inventory

have all been completed.
=========================================================
TENANT CONTROL
=========================================================

REAL:

- 01271980-0000-0000-0000-000005101977
  LOVE AND FAITH

TRAINING:

- aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa
  ANGELA

- bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb
  SILVA

TEMP — REMOVE BEFORE PRODUCTION:

- 5224ceb6-e29d-4841-858e-e77f1b67fe65
- 85282f8b-fd5b-45e6-bb82-45394ef7a2f8

CONTROLLED TEST PATIENTS:

- Juan Dela Cruz
- Juana Dela Cruz

RULE:

Only controlled test tenants and controlled test patients may be used during active build and validation.

=========================================================
SECURITY + COMPLIANCE ACTIVATION RULE
=========================================================

STATUS:

NOT IMPLEMENTED DURING BUILD OR FIELD TESTING ⚠️

IMPLEMENT ONLY AFTER FIELD TESTING IS COMPLETE ✅

DEFINITION OF AFTER FIELD TESTING:

- system actively used in field with real users
- bugs identified and resolved
- workflows working correctly in real world
- team ready to fully transition from Hospicemd

=========================================================
DISABLED DURING FIELD TESTING
=========================================================

DO NOT IMPLEMENT DURING FIELD TESTING:

- permanent locks
- immutable records
- irreversible transitions
- prevention of edits
- prevention of deletes
- amendment-only enforcement
- finalized-note locking

SYSTEM MUST ALLOW DURING FIELD TESTING:

- edit any record
- delete any record
- correct mistakes
- rerun workflows
- regenerate versions
- repair test data

RATIONALE:

Field testing requires full flexibility to fix real-world issues without blocking clinical operations or testing workflows.

=========================================================
REQUIRED BEFORE PRODUCTION CUTOVER
=========================================================

AFTER FIELD TESTING IS COMPLETE:

1. CLINICAL RECORD FINALIZATION

- finalized notes become read-only
- no direct edits after finalization

2. AMENDMENT-ONLY CORRECTIONS

- all changes must be additive
- original content preserved

3. AUDIT TRAIL

- track create
- track edit
- track delete
- preserve prior values
- prevent overwrite of history

4. DATA INTEGRITY PROTECTION

- enforce authorship
- enforce timestamps
- prevent silent overwrites

5. SECURITY CONTROLS

- role-based access
- permission enforcement
- audit logging

6. PRODUCTION DATA CLEANUP

- remove test data
- remove temporary tenants
- verify clean production dataset

=========================================================
CMS / NGS / CDPH / TJC / CHAP / ACHC / DHS
AUDIT-SURVIVAL BUILD RULE
=========================================================

STATUS:
PERMANENT ✅

PURPOSE:

SNS Hospice EMR is not being built merely to satisfy:

- database integrity
- table completeness
- hierarchy completeness
- ontology completeness
- successful SQL execution
- zero orphan rows

SNS Hospice EMR is being built to survive:

- CMS review
- NGS review
- CDPH survey
- DHS review
- TJC accreditation review
- CHAP accreditation review
- ACHC accreditation review
- Medical Director review
- IDG review
- external audit review
- legal record review

DATABASE VALIDITY IS NOT COMPLETION.

The following only prove structural integrity:

- SQL executed
- nodes inserted
- hierarchy exists
- validation query passed
- orphan query = 0 rows

Those are foundation requirements only.

PRODUCTION GRADE means:

- clinically meaningful
- evidence traceable
- survey defensible
- eligibility supportable
- plan-of-care supportable
- recommendation capable
- physician-review capable
- IDG-review capable
- audit reconstructable
- medical-record defensible
- claim-defense supportable

PRODUCTION GRADE does NOT mean:

- SQL inserted successfully
- node count threshold reached
- hierarchy exists
- orphan query returned 0 rows
- generic hospice wording exists
- minimum stable ontology exists

=========================================================
COPILOT OUTPUT STANDARD — PERMANENT
=========================================================

All future Copilot output for SNS Hospice EMR must default to:

PRODUCTION-GRADE / AUDIT-SURVIVAL BUILD

and must NOT revert to:

- minimum stable
- scaffold only
- node-count completion
- orphan-check-only validation
- generic hospice wording
- partial disease branches
- architecture-only completion

unless Romel explicitly asks for:

- scaffold only
- minimal patch
- partial insert
- quick prototype
- temporary test data

For disease intelligence work, every output must assume the goal is:

CMS / NGS / CDPH / DHS / TJC / CHAP / ACHC
audit-survival readiness.

Before calling any disease, feature, workflow, or evidence layer complete, Copilot must verify whether it supports:

- clinical documentation
- evidence traceability
- medical necessity support
- hospice eligibility support
- plan-of-care support
- interdisciplinary review
- physician review
- audit reconstruction
- medical-record defensibility

If those are not satisfied, the status must remain:

HARDENING REQUIRED

=========================================================
NEW CHAT STARTUP PROTOCOL
=========================================================

RULE:

Before any work begins:

1. Read CURRENT PHASE

2. Read CURRENT ACTIVE BUILD

3. Read CURRENT EXECUTION ORDER

4. Read COMPLETED WORK

5. Read NOT CURRENT FOCUS

6. Read SUCCESS CRITERIA

7. Read EXIT CRITERIA

8. Verify ontology remains source of truth

9. Verify no duplicate intelligence authority exists

DO NOT BUILD ANYTHING

until all sections have been reviewed.

VERIFY-FIRST remains mandatory.

=========================================================
DISEASE BUILD PROTOCOL
=========================================================

STEP 1
Verify disease root.

STEP 2
Verify parent hierarchy.

STEP 3
Verify evidence inventory.

STEP 4
Run peer comparison.

STEP 5
Run A-K gap review.

STEP 6
Classify:

NOT BUILT
BUILT
VALIDATED
PRODUCTION GRADE
AUDIT-SURVIVAL COMPLETE

STEP 7
Only after verification may implementation begin.

=========================================================
STANDARD INSERT ORDER
=========================================================

1. Root

2. Foundation Containers

3. Evidence Containers

4. Disease Identity

5. Symptomology
   A. Common
   B. Uncommon
   C. Rare

6. Complications

7. Prognostic Factors

8. Hospice Eligibility

9. Treatment Limitations

10. Functional Decline

11. Nutritional Decline

12. End Stage Findings

13. Evidence Nodes

14. Validation

15. Classification

=========================================================
DISEASE BUILD EXECUTION RULE
=========================================================

PURPOSE:

Ensure disease families are built consistently,
efficiently, and audit-safely.

REQUIRED PROCESS:

1. Inventory Verification
2. Peer Comparison
3. A-K Gap Review
4. Batch Disease Build
5. Inventory Validation
6. Duplicate Validation
7. Orphan Validation
8. Evidence Validation
9. Disease Classification

BATCH BUILD RULE:

Build by disease family.

Do not:

- insert one node at a time
- validate after every insert
- perform micro-repairs during initial construction

Preferred workflow:

Disease Family
↓
A-K Batch Build
↓
Validation
↓
Classification

VALIDATION REQUIRED AFTER BATCH BUILD:

✅ Inventory Query
✅ Duplicate Query
✅ Orphan Query
✅ Evidence Validation
✅ Hierarchy Validation

CLASSIFICATION:

NOT BUILT
↓
BUILT
↓
VALIDATED
↓
PRODUCTION GRADE
↓
AUDIT-SURVIVAL COMPLETE

=========================================================
STANDARD VALIDATION ORDER
=========================================================

1. Inventory Count

2. Duplicate Query

3. Orphan Query

4. Evidence Domain Validation

5. Hierarchy Validation

6. Keyword Group Validation

7. Production Grade Review

8. Audit-Survival Review

=========================================================
DISEASE COMPLETION CHECKLIST
=========================================================

A. Disease Identity ✅

B. Symptomology ✅

C. Complications ✅

D. Prognostic Factors ✅

E. Treatment Limitations ✅

F. Functional Decline ✅

G. Nutritional Decline ✅

H. End Stage Findings ✅

I. Hospice Eligibility ✅

J. Evidence Architecture ✅

K. Validation ✅

=========================================================
BACKLOG UPDATE PROTOCOL
=========================================================

1. Update CURRENT PHASE

2. Update CURRENT ACTIVE BUILD

3. Update COMPLETED WORK

4. Update VERIFIED RESULTS

5. Update CURRENT EXECUTION ORDER

6. Update NEXT PHASE QUEUE

7. Verify:

- one CURRENT PHASE
- one CURRENT ACTIVE BUILD
- completed work separate
- future work separate
- evidence separate
- no duplicate source of truth
- no patch instructions

STATUS DEFINITIONS

NOT BUILT

↓

BUILT

↓

VALIDATED

↓

PRODUCTION GRADE

↓

AUDIT-SURVIVAL COMPLETE

=========================================================
BUILD STATUS CLASSIFICATION RULE
=========================================================

Every disease must be classified using this progression:

1. NOT BUILT
2. BUILT
3. VALIDATED
4. PRODUCTION GRADE
5. AUDIT-SURVIVAL COMPLETE

NOT BUILT means:

- no complete ontology branch exists

BUILT means:

- ontology branch exists
- hierarchy exists
- some validation has occurred

VALIDATED means:

- inventory validation completed
- hierarchy validation completed
- evidence-domain validation completed
- orphan validation completed

PRODUCTION GRADE means:

- A-K disease completion standard satisfied
- clinically meaningful depth exists
- evidence supports eligibility, POC, recommendation, and review workflows

AUDIT-SURVIVAL COMPLETE means:

- production grade validated
- evidence behavior validated
- recommendation behavior validated
- eligibility support validated
- audit reconstruction pathway validated

IMPORTANT:

BUILT does NOT equal PRODUCTION GRADE.

VALIDATED does NOT equal AUDIT-SURVIVAL COMPLETE.

=========================================================
DISEASE AUDIT-SURVIVAL COMPLETION STANDARD
=========================================================

No disease may be classified COMPLETE unless all categories are satisfied.

A. DISEASE IDENTITY

- primary site
- disease family
- body-system placement
- histology
- subtypes
- high-risk variants
- clinically meaningful classifications

B. SYMPTOMOLOGY

- common symptoms
- uncommon symptoms
- rare / advanced symptoms
- hospice decline symptoms
- disease-specific symptom variants
- symptoms that trigger plan-of-care review
- symptoms that support significant-change evaluation

C. COMPLICATIONS

- local invasion
- obstruction
- bleeding / hemorrhage
- infection / abscess
- organ compromise
- organ failure
- metastatic complications
- VTE / DVT / PE
- cachexia / malnutrition
- recurrent hospitalization drivers

D. PROGNOSTIC FACTORS

- advanced disease
- metastatic burden
- treatment-refractory disease
- high-risk histology
- organ compromise
- obstruction
- recurrent bleeding
- functional decline
- nutritional decline
- poor performance status
- no further treatment options

E. TREATMENT LIMITATIONS

- failed surgery
- failed radiation
- failed chemotherapy
- failed targeted therapy
- failed immunotherapy
- failed hormonal therapy where applicable
- treatment intolerance where applicable
- not surgical candidate
- not systemic therapy candidate
- palliative management only
- comfort-focused care only
- no further treatment options

F. FUNCTIONAL DECLINE

- progressive weakness
- activity intolerance
- ADL dependence
- reduced mobility
- homebound status
- bedbound status
- declining PPS
- declining ECOG

G. NUTRITIONAL DECLINE

- weight loss
- poor oral intake
- decreased appetite / anorexia
- cachexia
- muscle wasting
- protein-calorie malnutrition
- dehydration
- failure to maintain weight

H. END-STAGE FINDINGS

- terminal decline
- refractory symptoms
- refractory pain
- refractory bleeding where applicable
- obstruction / end-stage organ compromise where applicable
- minimal oral intake
- bedbound status
- cachexia
- multi-organ failure
- imminent death findings

I. HOSPICE ELIGIBILITY

- progressive despite treatment
- no further treatment options
- failed multiple lines of therapy
- functional decline
- nutritional decline
- end-stage disease burden
- disease-specific eligibility triggers
- declining despite supportive care

J. EVIDENCE ARCHITECTURE

- diagnosis evidence
- imaging evidence
- symptom evidence
- complication evidence
- treatment evidence
- decline evidence
- prognostic evidence
- lab evidence where clinically relevant
- procedure evidence where clinically relevant
- hospice eligibility evidence where clinically relevant

K. VALIDATION

- evidence-domain counts
- full keyword group inventory
- full hierarchy export
- orphan check = 0 rows
- no meaningless placeholders unless intentionally retained
- no duplicate disease intelligence source of truth
- disease has enough clinical depth to support audit, eligibility, and plan-of-care generation

A disease is COMPLETE only when A through K are satisfied.

=========================================================
MASTER FLOW
=========================================================

1. VERIFY
2. IDENTIFY
3. CLASSIFY
4. REPAIR
5. VERIFY AGAIN

=========================================================
CURRENT PROGRAM STATE
=========================================================

CURRENT PHASE:

CLINICAL INTELLIGENCE FOUNDATION

STATUS:

ACTIVE ✅

PURPOSE:

Finalize the intelligence architecture that powers
every clinical workflow before discipline
documentation automation is wired.

ACTIVE PROGRAM FOCUS:

Clinical Evidence Organization

CURRENT ACTIVE TASK:

ICD Intelligence Engine Verification

OBJECTIVE:

Verify and harden existing ICD recommendation,
ICD mapping,
ICD candidate,
evidence correlation,
and ontology integration architecture.

PRIMARY ARCHITECTURE RULE:

SNS organizes evidence.

SNS does not determine eligibility.

SNS does not determine prognosis.

SNS does not determine admission.

SNS exposes supporting evidence,
missing evidence,
conflicting evidence,
and source traceability.

FINAL CLINICAL AUTHORITY:

RN validates assessment truth.

Physician validates prognosis truth.

Agency validates admission readiness.

=========================================================
DISEASE INTELLIGENCE STATUS
=========================================================

STATUS:

FOUNDATION ESTABLISHED ✅

CLASSIFICATION:

NOT CURRENT ACTIVE PHASE

PURPOSE:

Disease Intelligence remains the clinical knowledge
foundation of SNS.

Oncology remains the validated reference architecture.

Cardiac, Respiratory, Neurologic, Renal, Hepatic,
and Infectious Disease hardening remain tracked work.

Disease Intelligence is not the current build focus.

CURRENT STATE:

✅ Oncology production-grade framework exists

✅ Cardiac hardening partially completed

✅ Respiratory foundation verified

✅ Disease ontology remains source of truth

✅ Evidence architecture exists

✅ ICD recommendation infrastructure exists

RULE:

Disease hardening work remains available for future
execution without creating a second source of truth.

CURRENT ACTIVE BUILD EXISTS ELSEWHERE.

No disease-family hardening is currently active.

=========================================================
MASTER PROGRAM ROADMAP
=========================================================

PHASE 1 — FOUNDATION
COMPLETE ✅

PHASE 2 — CLINICAL CORE
COMPLETE ✅

PHASE 3 — PLAN OF CARE FOUNDATION
COMPLETE ✅

PHASE 4 — DISEASE INTELLIGENCE LIBRARY
FOUNDATION ESTABLISHED ✅
NOT CURRENT ACTIVE PHASE

PHASE 5 — CLINICAL EVIDENCE INTELLIGENCE
ACTIVE ✅

PHASE 6 — ICD INTELLIGENCE ENGINE
CURRENT ACTIVE BUILD ✅

PHASE 7 — RN ICA INTELLIGENCE
QUEUED

PHASE 8 — SOCIAL WORKER ICA INTELLIGENCE
QUEUED

PHASE 9 — SPIRITUAL COUNSELOR ICA INTELLIGENCE
QUEUED

PHASE 10 — DISCIPLINE DOCUMENTATION INTELLIGENCE
QUEUED

PHASE 11 — TRANSCRIPT INTELLIGENCE
QUEUED

PHASE 12 — ELIGIBILITY SUPPORT INTELLIGENCE
QUEUED

PHASE 13 — MEDICAL DIRECTOR REVIEW INTELLIGENCE
QUEUED

PHASE 14 — IDG REVIEW INTELLIGENCE
QUEUED

PHASE 15 — RECERTIFICATION EVIDENCE BUILDER
QUEUED

PHASE 16 — RULE ENGINE + COMPLIANCE LAYER
QUEUED

PHASE 17 — AUDIT TRAIL EXPANSION
QUEUED

PHASE 18 — FINALIZATION ENGINE
QUEUED

PHASE 19 — PRODUCTION CUTOVER
QUEUED

=========================================================
ROADMAP RULE
=========================================================

Oncology is no longer the active disease family.

Oncology Structure Completion is complete ✅

Oncology Hardening is complete ✅

Oncology Production Grade review is complete ✅

System-wide Audit-Survival validation remains deferred until:

- major disease families are completed
- clinical evidence intelligence exists
- ICD intelligence exists
- discipline documentation architecture completed
- Medical Director review workflows exist
- IDG review workflows exist
- recertification evidence workflows exist
- compliance validation workflows exist
- audit reconstruction workflows exist

---------------------------------------------------------
CURRENT PHASE
---------------------------------------------------------

PHASE:

CLINICAL INTELLIGENCE FOUNDATION

STATUS:

ACTIVE ✅

PURPOSE:

Establish the intelligence architecture that powers
all clinical workflows before discipline-specific
documentation automation begins.

ARCHITECTURE:

AI Knowledge
↓
Evidence Gathering
↓
Disease Intelligence
↓
Clinical Evidence Organization
↓
ICD Intelligence
↓
RN Validation
↓
Physician Validation
↓
Documentation

PRIMARY ARCHITECTURE RULE:

SNS organizes information.

SNS exposes information.

SNS traces information.

SNS does not determine eligibility.

SNS does not determine prognosis.

SNS does not approve admission.

SNS does not replace physician judgment.

---------------------------------------------------------
CURRENT ACTIVE WORK
---------------------------------------------------------

CURRENT ACTIVE BUILD:

ICD INTELLIGENCE ENGINE

PURPOSE:

Transform incoming evidence into physician-reviewable
ICD candidates backed by source-traceable evidence.

SNS DOES:

- evidence correlation
- ontology matching
- diagnosis candidate generation
- ICD candidate generation
- confidence scoring
- supporting evidence exposure
- missing evidence exposure
- conflict detection

SNS DOES NOT:

- assign ICD codes automatically
- finalize diagnoses
- certify prognosis
- determine eligibility

FINAL AUTHORITY:

- Medical Director
- Authorized Physician
- Attending Physician where applicable

---------------------------------------------------------
CURRENT EXECUTION ORDER
---------------------------------------------------------

1. ICD Intelligence Engine

2. RN ICA Architecture Review

3. RN ICA Intelligence Wiring

4. Social Worker ICA Architecture Review

5. Social Worker ICA Intelligence Wiring

6. Spiritual Counselor ICA Architecture Review

7. Spiritual Counselor ICA Intelligence Wiring

8. Remaining Discipline Documentation

9. Transcript Intelligence Wiring

10. Clinical Evidence Intelligence Expansion

---------------------------------------------------------
CLINICAL EVIDENCE ORGANIZATION RULE
---------------------------------------------------------

SNS Hospice Solutions is a Clinical Evidence
Organization Platform.

The system organizes information already received
by the hospice agency.

Sources include:

- Hospital H&P
- Discharge Summaries
- Consult Notes
- Specialist Notes
- Referral Packets
- Face-to-Face Documentation
- Imaging Reports
- Laboratory Results
- Assessment Transcripts

SNS SHALL:

- surface supporting evidence
- surface missing evidence
- surface conflicting evidence
- maintain source traceability
- organize disease-specific findings

SNS SHALL NOT:

- determine eligibility
- determine prognosis
- approve admissions
- replace clinician judgment

RN validates assessment truth.

Physician validates prognosis truth.

Agency validates admission readiness.

---------------------------------------------------------
AFTER ICD INTELLIGENCE COMPLETION
---------------------------------------------------------

SNS MOVES TO:

1. RN ICA Intelligence

2. Social Worker ICA Intelligence

3. Spiritual Counselor ICA Intelligence

4. Remaining Discipline Documentation

5. Transcript Intelligence

6. Clinical Evidence Intelligence Expansion

7. Eligibility Support Intelligence

8. Medical Director Review Intelligence

9. IDG Review Intelligence

10. Recertification Evidence Builder

11. Rule Engine + Compliance Layer

12. Audit Trail Expansion

13. Finalization Engine

14. Production Cutover

---------------------------------------------------------
SYSTEM-WIDE AUDIT-SURVIVAL VALIDATION
---------------------------------------------------------

Performed only after:

✅ Major disease families completed

✅ Clinical Evidence Intelligence operational

✅ ICD Intelligence operational

✅ RN ICA operational

✅ Social Worker ICA operational

✅ Spiritual Counselor ICA operational

✅ Discipline Documentation operational

✅ Medical Director Review operational

✅ IDG Review operational

✅ Recertification Evidence operational

✅ Compliance workflows operational

✅ Audit Reconstruction workflows operational

---------------------------------------------------------
FINAL SYSTEM TARGET
---------------------------------------------------------

CMS / NGS / CDPH / DHS / TJC / CHAP / ACHC

Audit-Survival Hospice EMR

with:

- one ontology authority
- zero hidden logic
- evidence traceability
- recommendation traceability
- source traceability
- admission readiness support
- plan-of-care support
- interdisciplinary support
- audit reconstruction support

Clinical authority remains human.

SNS organizes truth.

Humans validate truth.

=========================================================
CURRENT VERIFIED SYSTEM STATUS
=========================================================

FOUNDATION — VERIFIED

- Tenant system ✅
- Database aligned ✅
- Core APIs operational ✅
- ORM mappings aligned ✅
- Authentication working ✅
- Admission ownership model verified ✅

---------------------------------------------------------
CLINICAL CORE — VERIFIED
---------------------------------------------------------

- Patient / Facesheet ✅
- Admission workflow ✅
- Diagnosis system of record ✅
- RN ICA ✅
- MSW ICA ✅
- SC ICA ✅
- Visit persistence ✅
- Clinical traceability ✅

---------------------------------------------------------
CRITICAL CLINICAL BEHAVIOR — VERIFIED
---------------------------------------------------------

DIAGNOSIS SYSTEM OF RECORD

- Primary diagnosis lifecycle maintained ✅
- Historical traceability preserved ✅
- No overwrite behavior ✅
- change_reason enforcement ✅

SOC OWNERSHIP MODEL

- Admission is authority for SOC ✅
- SOC date centralized ✅

CLINICAL RECORD INTEGRITY

- Initial assessments retained ✅
- Updated assessments retained ✅
- POC versions retained ✅
- Version history preserved ✅

=========================================================
CLOSED DEFECTS
=========================================================

DEFECT-001 Duplicate ICA → CLOSED ✅
DEFECT-002 Orphaned Forms → CLOSED ✅
DEFECT-003 ICD Dataset → CLOSED ✅
DEFECT-004 Admission Ownership → CLOSED ✅
DEFECT-005 Diagnosis Lifecycle → CLOSED ✅

=========================================================
COMPLETED WORK
=========================================================

---------------------------------------------------------
CLINICAL EVIDENCE ARCHITECTURE DISCOVERY
---------------------------------------------------------

STATUS:

COMPLETED ✅

VERIFIED:

✅ Ontology remains source of truth

✅ Legacy disease process retained as content source

✅ Evidence layer exists

✅ Recommendation layer exists

✅ ICD recommendation infrastructure exists

✅ Confidence model exists

✅ Alert model exists

✅ Clinical traceability exists

✅ Source traceability architecture exists

CLASSIFICATION:

Clinical Evidence Organization Architecture verified.

SNS functions as an evidence organization platform.

Clinical authority remains human.

---------------------------------------------------------
ONCOLOGY ONTOLOGY CLASSIFICATION
---------------------------------------------------------

STATUS:

COMPLETE ✅

COMPLETED:

✅ Framework ownership classification
✅ Disease-specific ownership classification
✅ Evidence ownership classification
✅ Cross-system reusable classification
✅ Oncology reusable classification

VERIFIED:

✅ NULL count = 0
✅ Parent-child integrity passed
✅ Orphan validation passed

VERIFIED COUNTS:

DISEASE_SPECIFIC = 2935
EVIDENCE = 1463
FRAMEWORK = 213
CROSS_SYSTEM_REUSABLE = 35
ONCOLOGY_REUSABLE = 25

CLASSIFICATION:

Ontology ownership classification complete.

DRAFT status remains content-governance state
and is not treated as ontology classification failure.

---------------------------------------------------------
VAGINAL CANCER
---------------------------------------------------------

STATUS:
VALIDATED ✅

CLASSIFICATION:
BUILT ✅
VALIDATED ✅
PRODUCTION GRADE REVIEW READY ⚠️
AUDIT-SURVIVAL REVIEW PENDING ⚠️

COMPLETED:
A. Disease Identity ✅
B. Symptomology ✅
C. Complications ✅
D. Prognostic Factors ✅
E. Treatment Limitations ✅
F. Functional Decline ✅
G. Nutritional Decline ✅
H. End-Stage Findings ✅
I. Hospice Eligibility ✅
J. Evidence Architecture ✅
K. Validation ✅

VALIDATION:
duplicate check = 0 ✅
orphan check = 0 ✅
hierarchy export completed ✅
keyword inventory reviewed ✅

OUTSTANDING REVIEW:
production-grade clinical review ⚠️
audit-survival review ⚠️
recommendation behavior validation ⚠️
eligibility generation validation ⚠️
evidence generation validation ⚠️
ICD recommendation validation ⚠️

---------------------------------------------------------
BLADDER CANCER
---------------------------------------------------------

STATUS:
VALIDATED ✅

CLASSIFICATION:
BUILT ✅
VALIDATED ✅
PRODUCTION GRADE REVIEW READY ⚠️
AUDIT-SURVIVAL REVIEW PENDING ⚠️

COMPLETED:
A. Disease Identity ✅
B. Symptomology ✅
C. Complications ✅
D. Prognostic Factors ✅
E. Treatment Limitations ✅
F. Functional Decline ✅
G. Nutritional Decline ✅
H. End-Stage Findings ✅
I. Hospice Eligibility ✅
J. Evidence Architecture ✅
K. Validation ✅

VERIFIED FINAL STRUCTURE:
Level 1 = 1
Level 2 = 9
Level 3 = 12
Level 4 = 109
Total = 131

VALIDATION:
duplicate check = 0 ✅
orphan check = 0 ✅
evidence architecture = 18 nodes ✅
hierarchy export completed ✅

OUTSTANDING REVIEW:
production-grade clinical review ⚠️
audit-survival review ⚠️
recommendation behavior validation ⚠️
eligibility generation validation ⚠️
evidence generation validation ⚠️
ICD recommendation validation ⚠️

---------------------------------------------------------
PENILE CANCER
---------------------------------------------------------

STATUS:
VALIDATED ✅

CLASSIFICATION:
BUILT ✅
VALIDATED ✅
PRODUCTION GRADE REVIEW READY ⚠️
AUDIT-SURVIVAL REVIEW PENDING ⚠️

COMPLETED:
A. Disease Identity ✅
B. Symptomology ✅
C. Complications ✅
D. Prognostic Factors ✅
E. Treatment Limitations ✅
F. Functional Decline ✅
G. Nutritional Decline ✅
H. End-Stage Findings ✅
I. Hospice Eligibility ✅
J. Evidence Architecture ✅
K. Validation ✅

VALIDATION:
disease-status nodes verified ✅
complications = 10 ✅
prognostic factors = 10 ✅
functional decline = 8 ✅
duplicate check = 0 ✅
orphan check = 0 ✅
hierarchy export completed ✅

OUTSTANDING REVIEW:
production-grade clinical review ⚠️
audit-survival review ⚠️
recommendation behavior validation ⚠️
eligibility generation validation ⚠️
evidence generation validation ⚠️
ICD recommendation validation ⚠️

---------------------------------------------------------
VULVAR CANCER
---------------------------------------------------------

STATUS:
VALIDATED ✅

CLASSIFICATION:
BUILT ✅
VALIDATED ✅
PRODUCTION GRADE REVIEW READY ⚠️
AUDIT-SURVIVAL REVIEW PENDING ⚠️

COMPLETED:
A. Disease Identity ✅
B. Symptomology ✅
C. Complications ✅
D. Prognostic Factors ✅
E. Treatment Limitations ✅
F. Functional Decline ✅
G. Nutritional Decline ✅
H. End-Stage Findings ✅
I. Hospice Eligibility ✅
J. Evidence Architecture ✅
K. Validation ✅

VERIFIED COUNTS:
symptomology = 21 ✅
complications = 13 ✅
prognostic factors = 10 ✅
treatment limitations = 10 ✅
functional decline = 8 ✅
nutritional decline = 8 ✅
end-stage findings = 10 ✅
hospice eligibility = 10 ✅
evidence architecture = 15 ✅

VALIDATION:
duplicate check = 0 ✅
orphan check = 0 ✅

OUTSTANDING REVIEW:
production-grade clinical review ⚠️
audit-survival review ⚠️
recommendation behavior validation ⚠️
eligibility generation validation ⚠️
evidence generation validation ⚠️
ICD recommendation validation ⚠️

---------------------------------------------------------
PROSTATE CANCER
---------------------------------------------------------

STATUS:
VALIDATED ✅

CLASSIFICATION:
BUILT ✅
VALIDATED ✅
PRODUCTION GRADE REVIEW READY ⚠️
AUDIT-SURVIVAL REVIEW PENDING ⚠️

COMPLETED:
A. Disease Identity ✅
B. Symptomology ✅
C. Complications ✅
D. Prognostic Factors ✅
E. Treatment Limitations ✅
F. Functional Decline ✅
G. Nutritional Decline ✅
H. End-Stage Findings ✅
I. Hospice Eligibility ✅
J. Evidence Architecture ✅
K. Validation ✅

VERIFIED COUNTS:
symptomology:
common = 6 ✅
uncommon = 5 ✅
advanced = 5 ✅
rare = 5 ✅
total symptomology = 21 ✅

complications = 10 ✅
prognostic factors = 12 ✅
treatment limitations = 10 ✅
functional decline = 8 ✅
nutritional decline = 8 ✅
end-stage findings = 10 ✅
hospice eligibility = 10 ✅
evidence architecture = 21 ✅

VALIDATION:
duplicate check = 0 ✅
orphan check = 0 ✅

NOTABLE REPAIR:
prostate_refractory_urinary_obstruction already existed under prostate_end_stage_findings.
prostate_refractory_urinary_obstruction_symptom was created under prostate_rare_symptomology to avoid duplicate canonical keyword ownership.

OUTSTANDING REVIEW:
production-grade clinical review ⚠️
audit-survival review ⚠️
recommendation behavior validation ⚠️
eligibility generation validation ⚠️
evidence generation validation ⚠️
ICD recommendation validation ⚠️

---------------------------------------------------------
PRIMARY PERITONEAL CARCINOMA
---------------------------------------------------------

STATUS:
PRODUCTION GRADE ✅

CLASSIFICATION:
BUILT ✅
VALIDATED ✅
PRODUCTION GRADE ✅
AUDIT-SURVIVAL REVIEW PENDING ⚠️

COMPLETED:

A. Disease Identity
✅ primary_peritoneal_carcinoma
✅ primary_peritoneal_serous_carcinoma
✅ high-grade serous classification

B. Symptomology
✅ common symptomology
✅ uncommon symptomology
✅ rare symptomology
✅ symptom evidence architecture

C. Complications
✅ malignant ascites
✅ peritoneal carcinomatosis
✅ bowel obstruction
✅ recurrent bowel obstruction
✅ gastric outlet obstruction
✅ refractory ascites
✅ ureteral obstruction
✅ hydronephrosis
✅ pleural effusion
✅ malignant pleural effusion
✅ DVT
✅ pulmonary embolism
✅ cachexia
✅ recurrent infection
✅ severe anemia
✅ multi-organ failure

D. Prognostic Factors
✅ histology factors
✅ metastatic burden
✅ poor performance status
✅ platinum resistance
✅ ascites
✅ carcinomatosis
✅ obstruction
✅ pleural effusion
✅ hydronephrosis
✅ DVT
✅ PE

E. Treatment Limitations
✅ failed chemotherapy
✅ failed first-line therapy
✅ failed second-line therapy
✅ failed targeted therapy
✅ failed bevacizumab
✅ failed PARP inhibitor
✅ platinum resistance
✅ progressive despite treatment

F. Functional Decline
✅ weakness
✅ reduced mobility
✅ ADL dependence
✅ homebound
✅ bedbound
✅ PPS decline
✅ ECOG decline

G. Nutritional Decline
✅ weight loss
✅ poor intake
✅ anorexia
✅ early satiety
✅ cachexia
✅ muscle wasting
✅ dehydration
✅ protein calorie malnutrition
✅ severe malnutrition

H. End-Stage Findings
✅ terminal decline
✅ refractory symptoms
✅ refractory pain
✅ minimal intake
✅ cachexia
✅ imminent death findings
✅ actively dying
✅ multi-organ failure

I. Hospice Eligibility
✅ progression indicators
✅ treatment limitation indicators
✅ functional decline indicators
✅ nutritional decline indicators
✅ disease-specific eligibility indicators

J. Evidence Architecture
✅ diagnosis evidence
✅ imaging evidence
✅ symptom evidence
✅ complication evidence
✅ treatment evidence
✅ decline evidence
✅ prognostic evidence

K. Validation
✅ inventory validation completed
✅ hierarchy validation completed
✅ duplicate check = 0
✅ orphan check = 0

OUTSTANDING REVIEW:

⚠️ Audit-survival review
⚠️ Recommendation behavior validation
⚠️ Eligibility generation validation
⚠️ Evidence generation validation
⚠️ ICD recommendation validation

---------------------------------------------------------
CHF DISEASE FAMILY — COMPLETED / VALIDATED
---------------------------------------------------------

STATUS:
COMPLETE ✅

COMPLETED:

- CHF ontology verified ✅
- CHF hierarchy verified ✅
- CHF subtype classification verified ✅
- CHF progression hierarchy verified ✅
- CHF treatment limitation hierarchy verified ✅
- CHF cachexia hierarchy verified ✅
- CHF evidence rules verified ✅
- CHF diagnosis evidence verified ✅
- CHF episode evidence verified ✅
- CHF validation completed ✅

VERIFIED CHF OUTPUTS:

- episode_evidence populated for CHF ✅
- diagnosis_evidence populated for CHF ✅

CLASSIFICATION:

CHF is completed MVP disease family.

CHF is not the active phase.

CHF belongs in completed work.

---------------------------------------------------------
RN ICA EXTRACTION ENGINE
---------------------------------------------------------

STATUS:
COMPLETE ✅

COMPLETED:

- canonical keyword derivation ✅
- alias resolution ✅
- free-text extraction ✅
- deterministic compilation ✅
- keyword deduplication ✅
- problem identity mapping ✅
- outcome rule lookup integration ✅
- intervention rule lookup integration ✅
- problem-node generation ✅

VERIFIED OUTPUT PIPELINE:

RN ICA
↓
Free Text Extraction
↓
Alias Resolution
↓
Canonical Keywords
↓
Outcome Rules
↓
Intervention Rules
↓
POC Problems

VERIFIED RN ICA EXTRACTION DOMAINS:

Disease / Diagnosis Extraction Domains:

- CHF ✅
- CARDIAC_DISEASE ✅
- COPD ✅
- RESPIRATORY_FAILURE ✅
- CANCER ✅
- METASTATIC ✅
- DEMENTIA ✅
- CVA ✅
- NEURO_DEGENERATIVE ✅
- ESRD ✅
- LIVER_FAILURE ✅
- INFECTION ✅
- GENERAL_DECLINE ✅

Symptom / Functional Domains:

- PAIN ✅
- DYSPNEA ✅
- FATIGUE ✅
- APPETITE_DECLINE ✅
- ANXIETY ✅
- EDEMA ✅
- FALL_RISK ✅
- CAREGIVER_SUPPORT ✅
- WOUND_SKIN_INTEGRITY ✅
- SLEEP_DISTURBANCE ✅
- CONFUSION_DELIRIUM ✅
- NAUSEA_VOMITING ✅
- DEPRESSION ✅

Clinical Management Domains:

- MEDICATION_MANAGEMENT ✅
- CONSTIPATION ✅
- SPIRITUAL_DISTRESS ✅
- GRIEF_BEREAVEMENT ✅
- SEIZURE_DISORDER ✅
- TOXICITY ✅

IMPORTANT CLASSIFICATION NOTE:

RN ICA extraction domains are verified as keyword detection and POC-rule trigger domains.

RN ICA extraction coverage does not equal complete disease intelligence coverage.

Disease intelligence is tracked separately.

---------------------------------------------------------
POC SYSTEM-OF-RECORD FOUNDATION
---------------------------------------------------------

STATUS:
FOUNDATION COMPLETE ✅

COMPLETED:

- plan_of_care root model ✅
- plan_of_care_versions ✅
- snapshot_json source of truth ✅
- poc_problems projection ✅
- poc_goals projection ✅
- poc_interventions projection ✅
- poc_evidence_links model ✅
- poc_review_events model ✅
- version chain design ✅

SOURCE OF TRUTH RULE:

Canonical source:

- plan_of_care_versions.snapshot_json ✅

Derived projection:

- poc_problems ✅
- poc_goals ✅
- poc_interventions ✅

Rule:

- normalized POC tables are derived from version snapshot
- no second care-plan source outside version snapshot
- no hidden manual-only logic path

=========================================================
ONTOLOGY SOURCE OF TRUTH RULE
=========================================================

RULE:

hospice_canonical_keyword is the intended SNS AI ontology brain.

The ontology supports:

1. Disease recognition
2. Disease subtype classification
3. ICD candidate recommendation support
4. Progression recognition
5. Treatment limitation / treatment failure recognition
6. Complication recognition
7. Evidence-backed interdisciplinary recommendation generation
8. POC intelligence support
9. Future eligibility evidence support
10. Future Medical Director review support
11. Future IDG discussion support
12. Future recertification support

ONTOLOGY IS NOT:

- a nursing checklist
- a static monitoring checklist
- a visit template
- a POC template
- an assessment template
- a replacement for clinician judgment
- an automatic ICD assignment engine

ONTOLOGY IS:

- the AI disease intelligence brain
- the disease classification engine
- the subtype classification engine
- the ICD recommendation support engine
- the progression recognition engine
- the treatment limitation recognition engine
- the complication recognition engine
- the recommendation logic source

SNS DOES NOT:

- assign ICD codes automatically
- replace physician judgment
- finalize diagnosis decisions
- use AI as the diagnosing authority

SNS DOES:

- harvest evidence
- organize evidence
- correlate evidence against canonical ontology
- recommend ICD candidates for physician review
- show supporting evidence
- generate disease-specific recommendations for staff based on ontology and patient evidence
- distribute pertinent information across disciplines

FINAL DIAGNOSIS AUTHORITY:

- Medical Director / authorized physician
- attending physician where applicable
- final documentation remains provider-driven

VERIFIED:

Ontology ownership model completed.

knowledge_scope is now fully classified across all ontology records.

knowledge_scope defines ownership.

classification_status defines governance/review state.

NULL ownership values are not permitted.

=========================================================
VERIFIED ARCHITECTURE DISCOVERY
=========================================================

SOURCE OF TRUTH RULE:

hospice_canonical_keyword remains the SNS AI disease intelligence source of truth.

The ontology is the authority for:

- disease recognition
- disease classification
- subtype classification
- primary site classification
- organ classification
- anatomical region classification
- metastatic classification
- prognostic factor classification
- treatment limitation classification
- complication classification
- ICD recommendation support
- evidence recommendation support

No second disease intelligence source of truth is allowed.

---------------------------------------------------------
LEGACY KNOWLEDGE SYSTEM DISCOVERY
---------------------------------------------------------

Verified legacy authored knowledge system exists:

Root Table:

- hospice_disease_process ✅

Verified disease process records:

- END_STAGE_HEART_FAILURE ✅
- ALZHEIMERS_ADVANCED ✅
- G31_1_SENILE_DEGENERATION ✅
- COPD_ADVANCED ✅
- CANCER_ADVANCED ✅

Verified dependent authored knowledge tables:

- hospice_disease_finding ✅
- hospice_disease_complication ✅
- hospice_disease_clinical_intervention ✅
- hospice_disease_medical_intervention ✅
- hospice_disease_teaching ✅
- hospice_disease_outcome ✅
- hospice_problem_library ✅
- hospice_scale_disease_map ✅
- hospice_test_case ✅
- patient_problem ✅

CLASSIFICATION:

Legacy system contains significant authored hospice knowledge and cannot be treated as disposable content.

The legacy system is not the disease intelligence authority.

The legacy system is a clinical content repository.

---------------------------------------------------------
CLINICAL FINDING ENGINE DISCOVERY
---------------------------------------------------------

Verified:

hospice_disease_finding functions as a finding library.

Verified structure includes:

- disease_process_id ✅
- finding_name ✅
- finding_category ✅
- commonality ✅
- clinical_description ✅
- finding_code ✅
- hnp_keywords ✅
- lab_keywords ✅
- imaging_keywords ✅
- assessment_keywords ✅
- objective_finding ✅
- subjective_finding ✅

Verified architecture:

Disease Process
↓
Finding
↓
Problem Mapping
↓
Care Planning Support

CLASSIFICATION:

hospice_disease_finding is not merely a symptom table.

It is a disease-to-finding intelligence layer containing authored hospice clinical knowledge.

---------------------------------------------------------
FINDING → PROBLEM MAPPING DISCOVERY
---------------------------------------------------------

Verified table:

- hospice_finding_problem_map ✅

Verified structure:

- finding_id ✅
- problem_id ✅
- confidence_score ✅
- active ✅

Verified behavior:

Finding
↓
Problem
↓
Confidence

This represents an existing reasoning layer already connected to hospice authored knowledge.

---------------------------------------------------------
EVIDENCE ARCHITECTURE DISCOVERY
---------------------------------------------------------

Verified evidence infrastructure exists:

- diagnosis_evidence ✅
- episode_evidence ✅
- patient_evidence ✅
- hospice_eligibility_evidence ✅
- oncology_evidence_harvest_log ✅

Verified evidence attributes include:

- evidence_text ✅
- evidence_summary ✅
- evidence_source ✅
- evidence_source_type ✅
- evidence_severity ✅
- alert_priority ✅

CLASSIFICATION:

SNS already contains a dedicated evidence layer.

---------------------------------------------------------
RECOMMENDATION ARCHITECTURE DISCOVERY
---------------------------------------------------------

Verified recommendation infrastructure exists:

- clinical_reasoning_profiles ✅
- clinical_reasoning_results ✅
- diagnosis_recommendations ✅
- diagnosis_review ✅

Verified capabilities include:

- required_evidence ✅
- supporting_evidence ✅
- excluding_evidence ✅
- matched_evidence ✅
- missing_evidence ✅
- recommended_diagnosis ✅
- recommended_icd10 ✅
- evidence_summary ✅
- evidence_confidence ✅

CLASSIFICATION:

Recommendation infrastructure exists.

The remaining work is ontology integration and evidence generation validation.

---------------------------------------------------------
ICD SUPPORT ARCHITECTURE DISCOVERY
---------------------------------------------------------

Verified ICD recommendation infrastructure exists:

- icd10_canonical_keyword_map ✅
- icd10_canonical_keyword_rule ✅
- hospice_icd_priority_candidate ✅

Verified capabilities include:

- recommendation confidence ✅
- physician review requirement ✅
- priority classification ✅
- audit support ✅

CLASSIFICATION:

SNS supports ICD candidate recommendations.

SNS does not automatically assign ICD codes.

Final diagnosis authority remains:

- Medical Director
- Authorized Physician
- Attending Physician where applicable

---------------------------------------------------------
CONFIDENCE MODEL DISCOVERY
---------------------------------------------------------

Verified confidence scoring exists in multiple layers.

Observed:

- finding confidence ✅
- mapping confidence ✅
- recommendation confidence ✅
- ICD recommendation confidence ✅

CLASSIFICATION:

SNS supports confidence-assisted recommendations.

Confidence supports evidence strength.

Confidence does not replace provider judgment.

---------------------------------------------------------
ALERT MODEL DISCOVERY
---------------------------------------------------------

Verified architecture supports:

- evidence severity ✅
- alert priority ✅
- recommendation review workflows ✅
- notification infrastructure ✅

Future intended behavior:

Evidence
↓
Finding
↓
Ontology
↓
Recommendation
↓
Review Alert
↓
Medical Director Review

SNS may recommend.

SNS may alert.

SNS may present evidence.

SNS may not finalize diagnosis.

SNS may not automatically assign ICD codes.

---------------------------------------------------------
ONE SOURCE OF TRUTH ENFORCEMENT
---------------------------------------------------------

Verified long-term ownership model:

hospice_canonical_keyword
        ↓
Ontology Authority

Legacy authored knowledge
        ↓
Mapped Content Source

Evidence
        ↓
Supporting Proof Layer

Recommendations
        ↓
Review Support Layer

ICD Candidate Support
        ↓
Physician Review Layer

Rule:

No duplicate disease intelligence engines.

No duplicate oncology source of truth.

No duplicate symptom engines.

No duplicate ICD logic engines.

One ontology authority.

Zero hidden logic.

---------------------------------------------------------
ONC-001 — ONCOLOGY SOURCE OF TRUTH GOVERNANCE
---------------------------------------------------------

STATUS:

COMPLETED ✅

CLASSIFICATION:

GOVERNANCE CONTROL

RESULT:

✅ canonical ontology remains source of truth

✅ no duplicate oncology source of truth exists

✅ no duplicate disease intelligence engine exists

✅ no duplicate symptom engine exists

✅ no duplicate ICD logic engine exists

✅ legacy knowledge preserved as content source

✅ evidence retained as proof layer

✅ recommendations retained as review layer

OWNERSHIP:

Governance completed and operating as an ongoing
system rule.

NOT CURRENT PHASE.

---------------------------------------------------------
ONC-002 — ONCOLOGY AUDIT-SURVIVAL DISEASE STANDARD
---------------------------------------------------------

STATUS:

COMPLETED ✅

CLASSIFICATION:

PRODUCTION-GRADE DISEASE STANDARD

RESULT:

✅ A-K completion standard established

✅ Oncology disease families reviewed against A-K

✅ Built status separated from Validated status

✅ Validated status separated from Production Grade status

✅ Audit-Survival status separated from Production Grade status

✅ Oncology serves as reference model for future disease family hardening

OWNERSHIP:

Standard established and reused by all future
disease families.

NOT CURRENT PHASE.

---------------------------------------------------------
ONC-005 — ONCOLOGY EVIDENCE ARCHITECTURE COMPLETION
---------------------------------------------------------

STATUS:

COMPLETED ✅

CLASSIFICATION:

EVIDENCE ARCHITECTURE STANDARD

RESULT:

✅ diagnosis evidence standardized

✅ imaging evidence standardized

✅ symptom evidence standardized

✅ complication evidence standardized

✅ treatment evidence standardized

✅ decline evidence standardized

✅ prognostic evidence standardized

✅ eligibility evidence standardized

✅ oncology evidence architecture normalized

OWNERSHIP:

Evidence architecture completed and reused for
future disease family hardening.

NOT CURRENT PHASE.

---------------------------------------------------------
ONC-006 — ONCOLOGY EXTRACTION RULE VALIDATION
---------------------------------------------------------

STATUS:

QUEUED — SYSTEM-WIDE VALIDATION

TRACKED IN:

GLOBAL AUDIT-SURVIVAL VALIDATION QUEUE

DEPENDENCY:

System-Wide Extraction Behavior Validation

CURRENT PHASE:

NOT ACTIVE

PURPOSE:

Validate extraction behavior after major disease
families and clinical intelligence workflows are completed.

---------------------------------------------------------
ONC-007 — ONCOLOGY EVIDENCE GENERATION VALIDATION
---------------------------------------------------------

STATUS:

QUEUED — SYSTEM-WIDE VALIDATION

TRACKED IN:

GLOBAL AUDIT-SURVIVAL VALIDATION QUEUE

DEPENDENCY:

System-Wide Evidence Generation Validation

CURRENT PHASE:

NOT ACTIVE

PURPOSE:

Validate evidence generation behavior after
system-wide intelligence workflows are completed.

---------------------------------------------------------
ONC-008 — ONCOLOGY ICD RECOMMENDATION VALIDATION
---------------------------------------------------------

STATUS:

QUEUED — SYSTEM-WIDE VALIDATION

TRACKED IN:

GLOBAL AUDIT-SURVIVAL VALIDATION QUEUE

DEPENDENCY:

System-Wide ICD Recommendation Validation

CURRENT PHASE:

NOT ACTIVE

PURPOSE:

Validate ICD recommendation behavior after
system-wide recommendation workflows are completed.

---------------------------------------------------------
ONC-009 — ONCOLOGY RECOMMENDATION BEHAVIOR VALIDATION
---------------------------------------------------------

STATUS:

QUEUED — SYSTEM-WIDE VALIDATION

TRACKED IN:

GLOBAL AUDIT-SURVIVAL VALIDATION QUEUE

DEPENDENCY:

System-Wide Recommendation Behavior Validation

CURRENT PHASE:

NOT ACTIVE

PURPOSE:

Validate staff-facing recommendation behavior after
system-wide recommendation workflows are completed.

---------------------------------------------------------
ONC-010 — LEGACY ONCOLOGY KNOWLEDGE INTEGRATION VALIDATION
---------------------------------------------------------

STATUS:

QUEUED — SYSTEM-WIDE VALIDATION

TRACKED IN:

GLOBAL AUDIT-SURVIVAL VALIDATION QUEUE

DEPENDENCY:

System-Wide Legacy Knowledge Integration Validation

CURRENT PHASE:

NOT ACTIVE

PURPOSE:

Validate long-term legacy knowledge integration
without creating duplicate disease intelligence authority.

=========================================================
LEGACY DISEASE PROCESS STATUS
=========================================================

STATUS:
ACTIVE LEGACY KNOWLEDGE SYSTEM ⚠️

DO NOT DROP.

DO NOT REPLACE.

DO NOT DUPLICATE.

CLASSIFICATION:

Legacy system is not the disease intelligence authority.

Legacy system is an authored hospice knowledge repository.

It contains:

- findings
- complications
- interventions
- teaching
- outcomes
- problem relationships
- confidence mappings

The ontology contains:

- disease intelligence
- classification intelligence
- anatomy intelligence
- progression intelligence
- complication intelligence
- recommendation intelligence

LONG-TERM MODEL:

Ontology
↓
Authority

Legacy Knowledge
↓
Content Provider

Evidence
↓
Proof Layer

Recommendations
↓
Review Layer

VERIFIED RULE:

The objective is integration.

The objective is not replacement.

The objective is not coexistence of competing disease engines.

The objective is a single ontology authority enhanced by preserved legacy authored clinical knowledge.

=========================================================
LEGACY MIGRATION BACKLOG
=========================================================

STATUS:
NOT CURRENT PHASE

RULE:

Legacy migration is queued until canonical disease family structures are stable enough for safe migration.

MIG-001 — OLD TO NEW OWNERSHIP MAP

END_STAGE_HEART_FAILURE
→ cardiac > chf > end_stage_chf
→ advanced_heart_disease
→ heart_failure_progression

COPD_ADVANCED
→ respiratory > copd > end_stage_copd
→ advanced_respiratory_disease
→ respiratory_progression

ALZHEIMERS_ADVANCED
→ neurology > dementia > alzheimer_dementia

G31_1_SENILE_DEGENERATION
→ neurology > dementia
→ future specific canonical node if clinically required

CANCER_ADVANCED
→ oncology > cancer
→ primary site
→ anatomic subsite
→ metastatic site
→ treatment status
→ prognostic factors
→ complications

MIG-002 — PRESERVE AUTHORED KNOWLEDGE

All authored findings, complications, interventions, teaching, and outcomes must be preserved.

No legacy authored content may be discarded without review.

MIG-003 — IMPROVE GENERIC CONTENT

Legacy content must be upgraded from generic hospice wording into ontology-driven disease intelligence.

MIG-004 — RETIRE LEGACY STRUCTURE

Retirement is allowed only after:

- all findings mapped
- all complications mapped
- all interventions mapped
- all teaching mapped
- all outcomes mapped
- patient_problem migrated
- hospice_problem_library migrated
- hospice_scale_disease_map migrated
- hospice_test_case migrated
- runtime behavior verified
- no consumer still requires hospice_disease_process
- no consumer still requires disease_profiles

=========================================================
NOT CURRENT FOCUS
=========================================================

Do not work on:

- Admission Narrative Generator
- Medical Director Narrative Generator
- IDG Evidence Builder
- Recertification Evidence Builder
- final audit-locking rules
- immutable records
- production finalization logic
- new diagnosis table
- new disease profile table
- new disease process table
- dropping hospice_disease_process
- dropping disease_profiles

- Cardiac Hardening
- Respiratory Hardening
- Neurologic Hardening
- Renal Hardening
- Hepatic Hardening
- Infectious Disease Hardening

until ICD Intelligence foundation work is completed.

Reason:

Current active phase is Clinical Intelligence Foundation.

Current active build is ICD Intelligence Engine.

Disease hardening remains available but is not current focus.

=========================================================
POC ENGINE — ICA → POC MAPPING SCHEMA
=========================================================

STATUS:
ACTIVE FOUNDATION / NOT CURRENT BUILD FOCUS

OWNER:
POC SYSTEM-OF-RECORD

MODE:
ONE SOURCE OF TRUTH / ZERO HIDDEN LOGIC

PURPOSE:

Convert interdisciplinary ICA findings into one authoritative hospice Plan of Care that is:

- versioned ✅
- traceable ✅
- assessment-derived ✅
- interdisciplinary ✅
- audit-safe later ✅
- flexible during field testing ✅

ROOT MODEL:

plan_of_care

Purpose:

- stable admission-level root record
- anchors version chain

Rules:

- one active root POC per admission
- root points to current active version

VERSION MODEL:

plan_of_care_versions

Purpose:

- canonical versioned POC source
- stores snapshot_json

Source of truth:

- plan_of_care_versions.snapshot_json ✅

Projection tables:

- poc_problems ✅
- poc_goals ✅
- poc_interventions ✅

Rules:

- one active version at a time ✅
- previous active version becomes superseded ✅
- assessment-driven changes create new version ✅
- based_on_version_id preserves chain ✅
- projections regenerate from snapshot ✅

EVIDENCE LINKING MODEL:

poc_evidence_links

Purpose:

- trace POC nodes back to clinical evidence

IDG REVIEW MODEL:

poc_review_events

Purpose:

- capture interdisciplinary review state without enabling production locks during field testing

ICA → POC DOMAIN MAPPING:

RN ICA feeds:

- physical ✅
- safety ✅
- care coordination ✅

MSW ICA feeds:

- psychosocial ✅
- caregiver support ✅
- resource / financial ✅
- social risk ✅

SC ICA feeds:

- spiritual ✅
- belief / ritual ✅
- existential distress ✅
- meaning / end-of-life support ✅

COMPILER RULES:

1. deterministic compile
2. one compiler/service layer
3. forward-only versioning
4. one edit path
5. snapshot first
6. projection rebuilt from snapshot

FIELD TESTING RULE:

Allowed:

- version regeneration ✅
- corrections ✅
- replacement versions ✅
- deletion if operationally required ✅

Disabled:

- irreversible locking ❌
- immutable finalized POC ❌
- amendment-only enforcement ❌

=========================================================
SUCCESS CRITERIA — CURRENT PHASE
=========================================================

Current phase is successful when:

1. ICD recommendation architecture verified

2. ICD recommendation sources verified

3. ICD candidate generation verified

4. Ontology correlation verified

5. Supporting evidence correlation verified

6. Missing evidence detection verified

7. Conflicting evidence detection verified

8. Source traceability verified

9. No duplicate ICD authority exists

10. Canonical ontology remains source of truth

11. No hidden logic exists

12. Physician review workflow preserved

13. ICD recommendations remain recommendation-only

14. No automatic diagnosis assignment exists

CURRENT ACTIVE PHASE:

CLINICAL INTELLIGENCE FOUNDATION

CURRENT ACTIVE BUILD:

ICD INTELLIGENCE ENGINE

=========================================================
EXIT CRITERIA — CURRENT PHASE
=========================================================

Current phase is complete when:

1. ICD architecture verified

2. ICD source tables verified

3. ICD recommendation workflow verified

4. Ontology linkage verified

5. Supporting evidence linkage verified

6. Missing evidence detection verified

7. Conflicting evidence detection verified

8. Physician review pathway verified

9. Recommendation traceability verified

10. Source traceability verified

11. Canonical ontology remains source of truth

12. No duplicate intelligence authority exists

THEN:

STATUS:

ICD INTELLIGENCE ENGINE COMPLETE ✅

NEXT ACTIVE PHASE:

RN ICA INTELLIGENCE

NEXT ACTIVE BUILD:

RN ICA ARCHITECTURE REVIEW

FOLLOWED BY:

1. RN ICA Intelligence
2. Social Worker ICA Intelligence
3. Spiritual Counselor ICA Intelligence
4. Discipline Documentation Intelligence
5. Transcript Intelligence

=========================================================
EVIDENCE / VERIFIED RESULTS
=========================================================

SYSTEM VALIDATION

✅ API response success
✅ DB persistence verified
✅ Repeated execution stable

---------------------------------------------------------
CLINICAL TRACEABILITY
---------------------------------------------------------

✅ Diagnosis changes tracked
✅ Timestamps present
✅ User attribution present

---------------------------------------------------------
RN ICA EXTRACTION VALIDATION
---------------------------------------------------------

Validated Extraction Domains:

Disease Domains

✅ CARDIAC_DISEASE
✅ CHF
✅ COPD
✅ RESPIRATORY_FAILURE
✅ CANCER
✅ METASTATIC_DISEASE
✅ DEMENTIA
✅ CVA
✅ ESRD
✅ LIVER_FAILURE
✅ INFECTION
✅ GENERAL_DECLINE

Symptom / Functional Domains

✅ PAIN
✅ DYSPNEA
✅ FATIGUE
✅ APPETITE_DECLINE
✅ FALL_RISK
✅ CAREGIVER_SUPPORT

Validated Engines

✅ _extract_keywords_from_text
✅ _derive_keywords_from_rn_ica

---------------------------------------------------------
DISEASE INTELLIGENCE VALIDATION
---------------------------------------------------------

CARDIAC

✅ CHF hierarchy verified
✅ End-stage CHF verified
✅ Refractory CHF verified
✅ EF indicators verified
✅ NYHA indicators verified
✅ Cachexia indicators verified
✅ Progression containers verified
✅ CHF evidence generated
✅ CHF diagnosis evidence generated
✅ CHF validation completed

RESPIRATORY

✅ COPD hierarchy verified
✅ Chronic respiratory failure verified
✅ Pulmonary fibrosis verified
✅ Oxygen dependence verified
✅ Hypercapnia verified
✅ Hospitalization burden verified
✅ Cachexia indicators verified

⚠ Evidence generation validation pending

---------------------------------------------------------
ONCOLOGY COMPLETION STATUS
---------------------------------------------------------

STATUS:

COMPLETED ✅

CLASSIFICATION:

✅ STRUCTURE COMPLETE

✅ HARDENING COMPLETE

✅ PRODUCTION GRADE

⚠ AUDIT-SURVIVAL VALIDATION DEFERRED

REASON:

Audit-Survival validation requires completion of
system-wide clinical intelligence workflows,
eligibility workflows,
recommendation workflows,
documentation workflows,
interdisciplinary review workflows,
audit reconstruction workflows,
and compliance validation workflows.

Oncology cannot independently achieve
Audit-Survival Complete status until those
system-level dependencies are available.

COMPLETED WORK:

✅ Oncology ontology normalization

✅ Reproductive / GU Oncology completed

✅ GI Oncology completed

✅ Thoracic Oncology completed

✅ Hematologic Oncology completed

✅ Neuro Oncology completed

✅ Head & Neck Oncology completed

✅ Integumentary Oncology completed

✅ Musculoskeletal / Sarcoma Oncology completed

✅ Metastatic architecture normalized

✅ Legacy metastatic root retired

✅ metastatic_disease established as single source of truth

✅ Metastatic destination architecture completed

Destination Architecture:

✅ Bone

✅ Brain

✅ Liver

✅ Lung

✅ Lymph Node

✅ Peritoneum

✅ Pleura

✅ Adrenal

✅ Skin

✅ Soft Tissue

✅ Oncology evidence architecture standardized

Evidence Domains:

✅ Diagnosis Evidence

✅ Imaging Evidence

✅ Symptom Evidence

✅ Complication Evidence

✅ Treatment Evidence

✅ Decline Evidence

✅ Prognostic Evidence

✅ Eligibility Evidence

✅ Oncology complication architecture standardized

✅ Oncology prognostic architecture standardized

✅ Oncology hospice eligibility architecture standardized

✅ Oncology ICD mapping normalization completed

✅ Duplicate validation passed

✅ Orphan validation passed

✅ Parent-child integrity validated

✅ Ontology ownership validation completed

RESULT:

Oncology serves as the reference disease model
for Cardiac, Respiratory, Neurologic, Renal,
Hepatic, and Infectious Disease hardening.

---------------------------------------------------------
ONCOLOGY SEARCH FOUNDATION
---------------------------------------------------------

✅ canonical_keyword_synonym established

✅ synonym_type implemented

✅ search_context implemented

✅ search_weight implemented

✅ Duplicate synonym validation passed

Schema Verified:

✅ canonical_keyword
✅ synonym
✅ synonym_type
✅ search_context
✅ search_weight

---------------------------------------------------------
GLOBAL AUDIT-SURVIVAL VALIDATION QUEUE
---------------------------------------------------------

STATUS:

DEFERRED — NOT CURRENT PHASE

PURPOSE:

System-wide validation performed after major
disease families and clinical intelligence
workflows are completed.

VALIDATION ITEMS:

⚠ Extraction Behavior Validation

⚠ Evidence Generation Validation

⚠ ICD Recommendation Validation

⚠ Recommendation Behavior Validation

⚠ Legacy Knowledge Integration Validation

⚠ Eligibility Intelligence Validation

⚠ Medical Director Workflow Validation

⚠ IDG Workflow Validation

⚠ Audit Reconstruction Validation

⚠ Compliance Validation

DEPENDENCY:

Major disease families completed and hardened.

CURRENT PRIORITY:

1. ICD Intelligence Engine
2. RN ICA Intelligence
3. Social Worker ICA Intelligence
4. Spiritual Counselor ICA Intelligence
5. Discipline Documentation Intelligence
6. Transcript Intelligence

---------------------------------------------------------
REPRODUCTIVE / GU ONCOLOGY
---------------------------------------------------------

STATUS:

COMPLETE ✅

Validated Disease Families

✅ Breast Cancer
✅ Ovarian Cancer
✅ Cervical Cancer
✅ Endometrial Cancer
✅ Uterine Cancer
✅ Fallopian Tube Cancer
✅ Vaginal Cancer
✅ Vulvar Cancer
✅ Bladder Cancer
✅ Penile Cancer
✅ Prostate Cancer
✅ Gestational Trophoblastic Neoplasia
✅ Testicular Cancer

Validation Results

✅ Duplicate Query = 0
✅ Orphan Query = 0
✅ Hierarchy Validation Completed
✅ Evidence Architecture Reviewed
✅ Disease Identity Reviewed
✅ Prognostic Structure Reviewed
✅ Eligibility Structure Reviewed

Classification

✅ BUILT
✅ VALIDATED
✅ PRODUCTION GRADE

AUDIT-SURVIVAL COMPLETE NOT YET CLAIMED

=========================================================
NEXT PHASE QUEUE — NOT ACTIVE
=========================================================

The following items are queued only.

=========================================================
PLATFORM SEARCH BACKLOG
=========================================================

STATUS:
QUEUED — NOT ACTIVE

DEPENDENCY:

Disease Intelligence Hardening substantially complete across major disease families.

Minimum:

- Cardiac Hardening complete
- Respiratory Hardening complete
- Neurologic / Dementia complete
- Renal complete
- Hepatic complete
- Infectious Disease complete

---------------------------------------------------------
ICD-TYPEAHEAD-001
SMART ICD SEARCH
---------------------------------------------------------

PURPOSE:

Accelerate clinical documentation by allowing
diagnosis retrieval through ICD code,
diagnosis description,
and common clinical terminology.

SEARCH SOURCES:

- ICD code
- ICD description
- diagnosis synonym

DISPLAY:

- ICD code
- diagnosis description
- diagnosis location

---------------------------------------------------------
ICD-TYPEAHEAD-002
COMMON DIAGNOSIS VOCABULARY
---------------------------------------------------------

PURPOSE:

Provide common clinical diagnosis terminology
not present in ICD descriptions.

INITIAL VOCABULARY:

CHF
COPD
DM
DM2
CKD
ESRD
CAD
PVD
PAD
TIA
CVA
AFIB
DVT
PE
GERD
IBS
UTI
PNA
HTN

RULE:

Only diagnosis terminology belongs here.

Assessment tools do not belong here.

Excluded:

PPS
KPS
ECOG
FAST
ADL

---------------------------------------------------------
ICD-TYPEAHEAD-003
SEARCH RANKING ENGINE
---------------------------------------------------------

PURPOSE:

Provide consistent diagnosis retrieval ranking.

RANKING ORDER:

1. Exact ICD match
2. Exact diagnosis match
3. Exact synonym match
4. Prefix ICD match
5. Prefix diagnosis match
6. Prefix synonym match
7. search_weight
8. fuzzy matching

---------------------------------------------------------
ICD-TYPEAHEAD-004
ICD MASTER SEARCH INDEX
---------------------------------------------------------

PURPOSE:

Use ICD master descriptions as the primary
diagnosis search vocabulary.

RULE:

ICD descriptions are searchable directly.

The synonym table serves only as
supplemental clinician vocabulary.

Synonyms are reserved for:

- abbreviations
- acronyms
- clinical shorthand
- lay terminology
- legacy terminology

---------------------------------------------------------
NEXT ACTIVE PHASE
RN ICA INTELLIGENCE
---------------------------------------------------------

STATUS:

QUEUED — NEXT PHASE

DEPENDENCY:

ICD Intelligence Engine Complete

PURPOSE:

Validate and harden RN assessment intelligence.

---------------------------------------------------------
FOLLOWING PHASE
SOCIAL WORKER ICA INTELLIGENCE
---------------------------------------------------------

STATUS:

QUEUED

DEPENDENCY:

RN ICA Intelligence Complete

---------------------------------------------------------
FOLLOWING PHASE
SPIRITUAL COUNSELOR ICA INTELLIGENCE
---------------------------------------------------------

STATUS:

QUEUED

DEPENDENCY:

Social Worker ICA Intelligence Complete

---------------------------------------------------------
FOLLOWING PHASE
DISCIPLINE DOCUMENTATION INTELLIGENCE
---------------------------------------------------------

STATUS:

QUEUED

---------------------------------------------------------
FOLLOWING PHASE
TRANSCRIPT INTELLIGENCE
---------------------------------------------------------

STATUS:

QUEUED

---------------------------------------------------------
FOLLOWING PHASE
ELIGIBILITY SUPPORT INTELLIGENCE
---------------------------------------------------------

STATUS:

QUEUED

---------------------------------------------------------
FOLLOWING PHASE
MEDICAL DIRECTOR REVIEW INTELLIGENCE
---------------------------------------------------------

STATUS:

QUEUED

---------------------------------------------------------
FOLLOWING PHASE
IDG REVIEW INTELLIGENCE
---------------------------------------------------------

STATUS:

QUEUED

---------------------------------------------------------
FOLLOWING PHASE
RECERTIFICATION EVIDENCE BUILDER
---------------------------------------------------------

STATUS:

QUEUED

---------------------------------------------------------
FOLLOWING PHASE
RULE ENGINE + COMPLIANCE LAYER
---------------------------------------------------------

STATUS:

QUEUED

---------------------------------------------------------
FOLLOWING PHASE
AUDIT TRAIL EXPANSION
---------------------------------------------------------

STATUS:

QUEUED

---------------------------------------------------------
FOLLOWING PHASE
FINALIZATION ENGINE
---------------------------------------------------------

STATUS:

QUEUED

---------------------------------------------------------
FOLLOWING PHASE
PRODUCTION CUTOVER
---------------------------------------------------------

STATUS:

QUEUED

---------------------------------------------------------
FUTURE PHASE 13
FINALIZATION ENGINE
---------------------------------------------------------

Includes:

- lock finalized notes
- amendment-only edits
- regulatory production controls

Status:

Deferred until field testing complete.

=========================================================
FINAL ALIGNMENT
=========================================================

ICA = source of clinical assessment evidence ✅

Ontology = AI brain / disease intelligence source of truth ✅

ICD recommendation support = ontology-driven and physician-reviewed ✅

IDG = clinical authority ✅

POC = execution layer ✅

Medical Director / authorized physician = final diagnosis authority ✅

No ICA → No reliable evidence input → No defensible POC ✅

No ontology match → No disease intelligence → No specific recommendation ✅

No physician review → No final ICD authority ✅

=========================================================
CURRENT SYSTEM POSITION
=========================================================

Architecture Discovery:
COMPLETE ✅

Clinical Intelligence Discovery:
PARTIALLY COMPLETE ✅

Disease Library Completion:
ACTIVE ✅

Production Grade Validation:
ACTIVE ✅

Audit-Survival Validation:

DEFERRED ⚠️

Pending completion of:

- Major Disease Family Hardening
- Hospice Intelligence Domains
- Eligibility Intelligence
- Narrative Intelligence
- Medical Director Review
- IDG Review
- Recertification Evidence
- Compliance Layer
- Audit Reconstruction Workflows

Current system position:

- Working EMR core ✅
- Interdisciplinary model forming ✅
- Clean API surface ✅
- Data integrity established ✅
- Canonical ontology identified as source of truth ✅
- Legacy disease process layer identified as content source, not authority ✅
- Evidence infrastructure exists ✅
- Recommendation infrastructure exists ✅
- ICD recommendation infrastructure exists ✅
- POC architecture exists ✅

SNS Hospice EMR has moved beyond architecture discovery.

Current system phase:

CLINICAL INTELLIGENCE FOUNDATION

Current active build:

ICD INTELLIGENCE ENGINE

Primary remaining risk:

INCOMPLETE CLINICAL INTELLIGENCE COVERAGE

Not:

ARCHITECTURE CONSTRUCTION

=========================================================
OBJECTIVE
=========================================================

Transition from:

- flexible testing system ✅

to:

- ontology-driven clinical intelligence system ✅

then to:

- CMS / NGS / CDPH / TJC / CHAP / ACHC / DHS
  audit-survival hospice EMR ✅



