# SNS Hospice Language Standard

**Version:** 1.2  
**Status:** Proposed enterprise clinical-language, UI-copy, summary-generation, and documentation-assistance standard  
**Owner:** SNS Hospice Solutions clinical governance  
**Verification date:** October 5, 2026  
**Supersedes:** Version 1.1  
**Scope:** RN, LVN/LPN, CHHA/hospice aide, physician/medical director, NP/PA, MSW/MFT/MHC, spiritual care/chaplain, volunteer/bereavement, PT/OT/SLP, dietary, pharmacy, respiratory therapy, wound/ostomy care, inpatient/GIP/CHC staff, after-hours triage, case manager/IDG coordinator, administrator/DPCS, quality/QAPI/infection prevention, HIM/privacy/security, interpreter/language access, scheduling/front office, intake/admission, coding/billing/authorization, DME/supply, facility liaison, pediatric/child-life support where offered, complementary/creative arts services where offered, and future AI-assisted documentation

---

## 1. Purpose

This standard guides the words, phrases, prompts, controlled choices, summaries, templates, alerts, and AI-assisted drafts used in SNS Hospice EMR.

SNS should help staff record:

- what was observed, measured, auscultated, palpated, reported, reviewed, or confirmed;
- what changed since the prior assessment;
- symptom burden and effect on comfort, safety, function, and caregiver needs;
- response to medications, treatments, services, and nonpharmacologic interventions;
- progression, decline, complications, and disease trajectory when supported;
- patient and family goals, understanding, decisions, and education;
- unresolved concerns, communications, orders, follow-up, and escalation.

This standard does **not** ban clinically appropriate words. It discourages vague or unsupported language when more precise documentation is available.

---

## 2. Controlling principles

### 2.1 Describe before concluding

Prefer observations and data before general conclusions.

**Weak alone:** `Patient stable.`  
**Preferred:** `No significant change in documented respiratory findings since prior assessment. Dyspnea with minimal exertion persists; oxygen remains in use at 2 L/min by nasal cannula.`

### 2.2 Compare when comparison is intended

Do not use change words without a reference point.

- `Reduced since prior assessment`
- `Increased from reported baseline`
- `Consistent with prior documented findings`
- `Unable to compare; prior baseline unavailable`

### 2.3 Attribute the source

Distinguish:

- **Observed by clinician**
- **Measured during visit**
- **Patient-reported**
- **Caregiver-reported**
- **Documented in hospital/H&P/referral record**
- **Confirmed with provider or facility**
- **Unable to verify**

### 2.4 Do not turn temporary response into recovery language

Symptom reduction or response to comfort measures does not automatically mean the terminal condition improved.

**Preferred:** `Pain reduced from 8/10 to 3/10 after ordered medication; patient resting without observed grimacing at reassessment.`  
**Avoid alone:** `Patient improved.`

### 2.5 Do not force decline language

Document decline only when supported. Hospice eligibility and recertification require the total individualized clinical picture and physician judgment. Do not fabricate deterioration or suppress genuine stabilization or improvement.

### 2.6 Document once, reuse accurately

Structured findings, summaries, IDG views, plans of care, and AI drafts must use the same canonical facts. Do not make clinicians restate the same finding in multiple sections.

### 2.7 Preserve discipline scope

The EMR may guide wording but must not prompt a discipline to diagnose, prescribe, certify, or perform functions outside applicable scope, policy, orders, or credentialing.

---

## 3. Language classes

### 3.1 Preferred

Use when supported:

- Observed
- Measured
- Reported by patient
- Reported by caregiver
- Documented in available record
- Confirmed with provider
- Present / not observed during current assessment
- Increased / reduced since prior assessment
- New finding since prior assessment
- Persistent
- Intermittent / continuous
- Findings consistent with prior assessment
- No significant change since prior assessment
- Current interventions appear effective based on documented response
- Partial response / limited response / no observed response
- Symptoms remain despite current interventions
- Additional review or intervention requested
- Progressive functional dependence
- Increased assistance required
- Unable to compare because prior baseline is unavailable

### 3.2 Acceptable but requires context

These terms are allowed but should be accompanied by observations, comparison, or evidence:

- Stable
- Improving / improved
- Controlled
- Well managed
- Resolved
- Comfortable
- Normal
- Unremarkable
- Tolerated
- Compliant / noncompliant
- Appropriate / inappropriate
- Declining
- Lethargic
- Confused
- Agitated

Examples:

- `Stable` → `No significant change in edema, dyspnea, or activity tolerance since prior assessment.`
- `Improving` → `Cough frequency reduced from caregiver-reported hourly episodes to three episodes during the visit.`
- `Controlled` → `Pain reduced to stated acceptable level after ordered intervention.`
- `Comfortable` → `Patient denied pain; respirations unlabored at rest; no observed grimacing or guarding.`
- `Resolved` → `Previously documented nausea was not reported or observed during the current assessment.`
- `Tolerated` → describe the response: `No vomiting, rash, respiratory distress, or other adverse response observed after medication administration.`
- `Noncompliant` → document the choice and reason: `Patient declined the medication after education, stating concern about excessive sedation.`

### 3.3 Discouraged when used alone

- Doing well
- Doing good
- Better
- Fine
- Good
- Great
- Stable
- Improving
- Controlled
- Comfortable
- Normal
- Unremarkable
- No issues
- No complaints
- Appears okay
- Continue to monitor
- Education provided
- Physician notified
- Family aware
- Tolerated well
- Will follow up
- Per usual
- Baseline
- Noncompliant
- Poor historian

These phrases become acceptable only when the documentation identifies the finding, source, intervention, response, communication, or next action.

### 3.4 Prohibited or unsafe system-generated language

SNS must not automatically generate:

- a diagnosis not entered or confirmed by an authorized clinician;
- a six-month prognosis determination;
- hospice eligibility approval or denial;
- terminal-relatedness determination;
- “no concern” from missing data;
- “stable” from unchanged checkboxes alone;
- “resolved” because a field is blank;
- “patient denies” when the patient could not report;
- “family understands” without documented teach-back, acknowledgment, or response;
- “physician notified” without recorded communication evidence;
- “order received” without an authenticated order source;
- “intervention effective” without a documented response;
- “noncompliant” as an automated characterization;
- causal statements such as “due to” or “secondary to” unless supported and authorized.

---

## 4. Universal phrase patterns

### 4.1 Observation

`[Finding] observed/measured at [time or assessment].`

### 4.2 Comparison

`[Finding] increased/reduced/remains consistent compared with [prior assessment/date/reported baseline].`

### 4.3 Symptom impact

`[Symptom] affects [comfort, sleep, intake, mobility, communication, safety, caregiving, activity tolerance].`

### 4.4 Intervention and response

`[Intervention] provided/performed per [order/plan]. At reassessment, [objective or reported response].`

### 4.5 Education

`Reviewed [topic] with [patient/representative/caregiver]. [Person] stated/repeated/demonstrated [understanding or remaining question].`

### 4.6 Communication

`Communicated [finding/request] to [role/name] at [time] by [method]. Response/order/follow-up: [result].`

### 4.7 Unable to determine

`Unable to determine [specific item] because [specific limitation]. Evidence reviewed: [sources]. Follow-up: [action/owner].`

---

## 5. Discipline-specific language guide

### 5.1 Registered Nurse (RN)

**Focus:** comprehensive assessment, symptom burden, safety, comfort, medication and treatment response, plan-of-care coordination, change in condition, patient/family education, physician communication.

**Preferred phrases**

- `Observed...`
- `Measured...`
- `Patient reported...`
- `Caregiver reported...`
- `Finding increased/reduced since prior assessment...`
- `Current comfort measures produced [documented response]...`
- `New safety concern identified...`
- `Provider notified; response documented...`
- `Plan-of-care review requested because...`

**Avoid alone**

- `Stable`
- `Doing well`
- `Continue to monitor`
- `Education done`
- `MD aware`

### 5.2 Licensed Vocational/Practical Nurse (LVN/LPN)

**Focus:** focused assessment and observation within scope, ordered care, medication administration, response, reporting changes to RN/physician, reinforcing education.

**Preferred phrases**

- `Observed and reported to RN...`
- `Medication administered per order; response at reassessment...`
- `Finding differs from prior documented status...`
- `RN notified at [time]; instructions received...`
- `Reinforced previously established teaching on...`

**Avoid**

- independent diagnosis or prognosis claims;
- undocumented order changes;
- `No change` without defining what was compared.

### 5.3 CHHA / Hospice Aide

**Focus:** care provided, patient response, functional observations, skin observations visible during care, intake/elimination observations, safety concerns, reporting to supervising nurse.

