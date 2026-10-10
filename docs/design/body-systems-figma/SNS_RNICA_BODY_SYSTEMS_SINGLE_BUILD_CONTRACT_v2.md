# SNS RNICA Body Systems Single Build Contract

**Status:** Product-owner design and implementation authority  
**Scope:** RN Initial Comprehensive Assessment, Section 7 Body Systems only  
**Version:** 2.0  
**Date:** 2026-10-09  
**Supersedes:** Version 1.0 and every prior Body Systems plan, mockup interpretation, situation-gate proposal, visit-mode proposal, proof-of-concept, and worktree note that conflicts with this contract  

---

## 1. Controlling correction

RNICA is an initial comprehensive admission assessment. A nurse is establishing the patient's current baseline and cannot begin by assuming a body system has no concern.

**Review Required is the only permitted starting state for every body system.**

The following controls are prohibited in RNICA Body Systems:

- No current concern as an entry gate
- Stable existing as an entry gate
- New or worsening as an entry gate
- Admission / Routine RN / Recertification mode selector
- One-click normal or all-normal action
- Auto-normalization from blank values
- Auto-completion from diagnoses, medications, prior records, or historical evidence

These concepts may be evaluated later for separately specified Update or Recertification workflows. They are not part of RNICA.

---

## 2. State model

Every system uses exactly these workflow states:

1. **REVIEW_REQUIRED**
2. **IN_PROGRESS**
3. **REVIEWED_COMPLETE**
4. **REVIEWED_WITH_EXCEPTION**

### 2.1 REVIEW_REQUIRED

- Default for every system.
- No clinical conclusion exists.
- No narrative is generated.
- No HOPE value is harvested.
- The system does not count toward completion.
- Historical evidence may be displayed, but does not change the state.

### 2.2 IN_PROGRESS

The state begins when the nurse records or changes any current-assessment field.

- Partial findings may be saved.
- Draft save is allowed.
- The system does not count as complete.
- Missing required review groups are shown inline.
- No system-level “normal” conclusion is generated.

### 2.3 REVIEWED_COMPLETE

The state is available only after every required current-assessment group for that system has an explicit nurse response and every triggered conditional branch is complete.

- Each required group may contain expected findings, abnormal findings, not present, not applicable when clinically valid, or a documented limitation.
- Blank values cannot satisfy a required group.
- Historical evidence cannot satisfy a required group.
- A diagnosis alone cannot satisfy a required group.
- A medication alone cannot satisfy a required group.
- The nurse explicitly completes system review.

### 2.4 REVIEWED_WITH_EXCEPTION

This state is used when the nurse completed all assessable portions but one or more limitations or unresolved issues remain.

Required for each exception:

- affected scope
- reason
- assessed portion
- available evidence
- clinical risk or implication
- follow-up owner
- due time or contingency

A reviewed-with-exception system may satisfy **draft review**, but whether it permits record finalization depends on the blocking classification defined below.

---

## 3. RNICA Body Systems completion hierarchy

### 3.1 Field level

A field is complete when:

- the nurse entered an explicit current value; or
- the field is conditionally hidden because its parent response makes it inapplicable; or
- the nurse documented a permitted assessment limitation.

### 3.2 Required review-group level

A review group is complete when:

- every required field in the group is complete; and
- every triggered conditional field is complete; and
- every clinically significant finding has a disposition when required.

### 3.3 System level

A body system is complete when:

- every required review group is complete;
- all cross-field contradictions are resolved;
- all required current evidence is entered;
- every required intervention, response, follow-up, or reason-none-needed is documented;
- the nurse selects **Complete system review**.

### 3.4 Body Systems section level

Section 7 is complete when:

- all ten systems are REVIEWED_COMPLETE; or
- a system is REVIEWED_WITH_EXCEPTION and every exception is classified as nonblocking or draft-allowed under the approved rule profile;
- no system remains REVIEW_REQUIRED or IN_PROGRESS;
- no unresolved record-blocking contradiction exists;
- all required wound, Braden, infection, medication/bowel, and symptom-impact relationships are complete.

### 3.5 RNICA finalization level

RNICA clinical finalization is blocked when any Body Systems rule marked **record blocking** remains unresolved.

