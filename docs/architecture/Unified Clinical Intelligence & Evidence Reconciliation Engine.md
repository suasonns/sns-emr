SNS Hospice EMR 

Unified Clinical Intelligence & Evidence Reconciliation Engine (UCIER) 

Clickable Mini Backlog and Implementation Plan 

Purpose: Build a traceable evidence-harvesting layer that captures overlooked observations from CHHA notes, communication logs, on-call logs, visit notes, and interdisciplinary documentation before problems stay buried. 

Compliance posture: This backlog supports documented observations, changes in condition, interdisciplinary coordination, reassessment, plan-of-care review, and source traceability. It is designed to surface evidence for RN and IDG review, not to let AI independently change diagnoses or plans of care. 

Clickable Table of Contents 

1. Vision and Scope 

2. Non-Negotiable Design Rules 

3. Target Architecture 

4. Phase 1: Foundation 

5. Phase 2: Harvesters 

6. Phase 3: Signal Processing 

7. Phase 4: Clinical Workflow 

8. Phase 5: Problem Management 

9. Phase 6: Visualization 

10. Database Backlog 

11. Sprint Priority Order 

12. Example Evidence Chain 

13. Acceptance Criteria 

14. Verification Plan 

15. Source References 

1. Vision and Scope 

SNS should not depend only on RN assessments to identify evolving patient problems. SNS should continuously harvest documented observations, findings, concerns, and reports from all care and coordination sources into one unified evidence layer. 

Primary sources include RN ICA, RN routine visits, RN PRN visits, LVN visits, CHHA visits, MSW visits, Spiritual Counselor visits, volunteer notes, communication logs, on-call logs, after-hours calls, caregiver and family calls, incident reports, facility communications, hospital notifications, IDG notes, and plan-of-care reviews. 

Primary outcomes to detect: emerging problems, functional decline, safety risks, caregiver issues, medication issues, skin issues, comfort issues, plan-of-care gaps, and missed follow-up. 

Back to top 

2. Non-Negotiable Design Rules 

Every source is harvestable. 

Nothing observed is discarded. 

Nothing harvested is anonymous. 

Nothing elevated lacks evidence. 

Every problem must show who saw it, when it was documented, where it was documented, and the original text that supports it. 

CHHA findings are first-class evidence. 

Communication logs and on-call logs are first-class evidence. 

IDG owns problems. Disciplines contribute evidence. 

Every problem must have a disposition and resolution path. 

AI may harvest, organize, and flag. AI must not silently change diagnoses, plan of care, or problem status without review workflow. 

Back to top 

3. Target Architecture 

Component 

Purpose 

Input Sources 

RN, LVN, CHHA, MSW, SC, volunteer notes, communication logs, on-call logs, family/caregiver calls, incident reports, facility messages, IDG notes, POC reviews. 

Evidence Harvester 

Extracts documented observations, statements, changes, risks, and concerns from every source. 

Source Attribution Engine 

Stamps every harvested signal with source type, source record, staff name, discipline, date/time, original text, and AI harvest timestamp. 

Patient Unified Evidence Registry 

One repository for all source-stamped observations. 

Clinical Reconciliation Engine 

Links related evidence across sources, disciplines, and time. 

RN Review Queue 

Presents meaningful signals to RN for accept, monitor, dismiss, escalate, or link to existing problem. 

IDG Evidence Queue 

Presents validated or repeated problem signals to IDG with source evidence. 

IDG Problem Registry 

Patient-level problem list owned by IDG and supported by all discipline evidence. 

Resolution Tracking 

Tracks open, monitoring, escalated, and resolved problems with history. 

Evidence Timeline 

Displays patient change over time from all sources. 

Back to top 

4. Phase 1: Foundation 

Epic 1. Patient Unified Evidence Registry 

Goal: Create one evidence repository for all patient observations from all documentation and communication sources. 

Deliverable: patient_evidence_registry 

Epic 2. Source Attribution Engine 

Goal: Require source provenance for every AI-harvested signal. 

Deliverable: source-stamped harvested signals 

Mandatory source attribution fields 

patient_id, tenant_id, source_type, source_record_id, visit_id, communication_log_id, discipline, staff_name, recorded_date, recorded_time, original_documentation, ai_harvest_timestamp, review_status 

Back to top 

5. Phase 2: Harvesters 

Epic 3. CHHA Observation Harvester 

Prevent CHHA observations from getting buried. Harvest mobility, transfers, ADLs, skin, nutrition, hydration, sleep, behavior, elimination, medication observations, caregiver observations, and safety observations. 

Epic 4. Communication Log Harvester 

Capture buried patient and caregiver problems from phone calls, caregiver calls, family calls, office calls, triage calls, after-hours calls, and on-call logs. 

Epic 5. All Discipline Harvesters 

Harvest RN assessment findings and decline indicators, LVN symptom changes and intervention response, MSW caregiver/psychosocial concerns, and Spiritual Counselor spiritual/existential support needs. 

Examples of Harvested Signals 

Walking slower 

Needs more assistance 

Sleeping longer 

Poor intake 

Patient scratching 

Medication hidden 

Unsafe transfers 

Skin redness 

Patient not taking medications 

Caregiver exhausted 

Patient confused 

Patient fell 

Back to top 

6. Phase 3: Signal Processing 

Epic 6. Patient Signal Registry 

Store observations before they become problems. States: NEW, PENDING_REVIEW, ACKNOWLEDGED, DISMISSED, ESCALATED. 

Epic 7. Clinical Reconciliation Engine 

Link related evidence from different sources while keeping every source attached. 

Epic 8. Trend Detection Engine 

Identify worsening patterns over time, such as increasing assistance, slower ambulation, repeated poor intake, or worsening weakness. 

Back to top 