**Preferred phrases**

- `Assistance provided with [task] according to aide plan of care.`
- `Patient required [level] assistance for [ADL].`
- `Observed [specific change] during care and reported to supervising nurse at [time].`
- `Caregiver reported...; supervising nurse notified.`
- `No new skin concern observed during assigned care` only when within the aide’s assigned observation responsibilities.

**Avoid**

- diagnosing infection, pressure injury stage, or terminal decline;
- `Patient stable`;
- `Wound improved`;
- `Family noncompliant`.

### 5.4 Physician / Medical Director / Attending Physician

**Focus:** certification and recertification, diagnosis, prognosis, relatedness, medication and treatment orders, medical management, eligibility reasoning, level-of-care decisions.

**Preferred phrases**

- `Clinical information reviewed includes...`
- `Prognosis is supported by...`
- `Despite [stabilization or response], the patient continues to demonstrate...`
- `The following findings remain consistent with a terminal trajectory...`
- `Condition determined related/unrelated based on...`
- `Order issued for...`

**Avoid**

- diagnosis-only eligibility statements;
- copied narratives without patient-specific evidence;
- `Remains appropriate` without supporting findings;
- unexplained contradictions such as meaningful recovery in ADLs.

### 5.5 Medical Social Worker (MSW)

**Focus:** psychosocial status, coping, caregiver burden, practical needs, access barriers, resources, advance-care planning support, communication and family dynamics.

**Preferred phrases**

- `Patient stated...`
- `Caregiver described...`
- `Observed interaction included...`
- `Caregiver burden reported as...`
- `Barrier identified: ...`
- `Resource referral offered/accepted/declined...`
- `Patient/family goals expressed as...`
- `Follow-up assigned for...`

**Avoid**

- labeling family as difficult, dysfunctional, manipulative, or noncompliant;
- speculative mental-state conclusions;
- `Coping well` without evidence;
- legal determinations outside scope.

### 5.6 Spiritual Care / Chaplain

**Focus:** spiritual concerns, meaning, hope, distress, beliefs, rituals, sources of strength, reconciliation, patient/family preferences, declined services.

**Preferred phrases**

- `Patient/family identified [belief/practice/source of strength].`
- `Spiritual concern expressed as...`
- `Requested [ritual/prayer/clergy contact/quiet presence].`
- `Visit offered and declined; preference respected.`
- `Patient/family response to intervention...`

**Avoid**

- judging faith as strong/weak;
- assuming religion from demographics;
- `Spiritually stable`;
- imposing a belief framework;
- diagnosing psychiatric conditions.

### 5.7 Bereavement / Volunteer

**Focus:** assigned support, observed or reported needs, activities performed, boundaries, escalation.

**Preferred phrases**

- `Provided assigned companionship/support activity.`
- `Patient/caregiver requested...`
- `Observed [specific concern] and reported to [supervisor] at [time].`
- `Bereavement contact completed by [method]; response documented.`

**Avoid**

- clinical assessments;
- prognosis statements;
- independent care-plan changes;
- `Grieving normally` or `grief resolved`.

### 5.8 Case Manager / IDG Coordinator

**Focus:** synthesis, unresolved needs, ownership, deadlines, coordination, duplicated or conflicting plans, follow-up.

**Preferred phrases**

- `IDG reviewed...`
- `Unresolved need: ...`
- `Responsible discipline: ...`
- `Follow-up due: ...`
- `Plan-of-care update required because...`
- `Conflicting information identified and routed for review.`

**Avoid**

- `All disciplines aware` without evidence;
- `No issues` when open tasks exist;
- closing a concern because a note is absent.

### 5.9 Administrator / DPCS / Quality / Compliance

**Focus:** operational facts, corrective actions, record deficiencies, audit evidence, policy implementation, staff support, patient safety.

**Preferred phrases**

- `Record deficiency identified: ...`
- `Required element absent/incomplete at review.`
- `Corrective action assigned to [role] with due date [date].`
- `Follow-up verification completed; evidence reviewed: ...`
- `Potential patient-safety impact: ...`
- `No patient harm identified from available evidence` only if the review supports it.

**Avoid**

- blame language;
- speculative intent;
- performance scoring in clinical notes;
- `Staff failed` when the record only shows a missing element.

### 5.10 Intake / Admission / Authorization / Billing Support

**Focus:** source, dates, received/missing records, election and authorization status, payer communications, routed clinical questions.

**Preferred phrases**

- `Record received from [source] on [date].`
- `Information reported by [source], not yet clinically verified.`
- `Missing document requested from...`
- `Clinical eligibility question routed to authorized clinician.`
- `Payer communication documented as...`

**Avoid**

- interpreting eligibility or relatedness unless authorized;
- backdating;
- `Approved` before actual approval evidence;
- entering clinical conclusions copied from incomplete referral material.


### 5.11 Nurse Practitioner / Physician Assistant

**Focus:** practitioner services within applicable Federal and State scope, hospice policy, attending-practitioner status, face-to-face findings when authorized, orders when authorized, symptom management, and communication with the hospice physician and IDG.

**Preferred phrases**

- `Clinical findings from the encounter include...`
- `Current symptoms and objective findings reviewed...`
- `Order entered for... under applicable authority.`
- `Finding communicated to the hospice physician/IDG because...`
- `Face-to-face findings forwarded for use by the certifying physician.`

**Avoid**

- implying that a face-to-face encounter itself certifies terminal illness;
- issuing orders outside applicable State scope or hospice policy;
- `Remains appropriate for hospice` without patient-specific supporting findings and authorized decision-making;
- copying a physician narrative without identifying the actual encounter findings.

### 5.12 Marriage and Family Therapist / Mental Health Counselor

**Focus:** psychosocial and emotional needs, family systems, coping, distress, communication, relationship concerns, counseling interventions, and coordination with the IDG.

**Preferred phrases**

- `Patient/caregiver described...`
- `Counseling focused on...`
- `Observed communication pattern included...`
- `Patient/family goal expressed as...`
- `Response to counseling intervention...`
- `Safety concern identified and escalated according to policy.`

**Avoid**

- unsupported psychiatric diagnoses;
- labels such as `dysfunctional`, `manipulative`, `attention-seeking`, or `difficult family`;
- conclusions about capacity, abuse, legal status, or risk without the required assessment and escalation pathway;
- `Coping well` without describing the reported or observed basis.

### 5.13 Physical Therapist

**Focus:** comfort-oriented mobility, transfers, positioning, safe movement, caregiver training, equipment needs, energy conservation, fall-risk reduction, and function consistent with goals of care.

**Preferred phrases**

- `Transfer required [level] assistance and [device].`
- `Mobility limited by [dyspnea, pain, weakness, fatigue, balance].`
- `Positioning intervention used to support comfort and reduce caregiver burden.`
- `Patient/caregiver demonstrated [technique] with [level] cueing.`
- `Equipment recommendation communicated to the IDG.`

**Avoid**

- restorative promises such as `will return to prior level of function` unless that goal is expressly appropriate and supported;
- `Gait improved` without distance, assistance, device, tolerance, or comparison;
- `Tolerated therapy well` without response details;
- therapy goals disconnected from comfort, safety, function, or the plan of care.

### 5.14 Occupational Therapist

**Focus:** ADL participation, energy conservation, positioning, upper-extremity function, environmental adaptation, caregiver techniques, cognitive supports, and comfort-focused task modification.

**Preferred phrases**

- `Required [level] assistance for [ADL].`
- `Task modified using [strategy/equipment] to reduce fatigue or discomfort.`
- `Caregiver demonstrated safe use of [equipment/technique].`
- `Environmental barrier identified: ...`
- `Recommendation aligned with patient goal of...`

**Avoid**

- `Independent` without naming the task and conditions;
- `Doing better with ADLs` without specifying assistance and change;
- `Safe` without documenting the observed performance or safeguards;
- goals that assume rehabilitation rather than the individualized hospice plan.

### 5.15 Speech-Language Pathologist

**Focus:** swallowing, aspiration risk, communication access, speech intelligibility, cognitive-communication support, caregiver education, food/fluid strategies consistent with goals, and comfort-focused recommendations.

**Preferred phrases**

- `Swallowing difficulty observed/reported with [consistency].`
- `Signs concerning for aspiration included...`
- `Communication limited by...; effective strategy was...`
- `Patient/caregiver education addressed...`
- `Recommendation reviewed in relation to patient goals and comfort.`

**Avoid**