HOPE review occurs after RNICA clinical finalization. RNICA finalization does not automatically submit HOPE.

---

## 4. Blocking classifications

### Informational

- Does not block draft save.
- Does not block Body Systems completion.
- Does not block RNICA finalization.

### Draft allowed

- Draft may be saved.
- System remains IN_PROGRESS or REVIEWED_WITH_EXCEPTION.
- Blocks Body Systems section completion until resolved or reclassified under an approved exception rule.

### Record blocking

- Draft may be saved.
- Blocks Body Systems completion.
- Blocks RNICA clinical finalization.

### Signature blocking

- Clinical record may be fully reviewed when allowed by the broader RNICA lifecycle.
- Blocks final authentication/signature until resolved.

This document defines the required blocking behavior below. It does not authorize arbitrary field-level blocking outside these rules.

---

## 5. Rules common to all ten systems

| Rule ID | Condition | Classification | Required resolution |
|---|---|---|---|
| BS-GLOBAL-001 | System remains REVIEW_REQUIRED | Record blocking | Nurse performs current review |
| BS-GLOBAL-002 | System remains IN_PROGRESS | Record blocking | Complete required review groups |
| BS-GLOBAL-003 | Required current field blank | Record blocking | Enter current value or valid limitation |
| BS-GLOBAL-004 | Historical evidence used as current without confirmation | Record blocking | Enter current nurse determination |
| BS-GLOBAL-005 | Unable to assess without scope, reason, assessed portion, owner, and timing | Record blocking | Complete limitation record |
| BS-GLOBAL-006 | Significant finding lacks disposition | Record blocking | Document intervention, response/follow-up, or reason none is needed |
| BS-GLOBAL-007 | Current fields contradict one another | Record blocking | Resolve contradiction |
| BS-GLOBAL-008 | Current finding conflicts with historical evidence | Draft allowed | Enter explicit current determination before completion |
| BS-GLOBAL-009 | Optional RN Notes blank | Informational | No action required |
| BS-GLOBAL-010 | Source attribution missing where source is not direct RN observation | Record blocking | Add source and date/time |
| BS-GLOBAL-011 | Required observation time missing | Record blocking | Add observation time |
| BS-GLOBAL-012 | System completion attempted without explicit Complete system review action | Record blocking | Nurse completes review action |
| BS-GLOBAL-013 | HOPE/CMS code displayed in clinical workspace | Build failure | Remove reporting label from clinical UI |
| BS-GLOBAL-014 | Any system silently resets after save/reload | Build failure | Implement persistence and regression test |

---

## 6. Neurological completion and blocking rules

### Required review groups

1. Level of consciousness
2. Orientation/cognition
3. Communication/speech
4. Anxiety impact
5. Agitation impact
6. Neurological/motor/sensory findings
7. Disposition for significant findings

### Minimum explicit responses

- Level of consciousness: one current value
- Orientation/cognition: current orientation status and cognitive finding
- Communication/speech: current ability and relevant limitation
- Anxiety impact: one current impact response
- Agitation impact: one current impact response
- Motor/sensory: explicit finding or explicit none identified after review

### Triggered requirements

| Trigger | Required detail | Classification if missing |
|---|---|---|
| Confusion/disorientation | Current presentation, source, safety implication, follow-up | Record blocking |
| Limited/nonverbal communication | Communication method and assessment limitation | Record blocking |
| Seizure | Current/recent status, intervention or plan, follow-up | Record blocking |
| Focal deficit/paralysis | Location/laterality and functional linkage | Record blocking |
| Moderate/severe anxiety | Intervention decision, response/pending response, follow-up owner | Record blocking |
| Moderate/severe agitation | Safety impact, intervention decision, response/pending response, follow-up owner | Record blocking |
| Unable to determine symptom impact | Reason, observation source, follow-up | Record blocking |

### Completion rule

Neurological becomes REVIEWED_COMPLETE only when all seven groups are complete and every triggered branch has a disposition.

---

## 7. Respiratory completion and blocking rules

### Required review groups

1. Shortness-of-breath presence and impact
2. Respiratory pattern
3. Lung findings
4. Cough/sputum
5. Oxygen/support status
6. Current measurement context
7. Disposition for significant findings