7. Phase 4: Clinical Workflow 

Epic 9. RN Review Queue 

RN reviews significant signals and can accept, monitor, dismiss, escalate, or link to an existing problem. 

Epic 10. Emerging Problem Engine 

Validated trends and repeated evidence become emerging problems for review. 

Epic 11. IDG Evidence Queue 

Evidence-supported issues are prepared for IDG with source stamps and timeline. 

Back to top 

8. Phase 5: Problem Management 

Epic 12. IDG Problem Registry 

IDG owns patient problems. Disciplines contribute evidence. Problem states: OPEN, MONITORING, ESCALATED, RESOLVED. 

Epic 13. Problem Evidence Links 

Every problem must show who saw it, when, where, original text, and evidence timeline. 

Epic 14. Resolution Tracking 

Every problem must have a status, owner, review date, disposition, and resolution notes. 

Back to top 

9. Phase 6: Visualization 

Epic 15. Evidence Timeline 

Show how patient condition evolves over time across CHHA, calls, LVN, RN, MSW, SC, IDG, and POC sources. 

Epic 16. Patient Intelligence Dashboard 

Widgets: emerging problems, open problems, worsening trends, RN review queue, IDG queue, communication alerts, and CHHA alerts. 

Back to top 

10. Database Backlog 

Table 

Purpose 

patient_evidence_registry 

Source-stamped evidence repository. 

patient_harvested_signals 

Raw AI-harvested signals from notes/logs/calls. 

patient_signal_registry 

Reviewed signal state machine. 

patient_problem_registry 

IDG-owned patient problem list. 

problem_evidence_links 

Links problems to evidence records. 

problem_status_history 

Tracks lifecycle changes. 

rn_review_queue 

RN review workflow. 

idg_review_queue 

IDG agenda/evidence workflow. 

evidence_timeline 

Timeline display source or materialized view. 

Suggested patient_harvested_signals minimum columns 

id, tenant_id, patient_id, source_type, source_record_id, source_visit_id, source_communication_log_id, source_discipline, recorded_by_user_id, recorded_by_name, recorded_at, harvested_by, harvested_at, clinical_system, signal_key, signal_text, original_text_excerpt, comparison_text, trend, confidence, requires_rn_review, requires_idg_review, requires_poc_review, review_status, linked_problem_id, created_at 

Back to top 

11. Sprint Priority Order 

Sprint 1: Patient Unified Evidence Registry; Source Attribution Engine; CHHA Harvester; Communication Log Harvester. 

Sprint 2: Signal Registry; Clinical Reconciliation Engine; RN Review Queue. 

Sprint 3: Trend Detection; Emerging Problem Engine; IDG Evidence Queue. 

Sprint 4: Problem Registry; Resolution Tracking; POC Integration. 

Sprint 5: Evidence Timeline; Clinical Intelligence Dashboard. 

Back to top 

12. Example Evidence Chain 

Emerging Problem: Functional Decline 

Source 

Date/Time 

Recorded By 

Finding 

CHHA Visit Note 

07/30/2026 09:42 AM 

Maria Santos, CHHA 

Patient ambulated slower compared to last week. 

Communication Log 

07/30/2026 02:15 PM 

Office Coordinator / Caller: Daughter 

Patient needed more help getting out of bed. 

LVN Visit Note 

07/31/2026 10:10 AM 

LVN 

Weakness increased. 

Back to top 

13. Acceptance Criteria 

A harvested signal cannot be saved without source_type, source_record_id, recorded_by, recorded_at, original_text_excerpt, and review_status. 

A signal from CHHA or communication log can be created without creating a diagnosis or POC update. 

RN can review signals and choose accept, monitor, dismiss, escalate, or link to existing problem. 

Rejected/dismissed signals require a reason and reviewer stamp. 

IDG queue displays only items with traceable evidence. 

Every IDG problem displays contributing evidence by source, date/time, discipline, staff, and original excerpt. 

No problem can move to RESOLVED without resolution note and reviewer stamp. 

The UI can show a timeline for one problem using evidence from multiple sources. 

Back to top 

14. Verification Plan 

Test 

Expected Result 

CHHA note test 

Enter a CHHA note: “Patient ambulated slower compared to last week.” Verify mobility signal is created with CHHA source stamp and pending RN review. 

Communication log test 

Enter daughter call: “Patient needs more help getting out of bed.” Verify ADL/function signal is created with communication log stamp. 

Reconciliation test 

Create CHHA + communication log + LVN weakness entries. Verify possible functional decline groups them without losing original evidence. 

RN review test 

RN links the signals to Emerging Functional Decline. Verify reviewed_by and reviewed_at are written. 

IDG queue test 

Escalate to IDG. Verify IDG view shows each evidence item with date/time/staff/source/original excerpt. 

Resolution test 

Resolve problem. Verify status history includes disposition and resolution note. 

Back to top 

15. Source References 

This document was prepared from the current SNS design discussion and grounded against the following hospice compliance references: 

<File>DPH-18-002E-HospiceAgencies_Text.pdf</File> / reference_id turn162search27 and turn162search44: assessment factors, plan-of-care requirements, significant-change notification, periodic reassessment, IDG coordination, clinical notes, observations, changes in condition, and POC review. 

<File>hospice_terminal_prog_non-disease_specific.pdf</File> / reference_id turn162search51: terminal prognosis support based on documented decline, baseline and follow-up data, symptoms, weakness, ADL dependence, nutritional decline, and functional decline over time. 

<File>cms guidelines.pdf</File> / reference_id turn162search77: LCD Hospice Determining Terminal Status reference. 

<File>1.pdf</File> / reference_id turn162search81: CMS LCD L33393 Hospice - Determining Terminal Status reference. 

 

Back to top 