- `Swallow normal` without assessment basis;
- `Aspiration resolved` without evidence;
- `Patient noncompliant with diet` instead of documenting the informed choice, goals, and risk discussion;
- guaranteeing prevention of aspiration.

### 5.16 Dietitian / Dietary Counselor

**Focus:** intake, hydration, weight and anthropometric trends, nutrition-impact symptoms, food preferences, culturally appropriate support, artificial nutrition/hydration goals, caregiver education, and comfort-focused recommendations.

**Preferred phrases**

- `Reported intake approximately...`
- `Nutrition-impact symptom identified: ...`
- `Weight/MAC trend reviewed with dates...`
- `Recommendation focused on comfort, preference, and tolerated intake.`
- `Patient/family preference regarding artificial nutrition/hydration documented as...`

**Avoid**

- `Eating well` or `poor appetite` without amount, trend, or impact;
- moralizing language regarding intake or weight;
- implying that forced intake is required;
- `Nutrition goals met` without the individualized goal and evidence.

### 5.17 Pharmacist / Pharmacy Consultant

**Focus:** medication profile review, therapeutic duplication, interactions, adverse effects, allergies, route and formulation burden, deprescribing recommendations, controlled-substance safety, and response to therapy.

**Preferred phrases**

- `Medication profile reviewed for...`
- `Potential adverse drug reaction identified: ...`
- `Potential interaction/duplication identified and communicated to...`
- `Recommendation: [action], rationale: [patient-specific reason].`
- `Response to medication therapy documented as...`

**Avoid**

- changing an order without authorized prescriber action;
- `Medication effective` without a documented response;
- suppressing mild allergies;
- `Noncompliant with medications` instead of documenting use, barriers, choice, education, and follow-up.

### 5.18 Homemaker

**Focus:** assigned homemaker services, environment-related observations, tasks completed, patient/caregiver requests, and reporting concerns through the approved supervisory pathway.

**Preferred phrases**

- `Completed assigned homemaker task according to the plan of care.`
- `Observed environmental concern: ...; reported to [supervisor] at [time].`
- `Patient/caregiver requested assistance with...`

**Avoid**

- clinical assessment, diagnosis, staging, prognosis, or medication recommendations;
- `Patient stable`;
- undocumented plan-of-care changes.

### 5.19 Volunteer Coordinator / Volunteer

**Focus:** assigned volunteer activity, training and supervision records, patient/family requests, boundaries, observations requiring escalation, and continuity of support.

**Preferred phrases**

- `Provided assigned volunteer service: ...`
- `Patient/caregiver requested...`
- `Observed concern and reported to the volunteer coordinator/IDG at [time].`
- `Volunteer assignment accepted/declined/discontinued at patient or family request.`

**Avoid**

- clinical judgments;
- independent care-plan changes;
- counseling beyond training and assignment;
- prognosis or treatment statements.

### 5.20 Bereavement Coordinator / Bereavement Counselor

**Focus:** risk assessment according to hospice policy, anticipatory grief, bereavement plan, outreach, grief support, referrals, family preferences, and continuity after death.

**Preferred phrases**

- `Bereavement risk factors identified according to the approved tool/policy: ...`
- `Family member reported...`
- `Support offered/accepted/declined...`
- `Follow-up plan: method, owner, and date...`
- `Referral provided for...`

**Avoid**

- `Normal grief` or `grief resolved` without assessment context;
- diagnosing a mental-health condition outside scope;
- assuming all family members share the same risk or response;
- `Family coping well` without source and supporting details.

### 5.21 DME / Supply Coordinator

**Focus:** order source, equipment or supply status, delivery, function, safety concerns, patient/caregiver instruction, vendor communication, and resolution.

**Preferred phrases**

- `Order verified from...`
- `Equipment delivered on...`
- `Equipment function confirmed/not confirmed; issue: ...`
- `Vendor contacted at...; response and follow-up...`
- `Patient/caregiver instructed on...; response documented.`

**Avoid**

- `Equipment okay`;
- documenting delivery without evidence;
- recording an order that has not been received or authenticated;
- closing an issue without a documented outcome.

### 5.22 Facility Liaison / Contracted-Facility Staff Interface

**Focus:** coordination with SNF/NF/RCFE/ALF or inpatient staff, responsibility boundaries, medication and order communication, visit findings, incident follow-up, and plan-of-care alignment.

**Preferred phrases**

- `Finding communicated to facility role/name at [time].`
- `Hospice responsibility/facility responsibility clarified as...`
- `Facility-reported event documented and routed for hospice review.`
- `Plan-of-care coordination completed regarding...`

**Avoid**

- assuming facility documentation replaces hospice documentation;
- blame language;
- `Facility aware` without recipient, time, and communication result;
- unresolved responsibility ambiguity.


### 5.23 Wound / Ostomy / Continence Nurse or Consultant

**Focus:** patient-specific skin, pressure injury, wound, ostomy, fistula, drainage, odor, pain, periwound condition, comfort, supplies, caregiver education, and treatment recommendations within scope and orders.

**Preferred phrases**

- `Wound assessment completed at [site]; findings include [dimensions, tissue, drainage, odor, periwound condition, pain].`
- `Comparison with [date/source] shows [specific increase, reduction, or no significant change].`
- `Treatment performed per current order; patient response documented as...`
- `Recommendation communicated to [authorized prescriber/IDG] with rationale...`
- `Caregiver demonstrated [wound/ostomy technique] with [level] cueing.`

**Avoid**

- `Wound better`, `healing well`, or `wound stable` without measurable findings;
- staging or diagnosis outside authority;
- treating absence of documentation as wound resolution;
- recommending curative goals that conflict with the patient’s comfort-focused plan without documenting the goals discussion.

### 5.24 Respiratory Therapist

**Focus:** ordered respiratory treatments, oxygen delivery, equipment function, secretion management, ventilatory support, tolerance, caregiver education, and communication of changes.

**Preferred phrases**

- `Oxygen delivered by [device] at [setting] per order.`
- `Respiratory effort and documented response before/after intervention: ...`
- `Equipment function checked; issue identified/resolved/escalated: ...`
- `Patient/caregiver demonstrated [equipment technique] with [level] cueing.`
- `Change in respiratory status communicated to [role/name] at [time].`

**Avoid**

- `Oxygen good`, `breathing stable`, or `tolerated treatment well` without findings;
- independently changing settings outside orders or scope;
- equating a normal temperature or a single saturation value with absence of respiratory concern;
- promising recovery of pulmonary function.

### 5.25 Inpatient Hospice / General Inpatient / Continuous Home Care Clinician

**Focus:** symptom crisis, level-of-care reason, intensity of services, frequent reassessment, interventions and responses, transition criteria, coordination, and continuity of the plan of care.

**Preferred phrases**

- `Level-of-care need supported by [specific uncontrolled symptom or crisis finding].`
- `Intervention provided at [time]; response at reassessment: ...`
- `Symptoms remain uncontrolled despite...`
- `Current findings support continuation/transition review; provider/IDG communication documented.`
- `Handoff includes current symptoms, recent interventions, responses, pending orders, and safety concerns.`

**Avoid**

- `Still qualifies for GIP/CHC` without patient-specific findings;
- `Comfortable` or `stable` without reassessment evidence;
- copying the same crisis narrative across shifts;
- discharging or changing level of care from a missing note or isolated checkbox.

### 5.26 After-Hours Triage / On-Call Clinician

**Focus:** caller and patient identification, source of report, immediate safety screening, symptom details, intervention instructions within scope, provider notification, dispatch decision, follow-up, and closed-loop handoff.

**Preferred phrases**

- `Call received from [source/relationship] at [time] regarding...`
- `Reported findings: ...; unable to directly observe by telephone.`
- `Immediate safety concern identified/not identified based on reported information.`
- `Instructions provided according to [order/plan/protocol]; caller teach-back documented.`
- `Visit dispatched/provider notified; outcome and handoff documented.`

**Avoid**

- charting telephone reports as direct observation;
- `No issue` or `patient stable` without the assessment basis;
- `Family understands` without teach-back or documented response;
- leaving advice without a follow-up owner or escalation plan when required.

### 5.27 Interpreter / Translator / Language-Access Coordinator

**Focus:** communication access, interpreter identity or service, language, modality, qualification, translated materials, patient preference, privacy, and accurate relay without adding clinical interpretation.

**Preferred phrases**

- `Qualified interpreter used for [language] by [modality/service/identifier].`
- `Interpretation provided for [encounter/document/topic].`
- `Patient/representative preference for communication documented as...`
- `Translated material provided in [language/version].`
- `Interpreter relayed the speaker’s statements without clinical summarization.`

**Avoid**