### Minimum explicit responses

- Shortness of breath: explicit current impact response
- Respiratory pattern: one current response
- Lung findings: explicit current findings
- Cough: explicit current response
- Oxygen/support: explicit yes/no and current details when yes
- SpO2: read-only authoritative value plus context when measured; or explicit not obtained with reason

### Triggered requirements

| Trigger | Required detail | Classification if missing |
|---|---|---|
| Dyspnea present | Impact, context, and treatment decision | Record blocking |
| Moderate/severe dyspnea impact | Intervention, response or response pending, urgency, follow-up owner | Record blocking |
| Oxygen use | Device, flow, frequency, current response | Record blocking |
| Abnormal SpO2 used in assessment | Room-air/oxygen context and observation time | Record blocking |
| Productive cough | Sputum characteristics and clinical disposition | Draft allowed; record blocking if clinically significant and undisposed |
| Ventilator/tracheostomy/noninvasive support | Device/support details and current status | Record blocking |
| Abnormal lung findings | Location/laterality where applicable and disposition | Record blocking |
| Respiratory infection suspected/known | Link or referral to Infection without duplicate infection entry | Draft allowed until relationship resolved |

### Completion rule

Respiratory becomes REVIEWED_COMPLETE only when all seven groups are complete. Oxygen never implies dyspnea, and dyspnea never implies oxygen use.

---

## 8. Cardiovascular completion and blocking rules

### Required review groups

1. Blood-pressure interpretation
2. Pulse/rhythm
3. Peripheral perfusion
4. Edema
5. Cardiac discomfort/syncope
6. Devices/vascular findings
7. Disposition for significant findings

### Minimum explicit responses

- Blood-pressure interpretation references the authoritative Vitals value
- Pulse/rhythm has an explicit current assessment
- Perfusion has an explicit current assessment
- Edema has explicit present/absent documentation after assessment
- Cardiac discomfort and syncope have explicit current responses

### Triggered requirements

| Trigger | Required detail | Classification if missing |
|---|---|---|
| Abnormal rhythm/pulse | Finding, current effect, disposition | Record blocking |
| Edema present | Location, laterality, pitting/nonpitting, grade when applicable | Record blocking |
| Cardiac discomfort | Link to Pain record and cardiac context | Record blocking |
| Syncope/orthostatic symptom | Current status, safety implication, follow-up | Record blocking |
| Poor perfusion/cyanosis/cool extremity | Location and disposition | Record blocking |
| Cardiac device | Device type and relevant current status | Draft allowed; record blocking if device concern exists |
| Edema duplicated in Integumentary | Ownership conflict | Build failure |

### Completion rule

Cardiovascular becomes REVIEWED_COMPLETE only when all seven groups are complete and edema remains Cardiovascular-owned.

---

## 9. Nutrition completion and blocking rules

### Required review groups

1. Appetite
2. Current intake
3. Hydration
4. Weight trend
5. Swallowing/aspiration risk
6. Diet/artificial support/oral factors
7. Disposition for significant findings

### Minimum explicit responses

- Appetite: current value
- Intake: current amount or qualitative intake
- Hydration: current assessment
- Weight trend: current/prior reference or reason unavailable
- Swallowing: explicit current review
- Diet/artificial support: explicit current status

### Triggered requirements

| Trigger | Required detail | Classification if missing |
|---|---|---|
| Poor/minimal/no intake | Current amount, cause/context, intervention/follow-up | Record blocking |
| Weight loss | Source values, period, clinical interpretation | Record blocking |
| Weight unavailable | Reason and alternative nutritional evidence | Draft allowed |
| Dysphagia | Texture/liquid status, aspiration concern, intervention/follow-up | Record blocking |
| Aspiration concern | Precautions and follow-up; infection link if aspiration pneumonia exists | Record blocking |
| Artificial nutrition/hydration | Type, current use, tolerance, patient preference when relevant | Record blocking |
| Dehydration concern | Findings and disposition | Record blocking |
| Duplicate manual weight/MAC | Ownership conflict | Build failure |

### Completion rule

Nutrition becomes REVIEWED_COMPLETE only when all seven groups are complete. Braden nutrition cannot satisfy this system.

---

## 10. Gastrointestinal completion and blocking rules

