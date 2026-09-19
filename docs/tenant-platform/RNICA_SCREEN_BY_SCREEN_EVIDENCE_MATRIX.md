# RNICA Screen-by-Screen Evidence Matrix

Companion document to `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` (v1.1,
authority-labeled Figma input package). Names the supporting discovery
document(s) behind every screen's underlying content, so the source-of-
truth document's screen groupings can be traced back to repository
evidence without re-describing code inline.

STATUS: SUPPORTING EVIDENCE FOR THE FIGMA INPUT PACKAGE. NOT A DESIGN
DOCUMENT ITSELF.
CODE: BLOCKED
SCHEMA: BLOCKED
MIGRATIONS: BLOCKED

## Authority Key

- RD: Repository-discovered
- LP: Locked product decision
- RC: Regulatory/clinical authority
- DR: Design requirement
- FP: Future product direction
- NB: Not built/not connected
- OD: Open defect

| # | Screen | Underlying discovered content | Primary evidence documents | Authority for new grouping | Current capability boundary | Required preservation | Acceptance risk |
|---:|---|---|---|---|---|---|---|
| 1 | Patient Story | Patient/admission context, diagnoses, caregiver fields, Intelligence summary/findings/missing evidence, prior comparison | `RNICA_SECTION_BREAKDOWN.md`; `RNICA_USABILITY_AND_AI_REVIEW.md`; `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`; `AI_VISIBILITY_MATRIX.md`; `RNICA_EXPERIENCE_IMPLEMENTATION_PLAN.md` | DR + FP | Dedicated story engine is NB; current screen is an aggregation | Source provenance; no new authority | High if represented as current generated story or eligibility conclusion |
| 2 | Evidence & Intake | Demographics, vitals, referrals, admission scoping, evidence harvesting | `RNICA_SECTION_BREAKDOWN.md`; `RNICA_SYSTEM_DEPENDENCY_MAP.md`; `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md` | DR; RC for assessment/POC relationship | Evidence harvesting exists but is not independently surfaced | Admission scoping; referrals review; evidence status | Medium if intake completion is inferred without source review |
| 3 | Functional Status | PPS, KPS, ECOG, FAST, NYHA, functional-decline notes, HOPE M1190, structured NYHA target | `RNICA_SECTION_BREAKDOWN.md`; locked redesign handoff; LCD supporting references | LP + DR; RC for hospice evidence | Current code does not diagnosis-gate all scales at the backend compliance layer (ECOG has no enforcement equivalent to FAST/NYHA) | PPS/KPS; allowed scale semantics; structured mapping | High if irrelevant scales render or scale values are treated as automatic eligibility |
| 4 | Pain & Symptom Burden | Pain Assessment, J0900/J0915, Symptom Impact J2051, blank-only derivation, Intelligence pain input | `RNICA_SECTION_BREAKDOWN.md`; `RNICA_USABILITY_AND_AI_REVIEW.md`; `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md` | DR | Intelligence is Save/Lock/load-triggered; derivation is blank-only | HOPE mapping; manual override; required pain fields | High if derivation overwrites manual data |
| 5 | Diagnosis & LCD | Primary/secondary diagnoses, comorbidities, terminal prognosis, LCD chain/narrative, POC and Intelligence inputs | `RNICA_SECTION_BREAKDOWN.md`; `RNICA_SYSTEM_DEPENDENCY_MAP.md`; `RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md`; `RNICA_CLINICAL_NARRATIVE_REWIRING_MAP.md` | LP + DR; RC for terminal-status evidence | LCD advisory chain exists; Diagnosis narrative is dead/legacy and prohibited in future UI | Diagnosis keys; LCD narrative; no duplicate narrative | Critical if Diagnosis narrative returns or LCD is presented as physician certification |
| 6 | Body Systems | Ten body-system sections; Intelligence and structured-finding paths; symptom derivation inputs | `RNICA_SECTION_BREAKDOWN.md`; `RNICA_UI_DEPENDENCY_MAP.md`; `RNICA_REDESIGN_IMPACT_ANALYSIS.md` | DR | Not every system feeds Intelligence; many are optional/unvalidated | All section reachability; consumed field paths | High if grouping suppresses sections or warnings |
| 7 | Caregiver & Support | PCG assessment, willingness/capability, psychosocial, spiritual, personal care, teaching needs | `RNICA_SECTION_BREAKDOWN.md`; `RNICA_USABILITY_AND_AI_REVIEW.md`; `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md` | DR | Dedicated caregiver integration/intelligence is NB; only embedded recommendation text exists | No-caregiver logic; source fields | High if fabricated risk score or dedicated engine is implied |
| 8 | Safety & Clinical Risk | Safety, imminent death, psychosocial, mobility, neurological, oxygen/fall/delirium thresholds | `RNICA_SECTION_BREAKDOWN.md`; `RNICA_SYSTEM_DEPENDENCY_MAP.md`; `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`; `AI_VISIBILITY_MATRIX.md` | DR | Threshold findings exist; formal risk score is NB | Intelligence inputs; suicide-note warning; source evidence | Critical if advisory finding becomes diagnosis/score or safety warning is hidden |
| 9 | ACP & Goals of Care | Six hard-required ACP fields, decision-maker/directive fields, HOPE F2000/F2100/F2200 | `RNICA_SECTION_BREAKDOWN.md`; `RNICA_USABILITY_AND_AI_REVIEW.md` | DR | No separate goals-of-care engine was discovered | Required ACP keys/validation/HOPE mapping | Critical if ACP remains buried or "Goals of Care" implies unsupported engine |
| 10 | Orders & POC | Admissions Order, POC adapter, explicit order-from-suggestion, POC completeness, conditional CHHA POC | `RNICA_SECTION_BREAKDOWN.md`; `RNICA_SYSTEM_DEPENDENCY_MAP.md`; `RNICA_UI_DEPENDENCY_MAP.md`; `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md` | DR + RC for individualized POC | POC is wired; RNICA billing readiness is not | Explicit user actions; adapter/dedup; readiness | Critical if recommendations auto-create orders/POC content |
| 11 | Compliance & Readiness | Client/server validation, finalization checks, HOPE lifecycle, referrals, POC/CHHA, Lock recheck | `RNICA_SYSTEM_DEPENDENCY_MAP.md`; `RNICA_UI_DEPENDENCY_MAP.md`; `RNICA_USABILITY_AND_AI_REVIEW.md`; `RNICA_REDESIGN_IMPACT_ANALYSIS.md` | DR | CTI/F2F/survey/billing readiness are NB/not connected | Every blocker; severity; navigation; server truth | Critical if blockers are hidden, truncated, or misclassified |
| 12 | AI Action Center | Intelligence output, Structured Findings signals, recommendations, missing evidence, evidence harvesting | `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`; `AI_VISIBILITY_MATRIX.md`; `RNICA_USABILITY_AND_AI_REVIEW.md` | DR | Rules engine; not live typing; Explanation Engine and Patient Story engine are NB | Data contract; recommendation-only semantics; freshness | Critical if branded as continuous/LLM intelligence or advisory output becomes mandatory |
| 13 | Finalization | Finalization narrative, signature/attestation, readiness, Lock, amendments, audit | `RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md`; `RNICA_CLINICAL_NARRATIVE_ARCHITECTURAL_CORRECTION.md`; `RNICA_LOCK_DEFECT_UNREACHABLE_NARRATIVE_REVIEW.md`; `RNICA_SYSTEM_DEPENDENCY_MAP.md`; `RNICA_UI_DEPENDENCY_MAP.md` | LP + DR | Sole active narrative is Finalization; Diagnosis review defect remains OD | Narrative authority; manual attestation/signature; Lock; amendments/audit | Critical if duplicate narrative, bypass, auto-attestation, or history loss occurs |