- using a minor child as interpreter except where expressly permitted in an emergency under controlling policy/law;
- documenting that language assistance was declined without the offer and response;
- machine-only translation of critical clinical or rights content when qualified human review is required;
- replacing the clinician’s patient-specific assessment with the interpreter’s opinion.

### 5.28 Health Information Management / Medical Records

**Focus:** record completeness, authentication, indexing, reconciliation, amendments, addenda, disclosure, retention, deficiency tracking, linkage, and retrieval.

**Preferred phrases**

- `Record element missing/incomplete: ...`
- `Authentication deficiency identified for [entry/date/role].`
- `Correction/addendum linked to the original entry with author, date, time, and reason.`
- `Disclosure request received/completed according to policy; scope documented.`
- `Duplicate or wrong-patient entry escalated for correction and audit review.`

**Avoid**

- silently correcting clinical meaning;
- overwriting signed content;
- backdating;
- marking a deficiency complete without verifying the required evidence.

### 5.29 Privacy / Security Officer

**Focus:** minimum necessary use, access review, disclosure, consent/authorization status, incident assessment, mitigation, breach workflow, device and account safeguards, and evidence preservation.

**Preferred phrases**

- `Potential privacy/security incident reported at [time]; facts known: ...`
- `Access/disclosure reviewed for [system/event] according to policy.`
- `Mitigation initiated: ...; owner and due date documented.`
- `Affected information and recipients verified as...`
- `Final determination made by authorized privacy/security process.`

**Avoid**

- placing sensitive incident-investigation details in the patient’s routine clinical narrative unless clinically necessary;
- concluding `no breach` before authorized review;
- sharing credentials, tokens, or unnecessary identifiers;
- blame or intent statements unsupported by evidence.

### 5.30 QAPI / Patient Safety / Risk / Infection Prevention

**Focus:** measurable indicators, adverse events, infection surveillance, investigation, contributing factors, corrective actions, effectiveness checks, patient safety, and learning without unsupported blame.

**Preferred phrases**

- `Event/indicator identified from [source] with date range and denominator when applicable.`
- `Known facts, contributing conditions, and unresolved questions documented separately.`
- `Corrective action assigned to [role] by [date].`
- `Effectiveness verified using [measure/evidence].`
- `Infection-control concern escalated according to policy.`

**Avoid**

- `Staff error` or `negligence` without completed authorized review;
- using QAPI language to score individual clinical performance in the patient record;
- claiming improvement without a defined measure and comparison period;
- closing an event because no additional report was received.

### 5.31 Scheduler / Front Office / Patient Services Representative

**Focus:** contact attempts, appointment or visit scheduling, availability, location, communication preference, routing, cancellations, access barriers, and escalation.

**Preferred phrases**

- `Contact attempted by [method] at [time]; outcome: ...`
- `Visit scheduled/rescheduled/canceled at request of [source], reason if provided: ...`
- `Urgent clinical concern routed immediately to [role] at [time].`
- `Communication preference/language need documented and routed.`
- `Transportation, access, or contact barrier identified: ...`

**Avoid**

- clinical triage or reassurance outside role;
- `Patient refused care` when the person only declined a proposed time;
- `Unable to reach` without attempts and methods;
- recording diagnosis, prognosis, or symptom conclusions copied from an unverified call.

### 5.32 Hospice Coding / Billing / Clinical Documentation Integrity

**Focus:** source-supported codes, terminal and related-condition queries, claim-supporting dates, levels of care, certifications, election, authorization, and non-leading clarification routed to authorized clinicians.

**Preferred phrases**

- `Code/claim element supported by [specific authenticated source].`
- `Documentation clarification requested regarding [objective inconsistency or missing specificity].`
- `Query is non-leading and preserves clinician judgment.`
- `Claim hold reason and required evidence documented.`
- `Clinical determination routed to authorized clinician.`

**Avoid**

- selecting a diagnosis solely to secure payment;
- instructing a clinician to document decline that is not present;
- converting an LCD criterion into an automatic pass/fail determination;
- altering clinical documentation or dates to fit billing.

### 5.33 Patient Rights / Grievance / Patient Advocate

**Focus:** complaint or grievance intake, respectful acknowledgment, immediate safety issues, nonretaliation, investigation routing, communication, resolution, and appeal rights.

**Preferred phrases**

- `Concern received from [source] on [date/time] regarding...`
- `Immediate safety issue identified and escalated to...`
- `Acknowledgment and next-step information provided in an understandable language/manner.`
- `Investigation owner and response due date documented.`
- `Resolution communicated; remaining concern or appeal option documented.`

**Avoid**

- minimizing a concern as `just a complaint`;
- retaliatory or judgmental language;
- declaring a grievance unfounded without investigation evidence;
- placing confidential personnel-investigation details in the clinical record.

### 5.34 Pediatric / Child-Life / Family Support Specialist, When Offered

**Focus:** developmentally appropriate communication, play or legacy activities, sibling/child support, caregiver goals, anticipatory grief support, safety, consent, and coordination with the IDG.

**Preferred phrases**

- `Developmentally appropriate support provided through...`
- `Child/family question or concern expressed as...`
- `Activity aligned with family goal of...`
- `Response to intervention observed/reported as...`
- `Concern escalated to the appropriate licensed discipline.`

**Avoid**

- diagnostic conclusions outside credentials;
- forcing disclosure or participation;
- assuming developmental understanding from age alone;
- documenting identity-sensitive family details beyond the minimum necessary.

### 5.35 Music / Art / Massage / Other Complementary Therapy, When Offered

**Focus:** service ordered or included in the plan of care, patient preference, intervention, observable or reported response, comfort goal, precautions, and IDG coordination.

**Preferred phrases**

- `Intervention provided according to the plan of care: ...`
- `Patient preference and consent documented.`
- `Before/after response documented as [reported or observed].`
- `Intervention stopped/modified because...`
- `Finding requiring clinical follow-up communicated to...`

**Avoid**

- claims that the service cured, reversed, or treated disease beyond evidence and scope;
- `Relaxed` or `better` without an observable or reported basis;
- continuing touch-based services without consent or despite contraindications;
- replacing required clinical assessment or treatment.

---

## 6. Body-system word list

### 6.1 General status and change

**Preferred options**

- No significant change since prior assessment
- Findings consistent with prior assessment
- New finding since prior assessment
- Findings increased since prior assessment
- Findings reduced since prior assessment
- Progressive decline observed
- Unable to compare; prior baseline unavailable
- Not assessed during this encounter, with reason

### 6.2 Pain and symptom burden

**Preferred**

- Pain present/absent/not reported
- Patient-reported intensity [score/descriptor]
- Nonverbal indicators observed: [specific indicators]
- Pain increased/reduced since prior assessment
- Partial/limited/no observed response
- Acceptable comfort level reported by patient
- Breakthrough symptoms reported

**Discouraged alone**

- Pain controlled
- Comfortable
- No pain issues
- Tolerated medication well

### 6.3 Cardiovascular

**Preferred**

- Pulse regular/irregular; rate measured at...
- Pulse strong/weak/thready/bounding/absent at documented site
- Skin pale/cyanotic/mottled/cool as observed
- Edema location, type, and grade documented
- Dizziness/syncope reported or not reported
- Chest discomfort reported/denied/unable to report
- No significant change in cardiovascular findings
- Cardiovascular findings increased/reduced since prior assessment

**Discouraged alone**

- Cardiac stable
- Circulation good
- Edema better

### 6.4 Respiratory

**Preferred**

- Dyspnea at rest/with exertion
- Respiratory effort unlabored/labored
- Respiratory rate measured at...
- Lung sounds [specific finding and location]
- Oxygen in use at [flow/device]; saturation measured at...
- Cough dry/productive; secretions characterized
- Unable to complete sentences because of dyspnea
- Dyspnea increased/reduced since prior assessment
- Current respiratory intervention produced [response]

**Discouraged alone**

- Breathing stable
- Breathing better
- Oxygen good
- Lungs normal

### 6.5 Neurological / cognitive / behavioral

**Preferred**

- Awake/lethargic/obtunded/unresponsive as observed
- Oriented to [domains]
- New or increased confusion reported/observed
- Communication limited by...
- Seizure activity reported/observed
- Behavioral finding observed: [specific behavior]
- Findings consistent with prior assessment
- Unable to obtain patient report; observation and caregiver report documented

**Discouraged alone**

- Neuro stable
- Normal cognition
- Confused patient
- Acting out

### 6.6 Gastrointestinal

**Preferred**