### Required review groups

1. Nausea impact
2. Vomiting impact
3. Diarrhea impact
4. Constipation impact
5. Abdominal findings
6. Bowel sounds/stool/ostomy
7. Bowel pattern and last bowel movement
8. Disposition for significant findings

### Minimum explicit responses

All four symptom-impact fields require explicit current responses. The four symptoms cannot be collapsed into a single GI-normal response.

### Triggered requirements

| Trigger | Required detail | Classification if missing |
|---|---|---|
| Nausea present | Pattern, intake effect, intervention/response | Record blocking for moderate/severe impact; otherwise draft allowed until disposition |
| Vomiting present | Frequency/description, hydration effect, intervention/response | Record blocking |
| Diarrhea present | Frequency/pattern, hydration/continence effect, intervention/response | Record blocking |
| Constipation present | Last BM, pattern, discomfort/impaction concern, intervention/response | Record blocking |
| Ostomy present | Type and current condition/function | Record blocking |
| Abdominal distention/tenderness/ascites | Current finding and disposition | Record blocking |
| Applicable opioid active | Bowel-regimen status sourced from medications | Record blocking if unanswered |
| Opioid without bowel regimen | Clinical reason | Record blocking if absent |
| Constipation despite bowel regimen | Preserve both facts and document response/follow-up | Record blocking if no disposition |

### Completion rule

Gastrointestinal becomes REVIEWED_COMPLETE only when all eight groups are complete and medication-to-bowel validation is resolved.

---

## 11. Genitourinary completion and blocking rules

### Required review groups

1. Continence
2. Urinary pattern
3. Urinary symptoms
4. Urine characteristics
5. Catheter/diversion status
6. Renal-output concern
7. Disposition for significant findings

### Minimum explicit responses

- Continence: explicit current response
- Pattern: explicit current review
- Symptoms: explicit current review
- Urine characteristics: current finding or not observed with reason
- Catheter/diversion: explicit yes/no/type

### Triggered requirements

| Trigger | Required detail | Classification if missing |
|---|---|---|
| Retention/dysuria/urgency/frequency/nocturia | Current detail and disposition | Record blocking when clinically significant |
| Oliguria/anuria | Current context and urgent disposition | Record blocking |
| Hematuria/abnormal urine | Description and disposition | Record blocking |
| Catheter/diversion | Type, patency, site/drainage, relevant dates | Record blocking |
| Catheter complication | Intervention/response/follow-up | Record blocking |
| UTI suspected/known | Link to Infection; GU retains manifestations | Draft allowed until link/disposition |
| UTI used to infer GU symptoms | Invalid inference | Build failure |

### Completion rule

Genitourinary becomes REVIEWED_COMPLETE only when all seven groups are complete. Infection owns the UTI record.

---

## 12. Musculoskeletal completion and blocking rules

### Required review groups

1. Strength/weakness
2. Range of motion
3. Rigidity/contracture/joint findings
4. Amputation/prosthesis
5. Paralysis/paresis
6. Gait/balance/mobility interpretation
7. Disposition for significant findings

### Minimum explicit responses

Every group requires explicit current review or a valid limitation.

### Triggered requirements

| Trigger | Required detail | Classification if missing |
|---|---|---|
| Weakness | Generalized/focal, location where relevant, functional linkage | Record blocking |
| Limited ROM/contracture | Location and care implication | Record blocking |
| Joint swelling/spasm/pain | Location and disposition; link Pain if applicable | Record blocking |
| Amputation/prosthesis | Site and current issue/status | Draft allowed; record blocking if concern exists |
| Paralysis/paresis | Type/laterality and functional linkage | Record blocking |
| Mobility concern | Reference authoritative Function/ADL values | Record blocking if relationship missing |
| ADL values re-entered in Musculoskeletal | Ownership conflict | Build failure |

### Completion rule

Musculoskeletal becomes REVIEWED_COMPLETE only when all seven groups are complete. Functional Status remains authoritative for standardized function and ADLs.

---

## 13. Integumentary completion and blocking rules

### Required review groups

1. General skin condition
2. Moisture/temperature/turgor/fragility/color
3. Skin impairment presence
4. Wound records
5. Pressure-risk/Braden assessment
6. Treatment/prevention response
7. Disposition for significant findings