## Cross-Screen Evidence Rules

1. A screen grouping may be new while its underlying fields and behaviors
   are repository-discovered.
2. A new grouping does not authorize new backend capability.
3. "AI" content must identify trigger/freshness and distinguish advisory
   output from validation.
4. "Compliance" content must preserve actual severity and server
   enforcement.
5. "Completion" must be observable through fields, review actions, and
   checks. Do not use subjective completion claims as system truth.
6. "Eligibility support" must remain evidence support, not automated
   physician certification.
7. Every NB item must remain absent or visibly labeled as future
   direction, not operational.
8. Every LP item overrides current repository placement for Figma but
   requires separate forward-only implementation planning.

## Evidence Documents Used

- `RNICA_SYSTEM_DEPENDENCY_MAP.md`
- `RNICA_UI_DEPENDENCY_MAP.md`
- `RNICA_USABILITY_AND_AI_REVIEW.md`
- `RNICA_FEATURE_TO_UI_WIRING_MATRIX.md`
- `AI_VISIBILITY_MATRIX.md`
- `RNICA_REDESIGN_IMPACT_ANALYSIS.md`
- `RNICA_SECTION_BREAKDOWN.md`
- `RNICA_EXPERIENCE_IMPLEMENTATION_PLAN.md`
- `RNICA_CLINICAL_NARRATIVE_ARCHITECTURAL_CORRECTION.md`
- `RNICA_CLINICAL_NARRATIVE_REWIRING_MAP.md`
- `RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md`
- `RNICA_LOCK_DEFECT_UNREACHABLE_NARRATIVE_REVIEW.md`
- `ANTI_HOSPICEMD_DESIGN_RULES.md`