- Nausea/vomiting present, frequency and response documented
- Bowel movement last reported on...
- Constipation/diarrhea pattern documented
- Abdominal distention/tenderness observed
- Bowel sounds documented when assessed
- Intake limited by [symptom]
- GI findings increased/reduced since prior assessment

**Discouraged alone**

- GI stable
- Eating okay
- Bowels normal

### 6.7 Genitourinary

**Preferred**

- Urinary output reported/observed as...
- Dysuria/frequency/retention/incontinence reported
- Catheter type, patency, output, and observed urine characteristics
- New change in urinary pattern
- GU findings consistent with prior assessment

**Discouraged alone**

- Voiding fine
- Urine normal
- Foley okay

### 6.8 Renal

**Preferred**

- Reduced urine output reported/observed
- Dialysis status and goals documented from verified source
- Edema, pruritus, nausea, confusion, or fatigue as documented
- Available renal laboratory trend cited with date/source
- Renal-related symptom burden increased/reduced

**Discouraged alone**

- Kidney function worse/better without supporting data
- Renal stable

### 6.9 Liver / hepatic

**Preferred**

- Ascites present; effect on comfort/mobility/respiration documented
- Jaundice observed
- Encephalopathy findings documented
- Bleeding/bruising reported or observed
- Intake, muscle wasting, and functional endurance documented
- Available laboratory findings cited with date/source

**Discouraged alone**

- Liver stable
- Ascites controlled

### 6.10 Nutrition / hydration / swallowing

**Preferred**

- Intake approximately [portion/percentage/description]
- Reduced intake since prior assessment
- Weight or mid-arm circumference trend with dates
- Dysphagia with [consistency/aspiration concern]
- Assistance required for feeding
- Signs of dehydration observed/reported
- Artificial nutrition/hydration status and goals documented

**Discouraged alone**

- Eating well/poorly
- Appetite good
- Weight stable without values/dates

### 6.11 Skin / wounds

**Preferred**

- Location, dimensions, tissue, drainage, odor, surrounding skin, pain
- New skin finding identified
- Wound dimensions increased/reduced since prior measurement
- Drainage increased/reduced
- Pressure injury stage documented only by authorized clinician
- Current wound intervention and response

**Discouraged alone**

- Wound better
- Healing well
- Skin intact everywhere unless actually assessed
- No issues

### 6.12 Infection / immune status / allergies

**Preferred**

- Active infection documented from [source]
- Local signs observed: redness, warmth, swelling, tenderness, drainage, odor
- Temperature measured at...
- Antibiotic/antimicrobial therapy and response documented
- Resistant-organism history documented from [source]
- Immunosuppression documented with reason/source
- Every documented allergy displayed with type, severity, and reaction when available

**Discouraged alone**

- Infection stable
- Infection improving
- No infection because temperature is normal
- Allergy insignificant

### 6.13 Musculoskeletal / mobility

**Preferred**

- Strength, range of motion, gait, balance, transfer ability
- Assistance/device required
- New weakness or reduced endurance
- Mobility-related pain or safety concern
- Functional ability reduced/increased since prior assessment

**Discouraged alone**

- Ambulates well
- Weak
- Gait stable

### 6.14 Functional status / ADLs

**Preferred**

- Independent/supervision/limited assistance/extensive assistance/total assistance
- Increased assistance required for [ADL]
- Bed/chair bound status documented
- PPS/KPS/FAST score supported by corresponding findings
- Functional dependence progressed since prior assessment

**Discouraged alone**

- Function stable
- Declining without examples
- Total care without specifying domains

### 6.15 Endocrine / diabetes

**Preferred**

- Glucose measured/reported at [value/time/source]
- Hypoglycemic/hyperglycemic symptoms observed/reported
- Intake and medication relationship documented
- Insulin/medication administered per order; response documented
- Monitoring limited or declined, with reason and plan

**Discouraged alone**

- Sugar good/bad
- Diabetes controlled

### 6.16 Hematologic / bleeding

**Preferred**

- Bleeding/bruising location and extent
- Fatigue, pallor, weakness, or dyspnea documented
- Available laboratory finding with date/source
- Anticoagulant use and safety concern documented

**Discouraged alone**

- Blood counts low without data
- Bleeding controlled without response details

### 6.17 Cancer / disease burden

**Preferred**

- Known disease site and progression source documented
- New/worsening symptom burden
- Weight loss, intake decline, weakness, functional decline
- Disease-directed therapy continued/declined/stopped, with source
- Patient goals and symptom priorities documented

**Discouraged alone**

- Cancer worsening without evidence
- End stage based on diagnosis alone

### 6.18 Psychosocial

**Preferred**

- Patient/caregiver stated...
- Concern identified...
- Caregiver burden reported as...
- Financial/housing/transportation/access barrier identified
- Resource offered/accepted/declined
- Safety concern escalated according to policy

**Discouraged alone**

- Coping well/poorly
- Difficult family
- Dysfunctional
- Manipulative
- Noncompliant

### 6.19 Spiritual

**Preferred**

- Belief, practice, source of strength, spiritual concern, ritual request
- Spiritual-care visit accepted/declined
- Patient/family requested...
- Response to supportive presence/intervention documented

**Discouraged alone**

- Spiritually stable
- Strong/weak faith
- At peace unless patient-reported

### 6.20 Caregiver and family

**Preferred**

- Caregiver stated...
- Demonstrated ability to...
- Requested additional teaching/support for...
- Teach-back indicated...
- Limitation identified...
- Backup plan available/not available

**Discouraged alone**

- Family understands
- Family aware
- Good support
- Uncooperative family

### 6.21 Safety / falls / equipment

**Preferred**

- Fall reported with date/circumstances/injury/status
- Near fall reported
- Specific hazard observed
- Equipment present and functioning/not functioning
- Education and corrective action documented
- Follow-up owner and time documented

**Discouraged alone**

- Safety maintained
- Fall risk high without supporting factors
- Equipment okay

### 6.22 Active dying / imminence

**Preferred**

- Specific changes in responsiveness, intake, urine output, breathing, perfusion, secretions, temperature, or function
- Patient/family education on expected changes
- Comfort interventions and response
- Team/provider communication and updated plan

**Discouraged alone**

- Actively dying without supporting observations
- Transitioning without defined findings
- Imminent without documented basis

---

## 7. Summary-generation rules

1. Use documented facts only.
2. Preserve source attribution where material.
3. Prioritize immediate safety and uncontrolled comfort concerns.
4. Include all documented allergies; do not suppress mild allergies.
5. Include new or worsening findings before unchanged background findings.
6. Include meaningful response to intervention.
7. Include comparison language only when a baseline exists.
8. Do not equate blank with absent.
9. Do not equate hidden with resolved.
10. Do not repeat the same fact in multiple summary bullets.
11. Separate current findings from history.
12. Separate patient/caregiver reports from clinician observations.
13. Do not generate eligibility, prognosis, diagnosis, or relatedness conclusions without authorized inputs.

---

## 8. EMR implementation rules

### 8.1 Controlled vocabulary metadata

Every controlled phrase must include:

- `phrase_id`
- `display_text`
- `classification`: preferred, acceptable_with_support, discouraged
- `discipline_scope`
- `workflow_scope`
- `body_system`
- `requires_supporting_detail`
- `suggested_replacements`
- `effective_date`
- `version`
- `active`

### 8.2 UI behavior

- Preferred language appears first.
- Discouraged language is not a default selection.
- A discouraged selection remains available when clinically necessary.
- Selecting a discouraged term prompts a non-blocking suggestion: `Add supporting findings or choose more specific wording.`
- The nurse may continue without being blocked, unless a separate safety or regulatory validation applies.
- Do not create repeated warnings after the clinician has addressed or dismissed a suggestion for the current field.

### 8.3 Free-text assistance

- Highlight discouraged phrases after entry, not while the clinician is typing each character.
- Offer specific replacement choices.
- Never rewrite signed text silently.
- Before signature, show proposed edits as tracked suggestions.
- After signature, corrections require the existing amendment/addendum workflow and audit trail.

### 8.4 Role-sensitive templates

- RN templates emphasize assessment, intervention, response, coordination.
- LVN/LPN templates emphasize ordered care, observation, response, and notification.
- Aide templates emphasize tasks, functional observations, and reporting.
- Physician templates emphasize individualized clinical support, prognosis, relatedness, orders.
- MSW and spiritual-care templates preserve patient/family language and avoid unsupported clinical diagnoses.
- Administrative templates document facts, deficiencies, ownership, due dates, and verification.

### 8.5 AI rules

AI may:

- organize documented facts;
- suggest stronger wording;
- identify missing source, comparison, response, or follow-up;
- draft discipline-appropriate summaries;
- cite the source fields used.