### Minimum explicit responses

- General skin condition: explicit current assessment
- Skin impairment: explicit yes/no after current examination
- Braden: all six subscales or documented valid limitation
- Wound status: explicit current response

### Triggered requirements

| Trigger | Required detail | Classification if missing |
|---|---|---|
| Skin impairment present | Type and location | Record blocking |
| Wound present | Separate wound record with required wound fields | Record blocking |
| Multiple wounds | Separate record for each wound | Record blocking if combined into one record |
| Pressure injury | Stage when stageable, location, dimensions, treatment, follow-up | Record blocking |
| Wound marker used | Authoritative location text and wound record | Record blocking |
| Braden started | All six subscales and derived total | Record blocking |
| Braden risk identified | Prevention/intervention decision | Record blocking |
| Wound infection suspected/known | Link to Infection | Draft allowed until resolved |
| Braden mobility/nutrition used to complete other systems | Ownership conflict | Build failure |
| Braden total manually editable | Build failure | Build failure |

### Completion rule

Integumentary becomes REVIEWED_COMPLETE only when all seven groups are complete, every wound has its own record, and Braden is complete or a valid limitation is documented.

---

## 14. Infection / Immunological completion and blocking rules

### Required review groups

1. Active infection status
2. Site/type
3. Suspected/confirmed status and source
4. Organism/diagnostic information when available
5. Anti-infective treatment
6. Response
7. Precautions/isolation
8. Immunosuppression/immunological concern
9. Follow-up

### Minimum explicit responses

- Active infection: explicit current response
- Immunosuppression/immunological concern: explicit current response
- Treatment status: explicit current response when infection is present

### Triggered requirements

| Trigger | Required detail | Classification if missing |
|---|---|---|
| Active infection | Site/type, suspected/confirmed, source, disposition | Record blocking |
| Anti-infective active | Drug reference, dates/status, response/follow-up | Record blocking |
| Resistant organism | Organism/status and precautions | Record blocking |
| Precaution/isolation required | Type and current implementation | Record blocking |
| Respiratory infection | Link to Respiratory manifestations when present | Draft allowed until link/disposition |
| UTI | Link to GU manifestations when present | Draft allowed until link/disposition |
| Wound infection | Link to wound record or explanation | Record blocking |
| Sepsis | Authoritative source and current status | Record blocking |
| Local infection auto-converted to sepsis | Invalid inference | Build failure |
| Allergy re-entered as infection data | Ownership conflict | Build failure |

### Completion rule

Infection / Immunological becomes REVIEWED_COMPLETE only when all nine groups are complete. The affected system owns manifestations; Infection owns infection-specific facts.

---

## 15. Endocrine completion and blocking rules

### Required review groups

1. Diabetes status
2. Current glucose-related concern
3. Monitoring/treatment reference
4. Thyroid/parathyroid/pituitary/adrenal/pancreatic condition
5. Neuropathy/foot/skin relationship when applicable
6. Disposition for significant findings

### Minimum explicit responses

- Diabetes: explicit current response
- Glucose concern: explicit current response
- Other endocrine condition: explicit current review

### Triggered requirements

| Trigger | Required detail | Classification if missing |
|---|---|---|
| Diabetes present | Type, monitoring/treatment reference, current concern | Record blocking |
| Hypoglycemia/hyperglycemia concern | Current signs/context and disposition | Record blocking |
| Insulin/therapy issue | Medication reference and follow-up | Record blocking |
| Endocrine condition present | Type and current clinical relevance | Draft allowed; record blocking if active concern lacks disposition |
| Neuropathy | Link to neurological/pain/foot context as applicable | Draft allowed until relationship resolved |
| Foot/skin concern | Link to Integumentary | Draft allowed until relationship resolved |
| Endocrine remains placeholder | Build failure | Build failure |

### Completion rule

Endocrine becomes REVIEWED_COMPLETE only when all six groups are complete. Endocrine cannot be deferred as a later phase.

---

## 16. Body Systems section completion screen

The register must show for each system:

- REVIEW REQUIRED
- IN PROGRESS
- REVIEWED
- REVIEWED WITH EXCEPTION

The register must not show “No concern” as a system completion state.