AI must not:

- invent findings;
- convert uncertainty to certainty;
- diagnose;
- determine eligibility or prognosis;
- determine relatedness;
- characterize staff or family performance;
- delete contradictory evidence;
- use “stable,” “improved,” “controlled,” or “resolved” without supporting inputs;
- alter authenticated documentation without the correction workflow.

### 8.6 Versioning and governance

- Language packs are versioned.
- Changes require clinical governance approval.
- Existing signed notes retain the wording and version used at signature.
- Reports must identify the language-standard version used for generated content.
- No global wording replacement may alter historical signed records.

---

## 9. Formal QA checklist

### 9.1 QA record format

Each executed test must record:

- **Test ID**
- **Requirement or risk**
- **Source requirement or SNS policy reference**
- **Preconditions and test data**
- **Role and permissions used**
- **Steps performed**
- **Expected result**
- **Actual result**
- **Evidence**: screenshot, log, database query, exported record, or audit event
- **Severity if failed**: Blocker, Critical, Major, Minor
- **Status**: Not Run, Pass, Fail, Blocked, Not Applicable
- **Defect ID**
- **Tester and execution date**
- **Retest result and date**

### 9.2 Release gates

- **Blocker:** release prohibited. Examples include PHI exposure, cross-patient data, loss or alteration of signed documentation, invented clinical facts, or unauthorized diagnosis/prognosis/eligibility output.
- **Critical:** release prohibited until corrected and retested. Examples include missing authentication, missing allergy, role-scope violation, incorrect summary that changes clinical meaning, or failed amendment history.
- **Major:** release requires clinical owner approval and documented remediation plan. Examples include repeated vague defaults, duplicate entry, incorrect ordering, or inaccessible guidance.
- **Minor:** does not change clinical meaning or safety; may be scheduled only with owner approval.

### 9.3 Source and version control

- [ ] **SRC-001 | Blocker** — Every external authority in the source table has an official source URL or controlled enterprise copy, authority type, jurisdiction, effective/revision date, verification date, and verification status.
- [ ] **SRC-002 | Critical** — The build records the active SNS language-standard version.
- [ ] **SRC-003 | Blocker** — Updating the language pack does not alter historical signed notes.
- [ ] **SRC-004 | Critical** — Superseded or expired references are flagged before release.
- [ ] **SRC-005 | Major** — Source re-verification is required before a production release that changes compliance-sensitive language.
- [ ] **SRC-006 | Critical** — California-specific behavior is not enabled for non-California tenants unless separately configured.
- [ ] **SRC-007 | Critical** — LCD language is labeled payer/contractor guidance and is not represented as a universal legal requirement.

### 9.4 Vocabulary classification

- [ ] **VOC-001 | Critical** — Every controlled phrase has `phrase_id`, text, classification, discipline scope, workflow scope, body system, support requirement, version, effective date, and active status.
- [ ] **VOC-002 | Major** — Every discouraged phrase has at least one clinically reviewed preferred alternative.
- [ ] **VOC-003 | Major** — `Stable`, `improving`, `controlled`, `well managed`, and `resolved` are not default selections.
- [ ] **VOC-004 | Critical** — Clinicians may still use those terms when clinically appropriate.
- [ ] **VOC-005 | Major** — A discouraged term produces no more than one non-blocking suggestion per field per editing session.
- [ ] **VOC-006 | Critical** — Dismissing a suggestion does not alter the clinician’s text.
- [ ] **VOC-007 | Major** — Suggested replacements preserve the original clinical meaning and source attribution.

### 9.5 Discipline coverage and scope

- [ ] **DIS-001 | Critical** — RN guidance supports assessment, intervention, response, education, communication, and coordination.
- [ ] **DIS-002 | Critical** — LVN/LPN guidance does not imply independent diagnosis, prognosis, or unauthorized prescribing.
- [ ] **DIS-003 | Critical** — CHHA/hospice aide and homemaker guidance stays within assigned services, observation, and reporting.
- [ ] **DIS-004 | Critical** — Physician/medical director guidance supports patient-specific certification and recertification evidence rather than diagnosis alone.
- [ ] **DIS-005 | Critical** — NP/PA language reflects applicable authority and does not imply unauthorized certification or ordering.
- [ ] **DIS-006 | Critical** — MSW/MFT/MHC guidance avoids unsupported psychiatric, capacity, abuse, or legal conclusions.
- [ ] **DIS-007 | Critical** — Spiritual-care language does not judge faith, impose belief, or infer religion.
- [ ] **DIS-008 | Critical** — PT/OT/SLP language is hospice-goal-oriented and does not promise restorative outcomes.
- [ ] **DIS-009 | Critical** — Dietitian/dietary language respects patient preferences and does not require forced intake.
- [ ] **DIS-010 | Critical** — Pharmacist language identifies recommendations and medication risks without silently changing orders.
- [ ] **DIS-011 | Critical** — Volunteer and bereavement guidance does not produce clinical diagnoses or independent care-plan changes.
- [ ] **DIS-012 | Major** — Case manager/IDG coordinator guidance includes issue, owner, due date, and outcome.
- [ ] **DIS-013 | Major** — Administrator/DPCS/quality guidance documents deficiency facts without blame or performance scoring in the clinical record.
- [ ] **DIS-014 | Critical** — Intake, billing, authorization, DME, and facility-liaison guidance does not create unsupported clinical conclusions or false approval/order status.

### 9.6 Summary generation

- [ ] **SUM-001 | Blocker** — Generated summaries use saved facts only.
- [ ] **SUM-002 | Blocker** — Blank fields are not interpreted as absent, normal, resolved, or no concern.
- [ ] **SUM-003 | Critical** — Hidden fields are not interpreted as resolved or deleted.
- [ ] **SUM-004 | Critical** — All documented allergies appear, including mild, and retain type, severity, and reaction when available.
- [ ] **SUM-005 | Critical** — Patient/caregiver reports are attributed and not presented as clinician observations.
- [ ] **SUM-006 | Major** — Current findings and historical findings are separated.
- [ ] **SUM-007 | Critical** — Intervention effectiveness is not stated without a documented response.
- [ ] **SUM-008 | Critical** — Comparison language is used only when a prior assessment or identified baseline exists.
- [ ] **SUM-009 | Major** — Duplicate facts are not repeated in multiple bullets.
- [ ] **SUM-010 | Critical** — New, worsening, safety, and uncontrolled comfort concerns are surfaced before unchanged background information.
- [ ] **SUM-011 | Blocker** — No diagnosis, eligibility, prognosis, relationship, or causal conclusion is generated without authorized inputs.

### 9.7 Free-text and suggestion behavior

- [ ] **TXT-001 | Major** — Free-text review occurs after entry or on field exit, not after every keystroke.
- [ ] **TXT-002 | Critical** — Suggestions appear as tracked proposals before signature.
- [ ] **TXT-003 | Blocker** — Signed text is never silently rewritten.
- [ ] **TXT-004 | Blocker** — Post-signature changes use the amendment/addendum workflow and preserve the original.
- [ ] **TXT-005 | Major** — Suggestions are understandable to a user with limited computer experience.
- [ ] **TXT-006 | Major** — Guidance does not require duplicate narrative already captured structurally.
- [ ] **TXT-007 | Critical** — `Poor historian`, `noncompliant`, `family aware`, `MD aware`, and similar phrases receive specific, nonjudgmental replacement suggestions.

### 9.8 AI-assisted documentation

- [ ] **AI-001 | Blocker** — AI does not invent findings, measurements, dates, orders, diagnoses, responses, or communications.
- [ ] **AI-002 | Critical** — AI preserves uncertainty and provenance.
- [ ] **AI-003 | Blocker** — AI does not determine hospice eligibility, prognosis, terminal relatedness, or certification.
- [ ] **AI-004 | Critical** — AI does not characterize a patient, family, caregiver, or employee with unsupported judgmental language.
- [ ] **AI-005 | Critical** — AI does not infer `stable` from unchanged selections or infer `improved` from treatment alone.
- [ ] **AI-006 | Critical** — AI cites or exposes the source fields used for the draft.
- [ ] **AI-007 | Critical** — The clinician can accept, edit, or reject each suggestion.
- [ ] **AI-008 | Blocker** — AI-generated text is not authenticated as clinician documentation until reviewed and signed by an authorized user.

### 9.9 Record integrity, security, and audit

- [ ] **REC-001 | Blocker** — Patient isolation passes.
- [ ] **REC-002 | Blocker** — Admission and assessment isolation pass.
- [ ] **REC-003 | Blocker** — Role permissions prevent out-of-scope editing or signing.
- [ ] **REC-004 | Critical** — Author, credentials, date, time, and authentication are retained.
- [ ] **REC-005 | Blocker** — Original signed text remains retrievable after correction.
- [ ] **REC-006 | Critical** — Correction reason, author, date, and time are traceable.
- [ ] **REC-007 | Critical** — Autosave, save, reload, and export preserve exact clinician-selected language.
- [ ] **REC-008 | Blocker** — No PHI is sent to an unapproved external service.
- [ ] **REC-009 | Critical** — No duplicate clinical fact or allergy record is created by display reuse.

### 9.10 Usability and staff-support validation

- [ ] **USE-001 | Major** — An experienced hospice clinician can select a precise phrase without opening help.
- [ ] **USE-002 | Major** — A clinician with limited computer experience can understand the preferred phrase and suggestion.
- [ ] **USE-003 | Major** — Guidance does not increase average clicks, state switches, or duplicate entry for the tested workflow.
- [ ] **USE-004 | Major** — Legitimate stabilization or temporary improvement can be documented without being blocked.
- [ ] **USE-005 | Major** — Field testing includes RN, LVN/LPN, aide, physician/APP, psychosocial, spiritual, therapy, and administrative users applicable to the organization.
- [ ] **USE-006 | Major** — Confusion points and rejected wording are recorded and resolved before enterprise activation.
- [ ] **USE-007 | Major** — Accessibility testing covers keyboard, screen-reader labels, focus order, zoom, touch targets, and contrast for new guidance controls.

### 9.11 Body-system regression

- [ ] **SYS-001 | Critical** — Cardiovascular phrases do not produce unsupported stability or circulation conclusions.
- [ ] **SYS-002 | Critical** — Respiratory phrases include effort, dyspnea, oxygen/device, and response without equating oxygen use with comfort or improvement.
- [ ] **SYS-003 | Critical** — Infection phrases do not rule out infection because temperature is normal and do not suppress allergies.
- [ ] **SYS-004 | Critical** — GI/GU phrases distinguish patient report, clinician observation, and unavailable history.
- [ ] **SYS-005 | Critical** — Skin/wound phrases do not infer stage, healing, or resolution from blank fields.
- [ ] **SYS-006 | Critical** — Neurologic/cognitive phrases avoid unsupported mood, capacity, or diagnostic conclusions.
- [ ] **SYS-007 | Critical** — Nutrition phrases retain quantities, trends, dates, and goals when available.
- [ ] **SYS-008 | Critical** — Functional phrases specify assistance level and task rather than `stable` or `total care` alone.
- [ ] **SYS-009 | Critical** — Active-dying language requires documented findings and does not appear from a single checkbox alone.

### 9.12 Additional discipline-gap tests

- [ ] **DIS-015 | Critical** — Wound/ostomy language requires measurable findings and authority-appropriate staging.
- [ ] **DIS-016 | Critical** — Respiratory-therapy language preserves orders, equipment settings, and pre/post response without unsupported conclusions.
- [ ] **DIS-017 | Critical** — Inpatient/GIP/CHC language links level-of-care statements to patient-specific symptom findings and reassessment.
- [ ] **DIS-018 | Critical** — After-hours triage distinguishes caller report from clinician observation and documents closed-loop follow-up.
- [ ] **DIS-019 | Blocker** — Interpreter/translation workflows use qualified services when required and do not expose PHI or silently machine-translate critical documentation.
- [ ] **DIS-020 | Blocker** — HIM workflows preserve signed text, authentication, correction reason, addendum linkage, and audit history.
- [ ] **DIS-021 | Blocker** — Privacy/security workflows do not place credentials or unnecessary incident details in routine documentation.
- [ ] **DIS-022 | Critical** — QAPI/risk/infection-prevention language separates facts, analysis, corrective action, and effectiveness evidence without unsupported blame.
- [ ] **DIS-023 | Major** — Scheduler/front-office language routes clinical concerns and does not convert scheduling decisions into refusal-of-care conclusions.
- [ ] **DIS-024 | Blocker** — Coding/CDI workflows cannot alter clinical facts, dates, or eligibility conclusions for payment purposes.
- [ ] **DIS-025 | Critical** — Grievance/patient-rights language supports understandable communication, nonretaliation, escalation, ownership, and resolution tracking.
- [ ] **DIS-026 | Critical** — Pediatric/child-life and complementary-service templates stay within scope, consent, plan-of-care, and escalation requirements.

### 9.13 Exit criteria

Release may be approved only when:

- all Blocker and Critical tests pass;
- all failed Major tests have owner-approved disposition;
- source verification is current for the release;
- clinical governance approves the changed wording;
- usability evidence includes users with varied computer experience;
- test data and temporary records are removed or restored;
- the final QA report identifies build, language-pack version, tester, date, evidence, open defects, and approval.

---

## 10. Compliance references, source verification, and effective dates

### 10.1 Source-verification rules

1. Use the controlling source for the subject, jurisdiction, provider, payer, and effective period.
2. Prefer official eCFR, CMS, CDPH, Federal Register, State code, or payer source pages over copied summaries.
3. Record the effective or revision date stated by the source. Do not infer an effective date from a page-modified date.
4. Record a separate verification date showing when SNS last confirmed the source.
5. Classify each source as mandatory law/regulation/Condition of Participation, payer guidance, educational guidance, or SNS policy.
6. Reverify the source before any production release that changes compliance-sensitive behavior.
7. Reverify immediately when CMS, CDPH, a MAC, a payer, or an accreditor publishes a superseding notice or correction.
8. Preserve the exact source version used for a released language pack.
9. When a source conflicts with another source, document subject, jurisdiction, effective period, and the reason one controls.
10. If current effect cannot be confirmed, flag the requirement as `Verification Required` and do not represent it as settled.

### 10.2 Source-verification and effective-date table

| Source | Authority type | Jurisdiction / applicability | Effective or revision date | Verified | Status for SNS | Required recheck trigger | Primary use in this standard |
|---|---|---|---|---|---|---|---|
| 42 CFR 418.52 | Mandatory federal Condition of Participation | Medicare-certified hospices | Current eCFR text; eCFR displayed up to date October 1, 2026 | October 5, 2026 | Verified current snapshot | Any amendment to Part 418 or patient-rights guidance | Respectful, understandable, noncoercive patient-facing language |
| 42 CFR 418.54 | Mandatory federal Condition of Participation | Medicare-certified hospices | Current eCFR text; verify before release | October 5, 2026 | Verified for current project use | HOPE/comprehensive-assessment revision or Part 418 amendment | Assessment language, patient-specific needs, symptom and risk documentation |
| 42 CFR 418.56 | Mandatory federal Condition of Participation | Medicare-certified hospices | Current eCFR text; eCFR displayed up to date October 1, 2026 | October 5, 2026 | Verified current snapshot | IDG or plan-of-care rule change | IDG roles, RN coordination, patient/family-specific plan language |
| 42 CFR 418.58 | Mandatory federal Condition of Participation | Medicare-certified hospices | Current eCFR text; eCFR displayed up to date October 1, 2026 | October 5, 2026 | Verified current snapshot | QAPI amendment or survey-guidance update | QAPI, patient-safety, event, measure, and improvement language |
| 42 CFR 418.60 | Mandatory federal Condition of Participation | Medicare-certified hospices | Current Part 418 text; verify before release | October 5, 2026 | Verified for current project use | Infection-control amendment or survey-guidance update | Infection prevention, surveillance, escalation, and education language |
| 42 CFR 418.64 | Mandatory federal Condition of Participation | Medicare-certified hospices | eCFR displayed up to date September 30, 2026 | October 5, 2026 | Verified current snapshot | Core-service amendment | Physician, nursing, social-service, and counseling role language |