The section summary must show:

- systems reviewed
- systems in progress
- systems requiring review
- systems with exception
- record-blocking issues
- draft-allowed issues

The nurse can open every issue at its owning field.

---

## 17. HOPE boundary

During clinical documentation:

- no HOPE codes are visible;
- no separate HOPE section is required for Body Systems-derived data;
- no HOPE response is created from REVIEW_REQUIRED or IN_PROGRESS data;
- no symptom value is derived from diagnosis, medication, oxygen use, or measurement alone.

After RNICA clinical finalization:

1. Freeze the final clinical source snapshot.
2. Apply the HOPE mapping version effective for the record date.
3. Generate the HOPE review.
4. Show the clinical source, derived response, mapping version, and exceptions.
5. Return clinical corrections to the owning field.
6. Preserve the audit trail.
7. Require authorized verification before submission.

---

## 18. Traceability amendments

| Requirement ID | Requirement | Required proof | Drift failure |
|---|---|---|---|
| BS-STATE-001 | REVIEW_REQUIRED is the only starting state | State unit test and initial UI screenshot | Any system starts normal/no concern/stable |
| BS-STATE-002 | RNICA has no situation gate | DOM test | No concern/stable/new-worsening buttons appear |
| BS-STATE-003 | No one-click normal action | Interaction test | Bulk normal action exists |
| BS-COMP-001 | Every system has defined required review groups | Per-system schema/config test | A system completes without all groups |
| BS-COMP-002 | Blank cannot satisfy completion | Validation test | Blank system or group completes |
| BS-COMP-003 | Historical evidence cannot satisfy current review | Current/historical test | Historical data marks reviewed |
| BS-COMP-004 | Nurse explicitly completes system review | Interaction/audit test | System auto-completes from field entry |
| BS-BLOCK-001 | REVIEW_REQUIRED blocks finalization | Finalization test | RNICA finalizes with unreviewed system |
| BS-BLOCK-002 | IN_PROGRESS blocks finalization | Finalization test | RNICA finalizes with partial system |
| BS-BLOCK-003 | Incomplete limitation blocks finalization | Unable-to-assess test | Limited assessment completes without details |
| BS-BLOCK-004 | Significant finding requires disposition | Cross-field scenario tests | Finding completes without action/reason |
| BS-BLOCK-005 | All ten systems persist | Save/reload suite | Any system resets |
| BS-HOPE-001 | No HOPE value before finalization | Pre-finalization mapping test | Draft creates final HOPE value |
| BS-HOPE-002 | No HOPE codes appear clinically | DOM text scan | Prohibited code/label appears |

---

## 19. Definition of done

Body Systems is complete only when:

- all ten systems start in REVIEW_REQUIRED;
- RNICA contains no No current concern, Stable existing, or New/worsening entry gate;
- all ten system-specific completion rules are enforced;
- all record-blocking conditions prevent finalization;
- draft save remains available;
- all ten systems persist after reload;
- hidden HOPE harvesting occurs only after clinical finalization;
- no HOPE/CMS labels appear during clinical documentation;
- density, scrollbar, wound, Braden, infection, opioid/bowel, and symptom-impact tests pass;
- the traceability matrix is complete;
- Facesheet and unrelated RNICA sections remain unchanged.

Final classification:

```text
RNICA BODY SYSTEMS IMPLEMENTED WITH REVIEW REQUIRED AS THE ONLY STARTING STATE AND ALL SYSTEM COMPLETION RULES ENFORCED
```

or:

```text
RNICA BODY SYSTEMS BLOCKED: <REQUIREMENT ID, FILE, ERROR, OR PRODUCT CONFLICT>
```

---

## 20. Source and policy distinction

- The **Review Required** state, per-system completion rules, blocking classifications, layout rules, and hidden-HOPE workflow are SNS product policy established by this contract.
- The clinical content preserves the patient-specific observations needed to describe respiratory, neurological, nutritional, cardiovascular, renal/urinary, wound, infection, and other system burden.
- Hospice eligibility remains an individualized physician determination. This contract does not implement automatic eligibility decisions.
- The applicable official HOPE version must be selected by record effective date. No HOPE item logic may be hardcoded into clinical presentation components.