| 42 CFR 418.76 | Mandatory federal Condition of Participation | Medicare-certified hospices using aide/homemaker services | Current eCFR text; eCFR displayed up to date October 1, 2026 | October 5, 2026 | Verified current snapshot | Aide qualification or supervision amendment | Aide/homemaker scope-sensitive language |
| 42 CFR 418.100 | Mandatory federal Condition of Participation | Medicare-certified hospices | Current eCFR text in 2026 | October 5, 2026 | Verified current snapshot | Part 418 service/organization amendment | Comfort, dignity, goals, service categories |
| 42 CFR 418.104 | Mandatory federal Condition of Participation | Medicare-certified hospices | Current eCFR text; eCFR displayed up to date October 1, 2026 | October 5, 2026 | Verified current snapshot | Clinical-record, authentication, retention, or transfer amendment | Complete, clear, authenticated, dated clinical records and responses to care |
| 42 CFR 418.106 | Mandatory federal Condition of Participation | Medicare-certified hospices | Current eCFR text; eCFR displayed up to date October 1, 2026 | October 5, 2026 | Verified current snapshot | Drug-ordering or pharmacy-services amendment | Pharmacist, order, adverse-reaction, and medication-response language |
| 42 CFR 418.110 | Mandatory federal Condition of Participation | Hospices providing inpatient care directly | eCFR displayed up to date September 29, 2026 | October 5, 2026 | Verified current snapshot | Inpatient-hospice staffing or facility amendment | Inpatient/GIP nursing, safety, comfort, and handoff language |
| 42 CFR 418.202 | Mandatory federal coverage regulation | Medicare hospice covered services | eCFR displayed up to date October 1, 2026 | October 5, 2026 | Verified current snapshot | Covered-service amendment | Covered service categories, qualified personnel, inpatient-care language |

| 42 CFR 418.114 | Mandatory federal Condition of Participation | Medicare-certified hospices | Current eCFR text; eCFR displayed up to date October 1, 2026 | October 5, 2026 | Verified current snapshot | Personnel-qualification amendment | Scope-sensitive discipline templates and permissions |
| CMS QSO-24-12 and Transmittal R12400BP | CMS implementation/survey and manual guidance | Medicare-certified hospices | MFT/MHC hospice changes effective January 1, 2024; manual implementation January 2, 2024 | October 5, 2026 | Verified | Superseding QSO memo, manual transmittal, or CoP amendment | MFT/MHC inclusion and terminology |
| CMS MLN9895410, Creating an Effective Hospice Plan of Care | CMS educational guidance | Medicare hospice providers | CMS listing data date May 2025; no substantive update stated | October 5, 2026 | Advisory educational source | New MLN version or revised plan-of-care guidance | Individualized POC, IDG coordination, measurable outcomes, education |
| CMS Hospice coverage page | CMS public program guidance | Medicare hospice benefit | Page last updated September 8, 2026 | October 5, 2026 | Advisory summary; confirm against regulations/manuals | Page revision or benefit-policy update | Covered disciplines and comfort/symptom-management context |
| LCD L34538, Hospice Determining Terminal Status | Medicare contractor coverage guidance | Only applicable MAC jurisdiction and effective period | Revision effective August 6, 2026 shown by CMS | October 5, 2026 | Verified payer guidance; not a universal law | LCD revision, retirement, replacement, or jurisdiction change | Observations/data, individualized support, decline, and explanation of stabilization/improvement |
| California Title 22, Division 5, Chapter 6.5, DPH-18-002E | Mandatory California emergency regulation while in effect | California-licensed hospice agencies | Effective June 22, 2026 | October 5, 2026 | CDPH page states emergency rulemaking currently in effect | Readoption, permanent rule, expiration, amendment, court or OAL action | Medical-record governance, authentication, corrections, addenda, role definitions |
| CDPH AFL 26-20 | California agency guidance | California hospice agencies | June 26, 2026 | October 5, 2026 | Verified agency notice | Superseding AFL or revised regulation | Operational context for 2026 emergency hospice regulations |
| CGS disease-specific and non-disease-specific hospice guides in the SNS source library | Contractor educational derivatives of LCD guidance | Use only within applicable contractor context and source date | Available library copies revised February 16, 2022, unless the individual file states otherwise | October 5, 2026 | Historical/supporting reference; verify against current LCD before clinical use | Current LCD or guide revision | Body-system examples, decline domains, and disease-specific documentation prompts |
| 45 CFR 92.11 and 92.201 | Mandatory federal nondiscrimination requirements when the entity/program is covered by Part 92 | Covered health programs and activities within the rules’ applicability | Current eCFR text displayed up to date October 1, 2026 | October 5, 2026 | Verified; applicability must be configured and legally confirmed | Part 92 amendment, court order, agency guidance, or applicability change | Language-assistance notices, qualified interpreter/translator use, privacy, accuracy, and meaningful access |
| SNS Hospice Language Standard | Internal SNS clinical-design policy | Configured SNS tenants after approval | Version 1.1; effective only after clinical-governance approval | October 5, 2026 | Proposed | Any approved language-pack change or source-table update | Preferred/discouraged language, UI prompts, AI rules, and QA |

### 10.3 Confirmed federal requirements

- The hospice clinical record must contain past and current findings and correct clinical information, including assessments, plans of care, clinical notes, responses to medications and symptom management, certifications, directives, and orders. Entries must be legible, clear, complete, authenticated, and dated.
- The IDG prepares and coordinates a patient- and family-specific written plan of care. Federal IDG roles include physician, RN, social worker/MFT/MHC, and pastoral or other counselor, with an RN coordinating care.
- Hospice services include nursing, physician, medical-social, counseling, aide/homemaker, volunteer, PT, OT, SLP, and other covered services addressed by the regulation and plan of care.
- Professionals must act within applicable licensure, certification, registration, and scope requirements.

### 10.4 Payer and educational guidance

LCD and contractor guidance supports patient-specific documentation of observations, data, baseline and follow-up findings, progression, complications, function, and response. It does not prescribe the SNS word list and must not be used as an automatic eligibility test.

CMS plan-of-care education supports individualized needs, interventions, service scope/frequency, measurable outcomes, medications, supplies, education, and IDG coordination. The SNS phrasing rules remain internal implementation choices.

### 10.5 California requirements

For California deployment, the EMR must retain traceable authorship, authentication, dates/times, corrections, addenda, record accessibility, and linked documentation across hospice providers in the primary electronic record as required by the California provisions applicable and in effect for the release.

### 10.6 Disease-specific source notes

The disease-specific and non-disease-specific files inform body-system examples. They do not prescribe interface labels. Before using a guide for eligibility support, verify the current controlling LCD and jurisdiction.

Relevant controlled copies include:

- `cms guidelines.pdf`
- `hospice_terminal_prog_non-disease_specific.pdf`
- `heart disease.pdf`
- `hospice_terminal_prog_pulmonary_disease.pdf`
- `ALS.pdf`
- `dementia.pdf`
- `hospice_terminal_prog_stroke_coma.pdf`
- `hospice_terminal_prog_renal_failure.pdf`
- `hospice_terminal_prog_liver_disease.pdf`

### 10.7 SNS policy boundary

The word lists, discipline templates, suggestion behavior, display priorities, metadata schema, AI guardrails, and QA checklist are SNS policy. They require clinical-governance approval and must not be represented as wording mandated by CMS, CDPH, a MAC, or an accreditor.

---

## 10.8 Version 1.2 discipline-gap review

Version 1.2 adds guidance for wound/ostomy/continence specialists, respiratory therapists, inpatient/GIP/CHC clinicians, after-hours triage, interpreter/language access, HIM/medical records, privacy/security, QAPI/patient safety/risk/infection prevention, scheduling/front office, coding/CDI, patient-rights/grievance staff, pediatric/child-life support, and complementary/creative arts services when offered.

These sections are SNS implementation guidance. A role’s presence does not by itself make the service separately covered or required. The controlling plan of care, qualifications, scope, contracts, jurisdiction, payer rules, and hospice policy remain applicable.

---

## 11. Implementation rollout

1. Preserve this document in `docs/SNS_HOSPICE_LANGUAGE_STANDARD.md`.
2. Complete inventory of existing UI labels, buttons, summaries, templates, and AI prompts.
3. Map each phrase to preferred, acceptable-with-support, or discouraged.
4. Correct one active workflow at a time during its approved design review.
5. Do not run an uncontrolled repository-wide replacement.
6. Add non-blocking guidance only after wording is clinically approved.
7. Validate by discipline and body system, including RN, LVN/LPN, aide/homemaker, physician/APP, MSW/MFT/MHC, spiritual care, therapies, dietary, pharmacy, volunteer/bereavement, case management, DPCS/administration, intake, billing, DME, facility liaison, wound/ostomy, respiratory therapy, inpatient/CHC/GIP, after-hours triage, interpreter/language access, HIM, privacy/security, QAPI/infection prevention, front office, coding/CDI, grievances, pediatric support, and complementary-service roles applicable to the organization.
8. Perform one global consistency audit before field testing.
9. Field test with users of varied computer experience.
10. Revise and version the standard before organization-wide activation.

---

## 12. GitHub handoff rule

GitHub may identify vague terms, duplicate wording, unsupported generated statements, and documentation burden. GitHub may not decide clinical significance, remove clinical concepts, globally rewrite signed documentation, or enforce new wording without owner and clinical-governance approval.
