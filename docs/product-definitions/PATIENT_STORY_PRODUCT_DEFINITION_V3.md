# PATIENT STORY
# PRODUCT DEFINITION V3
## CONSOLIDATED AUTHORITATIVE DOCUMENT

*Supersedes and fully incorporates V1, V2, V2.1, V2.2, V2.3, and V2.4. This is
the single working product definition. No further version-numbered addenda
will be issued — future corrections revise this document directly.*

*Product-definition mode only. No code, schema, migrations, APIs, routes,
services, UI implementation, or state machines are authorized by this
document.*

```
ARCHITECTURE AUTHORIZED: NO
CODE AUTHORIZED:         NO
SCHEMA AUTHORIZED:       NO
MIGRATIONS AUTHORIZED:  NO
APIs AUTHORIZED:         NO
ROUTES AUTHORIZED:       NO
IMPLEMENTATION READY:    NO
```

---

## 1. PURPOSE

Patient Story exists to preserve the human meaning of a patient's hospice
journey — who the patient is, what matters to them, and how their journey
unfolds — in a form that is durable, source-attributed, and usable by every
discipline and by IDG, without being duplicated, distorted, or lost across
disconnected notes.

---

## 2. PRODUCT OWNERSHIP

Patient Story is accessed from the **Patient Chart**, but is not owned by
RNICA, IDG, or any single discipline. RNICA, Evidence & Intake, IDG, voice
documentation, and all disciplines **contribute** to it; none **own** it.

Ownership is chart-level, but Patient Story itself is **episode-specific**
(Section 4A). The chart holds a collection of episode-scoped stories, not one
lifetime story.

### 2.1 Designated Clinical-Record Status (decision gate)

Before architecture is authorized, SNS must obtain organizational privacy,
health-information-management (HIM), compliance, and legal confirmation on
whether Patient Story is:

**A.** part of the designated clinical record, **or**
**B.** a clinical workspace and orientation aid outside the formal designated
record set.

Until that decision is confirmed:
- Patient Story must not be presented as replacing the clinical record.
- Patient Story must not be used as the sole source for release of
  information.
- Patient Story must not be used as the sole basis for certification,
  eligibility, billing, transfer, discharge, revocation, or legal decisions.

**If Patient Story is part of the designated clinical record:**
- published content must be authenticated and dated
- amendments must preserve prior versions
- authorized record exports must follow organizational policy
- retention must follow the controlling record-retention policy
- patient and representative access must follow applicable policy and law
- access controls and disclosures must be auditable

**If Patient Story is a workspace aid:**
- it must be clearly labeled
- authoritative source records must remain directly accessible
- it must not appear to be the controlling clinical record
- formal record-production behavior must be defined

Product validation (Section 30) does not substitute for privacy, HIM, legal,
or compliance approval of this issue. See Section 28.6 for the related open
governance questions.

---

## 3. PRIMARY AND SECONDARY USERS

**Primary:** IDG members, admitting/primary RN and other direct-care
clinicians, social work, chaplaincy, Medical Director/attending.

**Secondary:** Auditors and surveyors, new team members onboarding to an
existing patient, quality/compliance reviewers, privacy/HIM reviewers.

---

## 4. CORE DEFINITIONS

- **Patient Identity** — durable, person-centered context describing who the
  patient is: relationships, values, culture, fears, priorities. Not
  demographics. Not chapter-bound. Evolves over time rather than being fixed
  at a point in time.
- **Timeline** — the chronological record of dates, encounters, and clinical
  facts as documented in the chart.
- **Story Contribution** — a discrete, attributed, reviewed statement
  proposing that a piece of documented information carries narrative or
  care-planning significance.
- **Milestone** — a story-worthy event (decline, improvement, transition,
  family change) highlighted within its chapter, not a separate chapter.
- **Chapter** — the unit of story progression, aligned to a completed IDG
  review period, scoped within one episode.
- **Episode** — one hospice admission, from Referral/Admission to a
  documented closure event. See Section 4A.
- **Patient Story** — the woven presentation of Patient Identity plus the
  chaptered Hospice Journey **for one hospice episode**.

### 4A. Hospice Episode Boundary

One Patient Story represents **one hospice episode**. It does not span
multiple admissions and does not merge episodes into one continuous
narrative.

- **Begins with:** Referral, Admission, initial hospice context.
- **Ends with:** Death, Discharge, Revocation, Transfer, or other documented
  episode closure (Section 22).

**Readmission rule:** a readmission does not continue a prior Patient
Story — it creates a **new** Patient Story. Chapter numbering does not
continue across admissions; a readmission is never treated as another
chapter; prior stories are never rewritten or merged.

```
Patient Chart
 └─ Patient Story
      ├─ Episode 1   Jan 2026 → Jun 2026   Discharged
      ├─ Episode 2   Oct 2026 → Feb 2027   Readmitted
      └─ Episode 3   Aug 2028 → Death
```

Each episode independently preserves its own Introduction, Patient Identity,
Chapters, Meaning and Goals history, and Final Chapter.

### 4B. Terminology: "Patient Identity" (not "Snapshot")

The term "Snapshot" is retired everywhere in this document. It implied a
fixed point-in-time capture, which conflicts with the approved model that
Patient Identity evolves (Section 5).

### 4C. Episode References and Prior-Episode Content Boundary

A new Patient Story may reference prior hospice episodes for historical
context:

> **Previous Hospice Episode** — Admission: 01/12/2026 · Discharge:
> 06/18/2026 · Disposition: Discharged Alive

The previous episode is viewable but **strictly read-only** and is not
incorporated into the new story automatically. See Section 22.5 for the
exact rule on referencing an episode whose Final Chapter is still pending.

**Identity reuse across episodes:** Patient Identity elements (preferred
name, important relationships, cultural/spiritual preferences, sources of
meaning, good-death preferences, important goals) may be **proposed** for
reuse from a prior episode. Nothing is copied forward automatically — every
proposed item requires re-review and re-confirmation in the new episode.

**Net rule: Identity is reusable. Identity is not inherited.**

**Prior-episode clinical content boundary:** prior-episode clinical findings
remain historical context only. A prior-episode clinical finding may not
appear as a current-episode finding unless it is documented again, or
explicitly incorporated into a current, authorized source. Do not use a
prior episode's PPS, functional state, symptom status, caregiver capacity,
diagnosis interpretation, treatment response, legal authority, or goal
status as current without current-episode evidence.

---

## 5. PATIENT IDENTITY

Contains: Who The Patient Is, What Matters Most, Family and Relationships,
Culture and Spiritual Preferences, Fears and Concerns, Sources of Meaning and
Comfort, Good-Death Preferences, Unfinished Business.

**Governance:** not unsourced free text. Every statement retains: who
supplied it, which discipline documented it, source encounter/note, date
captured, last-reviewed date, current/historical/uncertain/conflicting
status, and who last amended the displayed wording. Streamlined review
process (not the full IDG chapter-publication cycle), but never an unsourced
one. See Section 28.2 for exactly which discipline may review which kind of
Identity statement.

**Stable, not static:** rarely changes, but is not frozen. New disclosures
update it without erasing prior content; updates are additive and
documented.

**"Who speaks for the patient":** Patient Identity may display persons
important to the patient, persons the patient wants involved, and preferred
communication contact. Legal decision-making authority is never created,
inferred, or overridden here — cross-referenced only from its authoritative
Face Sheet/advance-directive/legal-representative source.

**Scope:** per-episode (Section 4A/4C) — reusable across episodes by
explicit proposal only, never inherited automatically.

---

## 6. INTRODUCTION

A one-time-per-episode narrative establishing why hospice was considered,
referral/admission context, starting clinical/functional baseline, initial
caregiver/living situation, and the patient or family's own perspective —
patient statements and family reports kept distinct.

**Authorship:** source documents provide evidence; AI may propose
source-grounded wording; an authorized clinician reviews, edits, and
approves it. Published Introduction is **clinician-reviewed and
clinician-approved** — not necessarily typed from scratch ("clinician-
authored" is not used unless literally true).

**Amendment rule — full decision at Section 28.3.** In summary: the
Introduction may be amended after the first chapter closes only for factual
correction, corrected attribution, or missing/newly available historical
referral or admission information. Later clinical developments, goals, or
caregiver circumstances never rewrite the Introduction — they belong in the
applicable chapter or the current Meaning and Goals thread. Every amendment
preserves prior wording, amended wording, reason, source, author/reviewer,
date/time, attribution, and amendment history. The Introduction must never
silently regenerate, be rewritten to make later events appear predictable,
backdate later findings into admission context, or become certification/
eligibility prose.

---

## 7. HOSPICE JOURNEY LAYER

The chaptered progression of one episode's hospice journey, built from
reviewed Story Contributions. Scoped to "the patient's hospice journey" —
never a hard-coded six-month duration. Begins at the episode's
referral/admission context and continues through the actual episode length.

---

## 8. IDG CHAPTER MODEL

Each completed IDG review period within an episode is representable as a
chapter. Milestones are highlighted *inside* their chapter, never a separate
chapter. Recertification is a cross-cutting lens applied across chapters
**within one episode** — never across episode boundaries. Prior chapters are
never silently rewritten.

### 8.1 Discipline and Source Availability

A chapter must distinguish (product meanings only, not authorized database
states):

- **DOCUMENTED_FINDING**
- **NO_MATERIAL_CHANGE_DOCUMENTED**
- **SOURCE_NOT_AVAILABLE**
- **DISCIPLINE_NOTE_NOT_AVAILABLE**
- **VISIT_NOT_COMPLETED**
- **REVIEW_PENDING**
- **NOT_APPLICABLE**
- **UNABLE_TO_DETERMINE**

The absence of documentation must never be displayed as: no concern, no
change, negative finding, normal, or resolved. A discipline with no
available note during the review period must not appear to have completed
an assessment.

### 8.2 Ready for IDG Review

A chapter is ready for IDG review when: the review period is identified;
eligible authenticated records have been evaluated; high-priority pending
proposals are visible; material conflicts are visible; patient and family
priorities have been reviewed when documented; hospice responses are linked
when documented; unresolved issues are identified; missing-discipline
documentation is labeled (Section 8.1); source links have been verified; and
any urgent issue has already been routed through the appropriate workflow
(Section 17.1).

**"Ready for IDG Review" does not mean:** every discipline documented, every
field populated, every conflict resolved, every goal fulfilled, or every
proposed contribution accepted. Do not create false completeness merely to
close a chapter.

---

## 9. DISCIPLINE CONTRIBUTION RULES

Each discipline may contribute story material grounded in its own documented
encounters within the current episode. A contribution becomes part of
Patient Story only when source-linked, correctly attributed, and reviewed by
a reviewer with scope-appropriate authority — full decision at **Section
28.2**. Routine, unchanged documentation does not itself become a new
contribution.

---

## 10. STORY-WORTHINESS RULES

- **Always** story-worthy: clinical decline, functional decline, caregiver
  change, significant patient/family wish, goal change, care transition.
- **Sometimes** story-worthy: stable-but-significant terminal burden,
  meaningful improvement after intervention.
- **Usually not** story-worthy: routine unchanged visit notes, duplicate
  administrative documents.

Routine stability does not generate false story progression, but clinically
meaningful stability can be represented when relevant.

---

## 11. MEANING AND GOALS FRAMEWORK

Tracked categories: relationships, life roles/events, goals,
cultural/spiritual preferences, personal priorities, sources of
meaning/comfort, good-death preferences, fears/concerns, unfinished
business.

**Lifecycle statuses** (product-level meaning, not a database state):
CURRENT, REAFFIRMED, REVISED, FULFILLED, NO_LONGER_APPLICABLE, SUPERSEDED,
CONFLICTING, UNABLE_TO_VERIFY. Earlier preferences are preserved, never
erased, when superseded.

**Goal responsibility:** every approved current goal must answer: who stated
it, when, current lifecycle meaning, responsible discipline for follow-up,
next review point, whether it requires action through another workflow
(Section 18.2), whether it is actionable/aspirational/informational, and —
if fulfilled or revised — what source confirms it. Not every goal becomes an
order or plan-of-care intervention, but no actionable goal is left without a
visible follow-up owner, and Patient Story never independently authorizes
the response.

---

## 12. FAMILY INTERVIEW RULES

Family conversation may contribute to Patient Identity and Meaning/Goals
only under the classification in Section 14, with full source excerpt and
reviewer verification of interpretive language. Conflicting family accounts
remain visible, never silently merged (Section 16).

---

## 13. VOICE-TO-DOCUMENTATION RULES

```
Raw audio → transcript → clinician-reviewed note → authenticated note →
proposed contribution → clinician review → Patient Story
```

No contribution is ever published from raw audio or an unreviewed
transcript. Speaker attribution (patient/family member/representative/
clinician) must be explicit; if undeterminable, no publishable contribution
is generated. Background/off-topic mic-active conversation is excluded.
Clinician interpretation may be proposed only when deliberately retained in
the authenticated note, worded as clinician assessment, tied to identifiable
findings, and reviewed — never from exploratory language ("might be," "could
be," "seems like") without supporting observation.

---

## 14. ATTRIBUTION HIERARCHY

- **Patient-Stated**
- **Family-Reported Current** — "the family reports that the patient
  currently holds the preference" (a family report, never equivalent to
  Patient-Stated)
- **Family-Reported Historical**
- **Family Interpretation**
- **Family's Own Preference**
- **Representative-Reported**
- **Clinician-Observed**
- **Source-Documented**
- **Unknown or Conflicting**

Only current, direct patient confirmation is displayed as a current
Patient-Stated preference. If the patient cannot communicate,
family/representative attribution is preserved as such; legal
decision-making authority is never inferred from family involvement and
always links to its authoritative workflow.

---

## 15. PATIENT QUOTATION RULES

A concise clinical summary may pair with an optional short direct quotation,
with visible attribution and source link. Quotations are sparing, never
used under uncertain transcription confidence or ambiguous speaker
attribution, never expose unnecessarily sensitive conversation, and never
paraphrase in a way that changes meaning. A clinician's spoken question is
never attributed as a patient statement.

---

## 16. CONFLICT REPRESENTATION AND AUTHORIZED RESOLUTION

*(Full replacement per owner revision — Patient Story is not an actor.)*

Patient Story displays conflicting perspectives side by side.

Each perspective must preserve: source; speaker or information provider;
attribution classification; documenting discipline; date; current review
status.

Patient Story **may display:** responsible follow-up workflow; responsible
discipline; date last reviewed; documented clarification; documented
reconciliation; continued disagreement; verification against an
authoritative record; final disposition when documented.

Patient Story **does not:** determine which account is correct; adjudicate
family disagreements; determine legal authority; select a surrogate;
determine code status; interpret an advance directive; enter or change an
order; choose a treatment direction; resolve a conflict independently.

Authorized people and authoritative workflows perform clarification,
verification, reconciliation, escalation, and disposition. Patient Story
records and displays the documented outcome.

Conflicts involving legal authority, representative/surrogate designation,
code status, advance directives, treatment direction, orders, discharge
disposition, revocation, transfer, certification, or eligibility must link
to their authoritative record and workflow.

If disagreement remains unresolved, Patient Story displays **CONTINUED
DISAGREEMENT**. It must not silently select one account as true.

The family-versus-family conflict closure rule is defined at **Section
28.1**.

---

## 17. AI RESPONSIBILITIES AND PROHIBITIONS

**AI may:** detect candidate Identity/Journey statements, extract exact
supporting language, propose a concise contribution, identify the
information source and attribution, suggest a destination category, flag
likely duplicates or contradictions, identify a potential change in a prior
goal.

**AI may never:** invent a goal, dramatize or add emotional language absent
from the source, infer family dynamics/culture/religion/spirituality/what a
good death means, decide which family member matters most, convert a family
preference into a patient preference, auto-resolve conflicts,
publish/amend/lock/delete Patient Story content, use an unauthenticated note
as published evidence, treat a transcript error as clinical truth, calculate
or declare eligibility, or produce certification language.

### 17.1 Urgent Safety and Incident Boundary

Patient Story is **not** an urgent-alert, incident-reporting,
emergency-response, mandated-reporting, or supervisory-escalation system.

Information indicating possible: uncontrolled symptoms, immediate patient
danger, medication danger, caregiver collapse, suspected abuse or neglect,
self-harm or violence risk, imminent loss of essential care, urgent
equipment failure, or immediate environmental danger — **must route
immediately** through the existing authorized clinical, supervisory,
incident, emergency, or reporting workflow.

Patient Story may later display a reviewed, source-linked contribution
describing the documented event and hospice response. Patient Story must
not delay urgent action while waiting for AI processing, contribution
review, IDG review, or chapter publication.

---

## 18. CLINICIAN REVIEW

Every contribution requires human review, by a reviewer with scope-
appropriate authority (Section 28.2), before publication. Reviewer sees:
proposed contribution, category, exact source excerpt, source note/author/
date, attribution, related existing content, possible conflict/duplicate.
Reviewer actions: Accept, Edit and Accept, Reject, Defer, Mark Duplicate,
Mark Conflict, Change Attribution, Change Category. Editing the contribution
never edits the source note; rejecting never removes source information.

### 18.1 Review and Publication Meanings

Patient Story must distinguish:

- **AI PROPOSAL** — content suggested by AI but not reviewed or published.
- **CLINICIAN-REVIEWED PROPOSAL** — reviewed by an authorized clinician but
  not yet included in published story content.
- **CLINICIAN-AUTHENTICATED CONTRIBUTION** — approved with: reviewer
  identity, reviewer role, date and time, exact source, source version,
  final approved wording, attribution, applicable chapter.
- **IDG-REVIEWED CHAPTER** — a chapter reviewed through the IDG workflow.
- **PUBLISHED CHAPTER** — the approved chapter visible as part of Patient
  Story.
- **AMENDED CHAPTER** — a published chapter with a visible, additive
  correction.
- **HISTORICAL VERSION** — a prior reproducible version preserved after an
  amendment.

**No AI proposal may appear as published clinical truth.**

### 18.2 Contribution Disposition

Every accepted Story Contribution must identify whether it is (product
meanings only, not authorized database enums):

- STORY_ONLY
- NO_ACTION_REQUIRED
- IDG_REVIEW_REQUIRED
- POC_REVIEW_REQUIRED
- ORDER_REVIEW_REQUIRED
- ACP_REVIEW_REQUIRED
- SAFETY_ESCALATION_REQUIRED
- LEGAL_AUTHORITY_REVIEW_REQUIRED
- CAREGIVER_SUPPORT_REVIEW_REQUIRED
- OTHER_AUTHORIZED_WORKFLOW_REQUIRED

Patient Story does not execute the action. It displays: required
destination workflow, responsible role or discipline, current follow-up
state, source, date. The authoritative workflow records the clinical
action.

### 18.3 Source Correction

If a source note or document is corrected after a contribution is accepted:
the published contribution is not silently rewritten; the contribution is
marked **SOURCE_UPDATED**; the corrected source remains linked according to
record policy; an authorized reviewer must confirm, amend, supersede, or
withdraw the contribution; prior published wording remains reproducible;
amendment history remains visible.

### 18.4 Source Loss or Access Change

If a source is superseded, entered in error, becomes unavailable, becomes
restricted to the current user, is removed under policy, or belongs to a
prior episode — Patient Story must not display an unsupported orphan claim
as though the source remains verified. Display an appropriate status such
as: SOURCE_SUPERSEDED, SOURCE_CORRECTED, SOURCE_RESTRICTED,
SOURCE_UNAVAILABLE, PRIOR_EPISODE_SOURCE, REVIEW_REQUIRED (product meanings
only; no new technical states are authorized).

### 18.5 Late Documentation

When a note is entered after the applicable chapter has closed: preserve
the event/effective date when documented; preserve the documentation date;
do not backdate publication; do not silently insert the contribution into
the closed chapter; do not silently rewrite the closed chapter.

**Allowed product paths:**
- **A.** Amend the closed chapter through the authorized amendment workflow.
- **B.** Display the contribution in the current chapter labeled "Late
  documentation concerning a prior review period."
- **C.** Exclude the contribution when it is duplicate, unsupported, or not
  story-worthy.

A late entry affecting a closure event, legal authority, order, plan of
care, certification, or discharge must route to its authoritative workflow.

### 18.6 Multiple-Source Handling

When multiple sources describe the same event, distinguish:
- **CORROBORATING SOURCE** — a separate source independently supports the
  same material fact.
- **DUPLICATE CONTENT** — a source repeats substantially the same
  information without adding a distinct perspective or evidentiary value.
- **DISTINCT DISCIPLINE PERSPECTIVE** — the sources discuss the same event
  from different scope-appropriate perspectives.
- **CONFLICTING SOURCE** — the sources materially disagree.

Patient Story must not remove a valid discipline perspective merely because
another discipline documented the same event, and must not create repeated
story statements from duplicate text.

---

## 19. IDG WORKFLOW

IDG uses Patient Story as pre-meeting orientation, not a replacement for the
record (Section 25's 60-second usability target). See Section 28.4 for the
Next-Period Focus artifact IDG produces and Patient Story displays.

---

## 20. AUDITOR AND REVIEWER WORKFLOW

An authorized reviewer can follow progression across chapters within an
episode; compare baseline to later findings; identify the source behind
every displayed claim; identify whether hospice responded to a documented
change; distinguish Patient Story from certification, plan of care, orders,
and advance directives; and open the underlying record without manually
searching the entire chart. Patient Story assists navigation and
understanding — it does not replace source-record review.

---

## 21. RECERTIFICATION LENS

A cross-cutting review lens applied across chapters **within one episode** —
not a separate chapter, and never crossing an episode boundary.
Recertification reviews relevant findings across chapters without altering
them. See Section 28.4 for Next-Period Focus, the related IDG artifact.

---

## 22. FINAL CHAPTER PRODUCT DEFINITION

The Final Chapter closes the hospice journey **without inventing meaning,
eligibility conclusions, cause of death, or future outcomes.**

### 22.1 Triggering closure events
Death · Discharge (including "Discharged Alive" / extended prognosis) ·
Revocation · Transfer (to another hospice) · Other documented episode
closure.

### 22.2 Required contents of every Final Chapter

**A. Closure Facts** — closure type; effective date; authoritative source;
disposition; last chapter period; responsible documenting workflow.

**B. Closing-Period Summary** — a concise, source-grounded account of:
meaningful changes during the final review period; current functional and
symptom state when documented; patient and family priorities at closure;
caregiver context when relevant; hospice response during the final period;
unresolved issues at closure.

**C. Meaning and Goals at Closure** — for each active goal: current
lifecycle meaning; fulfilled/revised/superseded/unresolved/no-longer-
applicable status; documented source; date last reviewed.

**D. Source Links** — links to: authoritative closure record; final clinical
note or death/discharge documentation; final IDG chapter when available;
relevant transfer or revocation document; amendments or corrections.

**E. Immutability** — no silent rewrite; corrections remain visible and
additive; prior wording remains historically reproducible.

### 22.3 Final Chapter by closure type

**Death** — display only documented facts: date/time when present, place
when present, persons present only when documented and relevant, final
patient/family priorities, hospice response in the final period, unresolved
issues, authoritative death documentation. Do **not** infer cause of death,
create sentimental narrative, infer whether death was peaceful, infer goal
fulfillment, or replace death documentation/bereavement workflows.

#### 22.3.1 Death and Bereavement Boundary

The death Final Chapter closes the patient's hospice journey. Bereavement
documentation created after death remains linked to the closed hospice
episode but belongs to the authoritative bereavement workflow.

Post-death bereavement activity does **not** create: a new Patient Story
chapter, an extension of the deceased patient's clinical journey, or
additional clinical decline content.

Patient Story may display a limited bereavement-status reference only when
authorized, relevant, consistent with privacy policy, and sourced from the
bereavement workflow. Patient Story does not expose private bereavement
counseling content merely because it is linked to the same episode.
Bereavement services are recognized as support provided before and after
death, but Patient Story remains focused on the patient's hospice journey.

**Discharge — no longer terminally ill / extended prognosis** — display
authoritative discharge reason, discharge date, final documented
clinical/functional state, last-known goals, unresolved needs, documented
follow-up/transition information, source discharge order/note. Do not
describe stability as cure, speculate about future readmission, or
independently determine eligibility. Medicare contractor guidance states
that a patient who improves or stabilizes enough to no longer have a
prognosis of six months or less should be considered for discharge, and may
later re-elect hospice if again eligible; the source clinical record and
physician judgment remain authoritative.

**Discharge for move outside service area** — display documented move/
service-area reason, effective date, known transition information,
unresolved care needs, authoritative discharge documentation. Do not assume
transfer to another hospice unless documented.

**Discharge for cause** — display only the formal documented disposition and
care-transition facts permitted for Patient Story. Do not copy allegations,
stigmatizing language, or unnecessary behavioral details. Maintain links to
the authoritative discharge record.

**Revocation** — display that the patient or authorized representative
revoked the hospice election, effective date, documented current goals or
stated reason only when the source records it and inclusion is relevant,
unresolved care needs, authoritative revocation document. Do not
characterize the patient's decision, infer dissatisfaction, criticize the
patient/family, imply revocation equals discharge for cause, or speculate
about future care.

**Transfer** — display transfer effective date, receiving hospice when
documented, current unresolved issues, last-known goals, source transfer
documentation, whether an authorized handoff was completed. Do not merge the
receiving hospice's later documentation, continue chapter numbering, assume
the receiving hospice uses SNS, or imply the story continues under the
receiving hospice. Full transfer-handoff rule at **Section 28.5**.

**Other documented closure** — display exact authoritative closure
classification, date, source, minimal source-grounded explanation,
unresolved issues, last-known Meaning and Goals state. Do not create a
generic narrative when the closure classification is unclear — flag the
closure for authorized review instead.

### 22.4 Immutability rule

Once a Final Chapter is created for a closure event, prior chapters and the
Final Chapter itself are not rewritten. A correction to a factual error
follows the same amendment-preserving pattern as any other Patient Story
content (Sections 6/18): the correction is visible, and prior wording/
history is preserved, never silently replaced.

### 22.5 Prior-Episode Reference

An authoritative closed episode may appear as a read-only prior-episode
reference **when the authoritative closure record exists.** A completed
Final Chapter is **not required** merely to show that the prior episode
existed.

If the episode is closed but the Final Chapter is incomplete, display:
**"Episode closed. Final Chapter pending review."** The incomplete Final
Chapter becomes a visible workflow or quality item. The prior episode
remains read-only; no information copies automatically; a new admission
still creates a new Patient Story; completing or amending the prior Final
Chapter does not modify the new story. A valid historical episode is never
hidden merely because its narrative review is pending.

### 22.6 Acceptance criteria

- [ ] Every closed episode has exactly one Final Chapter.
- [ ] Closure type and date match the authoritative discharge/death/
      revocation/transfer record.
- [ ] Unresolved issues at closure remain visible, not silently dropped.
- [ ] Last-known Meaning and Goals state is preserved at closure.
- [ ] No Final Chapter speculates about outcomes beyond what is documented.
- [ ] A closed episode's Final Chapter is never edited to reopen the
      episode; corrections are additive/visible, not silent replacements.
- [ ] A closed episode with a closure record but pending Final Chapter
      narrative still appears as a read-only reference, clearly labeled.
- [ ] Transfer content never merges the receiving hospice's later
      documentation or assumes its software system.
- [ ] Post-death bereavement activity never creates a new chapter or
      clinical-decline content for the closed episode.

---

## 23. PRIVACY, RELEVANCE, AND CONTENT-MINIMIZATION RULES

Patient Story humanizes the patient without becoming an unrestricted
biography. Include only what helps the team understand the patient,
communicate respectfully, plan care, preserve what matters, understand the
journey, or respond to needs. Exclude: unrelated family secrets, gossip,
unsupported allegations, unnecessarily detailed trauma history, unrelated
sensitive information about another person, financially detailed material
without care relevance, stigmatizing language, biographical trivia without
care relevance.

Content minimization is an SNS Patient Story product rule — it does not
replace the organization's existing privacy, security, access-control,
disclosure, or record-retention policies. See Section 2.1 and Section 28.6
for the unresolved designated-record and access governance questions.

---

## 24. AUTHORITATIVE WORKFLOW BOUNDARIES

| Domain | Authoritative for | Patient Story's role |
|---|---|---|
| Plan of Care | Interventions | Informs, never substitutes |
| Orders | Authorized clinical actions | Never authorizes or implies an order |
| Advance-Care Planning / legal authority | Code status, representative/surrogate designation | Cross-references only |
| Certification / eligibility | Regulatory eligibility determination, physician narrative | Not a certification, eligibility determination, or independent basis for eligibility; may provide source-linked orientation to documented findings only |
| Conflict resolution (Section 16) | Clarification, verification, reconciliation performed by the responsible clinical/legal/IDG workflow | Displays and records the outcome; never adjudicates |
| Transfer handoff (Section 28.5) | Authorized transfer/HIE workflow | Not automatically transmitted; contributes only through that workflow |
| Urgent safety/incident (Section 17.1) | Existing clinical/supervisory/incident/emergency/reporting workflow | Never delays urgent action; may later display a reviewed contribution |
| Bereavement (Section 22.3.1) | Authoritative bereavement workflow | May display a limited, authorized status reference only |

---

## 25. ACCEPTANCE CRITERIA

**Product identity:** Patient Story preserves both Identity and Journey;
Identity is not reduced to demographics; not RNICA-owned; remains distinct
from Timeline, Face Sheet, notes, POC, certification; represents exactly one
hospice episode.

**Episode boundary:** readmission always creates a new story; chapter
numbering never continues across episodes; prior episodes are read-only
references (available even with a pending Final Chapter, per 22.5); Identity
reuse is always proposed, never automatic; prior-episode clinical findings
never appear as current without current-episode evidence.

**Governance:** no unsourced/anonymous Identity edits; every Identity
statement carries attribution + accountability metadata; updates are
additive; legal authority never inferred by Patient Story; review authority
is scope-appropriate per discipline (Section 28.2); the designated-record
status decision (Section 2.1) is confirmed before architecture proceeds.

**Attribution:** all family-relation states remain visually distinct; a
family statement never silently becomes patient-stated.

**Quotation:** sparing use only; never under uncertain attribution;
clinician questions never attributed to patient.

**Voice/transcript:** no publication from raw audio or unreviewed
transcript; undeterminable speaker blocks publication; clinician
interpretation requires deliberate retention + review; exploratory language
never finalized as fact.

**Conflict:** always shown, never adjudicated by Patient Story itself;
legal/order-related conflicts route to authoritative workflow; family-vs-
family conflict closure follows the seven documented outcomes in Section
28.1.

**Goals lifecycle:** all 8 statuses representable; superseded goals
preserved; every current goal answers the Section 11 responsibility
questions and carries a Section 18.2 disposition; no independent
authorization of clinical action.

**Privacy:** no care-irrelevant/stigmatizing/gossip content; neutral
wording; minimization stated as a product rule, not a substitute for org
policy.

**Introduction:** per Section 28.3 — explains why hospice was considered,
referral/admission context, baseline, initial caregiver/living situation;
preserves patient/family perspective distinctly; links to sources;
clinician-reviewed and approved; not silently regenerated; amendments after
first-chapter-close are limited to the permitted reasons and always
preserve history; never becomes certification prose.

**Chapters:** each completed IDG period (within an episode) representable as
a chapter; missing-discipline documentation labeled per Section 8.1; ready-
for-review does not imply false completeness (Section 8.2); milestones
inside correct chapter; no false progression from routine notes; meaningful
stability representable; each material change has a documented source and
(if present) hospice response; unresolved issues carry forward via
Next-Period Focus (28.4); prior chapters never silently rewritten;
recertification reviews across chapters within one episode only; Final
Chapter reflects documented closure per Section 22.

**Source & review:** every published contribution links to an authenticated
source; View Source opens the exact record/version; source date/author
visible; excerpt preserves context; reviewing clinician recorded; rejected/
deferred proposals never appear as published facts; duplicates don't create
duplicate statements (Section 18.6); conflicts remain visible; AI cannot
publish/amend/lock/delete content; source corrections and source loss are
handled per Sections 18.3–18.4; late documentation follows Section 18.5.

**Safety:** urgent safety information always routes through the existing
authorized workflow first, never delayed for Patient Story processing
(Section 17.1).

**IDG value (60-second target — usability, not regulatory):** an authorized
IDG user can identify in under 60 seconds why the patient entered hospice,
what changed since the previous IDG, current clinical/functional
trajectory, current symptom concerns, current caregiver risks, current
patient/family priorities, significant events, hospice response, unresolved
issues, next-period focus.

**Auditor/reviewer:** per Section 20.

**Usability:** a new team member identifies who the patient is and what
matters most in under 60 seconds; Patient Story remains readable and does
not become a note dump; no participant confuses Timeline with Patient
Story; no participant believes Patient Story independently determines
eligibility.

---

## 26. PRODUCT TEST SCENARIOS

Scenarios 1–30 (foundational) and 31–55 (regulatory/workflow expansion). Each
scenario is validated using the structure: **Given / When / Then / Must
Remain Unchanged / Attribution Requirement / Source Requirement / Review
Requirement / Expected User Understanding.**

### 26.1 Foundational scenarios (1–30)

1. Initial story from H&P and referral
2. Duplicate administrative document
3. Authenticated voice note
4. Unauthenticated voice draft
5. Routine stable visit
6. PPS decline
7. Functional decline
8. Caregiver change
9. Important patient wish
10. Goal changes over time — new proposal recorded REVISED/SUPERSEDED;
    prior stated goal remains visible, attributed, dated
11. Duplicate documentation across disciplines
12. Conflicting sources
13. Improvement after intervention
14. Stable but significant terminal burden
15. IDG chapter draft
16. Chapter review
17. Next IDG period
18. Late note after chapter closure
19. Cross-patient isolation
20. Cross-tenant isolation
21. Role restriction
22. Source correction or amendment
23. Episode closure / Final Chapter creation
24. Historical review
25. Accessibility
26. New admission after prior discharge (new story created, no auto-merge)
27. Clinician reviews and selectively reuses prior-episode Identity data
28. Clinician declines all reuse; new episode starts from a blank Identity
    slate
29. Attempted cross-episode chapter numbering or story merge (must not
    occur)
30. Correction to a Final Chapter after closure (additive/visible only)

### 26.2 Regulatory and workflow expansion scenarios (31–55)

Each entry below is written as
**Given → When → Then → Unchanged → Attribution → Source → Review →
Understanding.**

**31. Death with documented final patient goals**
Given a death closure with documented final-period goals → When the Final
Chapter is created → Then goals display with their last lifecycle status →
Unchanged: prior goal history → Attribution: as originally recorded →
Source: final-period notes → Review: clinician-confirmed at closure →
Understanding: reviewer sees what mattered to the patient at the end without
invented meaning.

**32. Death without a final-period assessment**
Given a death with no final-period assessment documented → When the Final
Chapter is generated → Then it shows the last available documented state
labeled with its actual date, not a fabricated current state → Unchanged:
earlier chapters → Attribution: as last documented → Source: last available
note → Review: clinician confirms absence is disclosed, not hidden →
Understanding: reviewer knows exactly how current the closing information is.

**33. Discharge because the patient is no longer terminally ill**
Given a discharge for extended prognosis → When the Final Chapter is created
→ Then it displays the authoritative discharge reason without describing
stability as cure or speculating about readmission → Unchanged: PPS/goal
history → Attribution: physician/discharge order → Source: discharge
documentation → Review: physician-confirmed → Understanding: reviewer
understands discharge is a documented clinical determination, not a product
inference.

**34. Discharge after moving outside the service area**
Given a documented move → When Final Chapter created → Then it shows the
move reason and effective date only, no assumption of hospice transfer →
Unchanged: prior chapters → Attribution: discharge documentation →
Source: discharge record → Review: documenting workflow confirmed →
Understanding: reviewer does not assume continuity of hospice care elsewhere.

**35. Discharge for cause with sensitive documentation**
Given a for-cause discharge with sensitive supporting notes → When Final
Chapter created → Then only the formal disposition and permitted
care-transition facts display, no allegations/stigmatizing language →
Unchanged: source note (unaltered, access-controlled) → Attribution:
discharge record → Source: authoritative discharge documentation →
Review: HIM/compliance-consistent → Understanding: reviewer sees a neutral,
minimally-detailed closure record.

**36. Revocation without a documented reason**
Given a revocation with no stated reason → When Final Chapter created →
Then it shows only that revocation occurred and its effective date, no
inferred reason → Unchanged: prior goals → Attribution: revocation document
→ Source: revocation form → Review: confirmed by documenting workflow →
Understanding: reviewer does not see a fabricated rationale.

**37. Revocation with a patient-stated reason**
Given a revocation with a documented patient-stated reason → When Final
Chapter created → Then the stated reason displays attributed as
Patient-Stated → Unchanged: earlier goal history → Attribution:
Patient-Stated → Source: revocation documentation → Review: clinician-
confirmed → Understanding: reviewer sees the patient's own words, not a
paraphrase presented as clinical interpretation.

**38. Transfer to another hospice**
Given a transfer → When Final Chapter created → Then it shows transfer date,
receiving hospice if documented, unresolved issues, and whether an
authorized handoff occurred, without merging future receiving-hospice
documentation → Unchanged: sending provider's chapters → Attribution:
transfer documentation → Source: transfer record → Review: sending-provider
workflow confirmed → Understanding: reviewer understands the sending
provider's story ends here; the receiving hospice's records are separate.

**39. Other or unclear closure requiring review**
Given an ambiguous closure classification → When Final Chapter attempted →
Then the system flags it for authorized review instead of generating a
generic narrative → Unchanged: nothing published prematurely → Attribution:
n/a until classified → Source: pending → Review: required before
publication → Understanding: reviewer knows this closure needs a human
decision.

**40. Closed episode with Final Chapter pending**
Given a closure record exists but Final Chapter narrative incomplete →
When a user references the episode → Then it displays "Episode closed. Final
Chapter pending review." → Unchanged: read-only status → Attribution: n/a →
Source: closure record → Review: pending, visibly flagged → Understanding:
reviewer knows the episode is real and closed, but its narrative isn't done.

**41. New admission while the prior Final Chapter is pending**
Given readmission occurs before prior Final Chapter completes → When new
Patient Story is created → Then it is fully independent; completing the old
Final Chapter later does not alter the new story → Unchanged: new episode
content → Attribution: independent → Source: independent → Review:
independent → Understanding: reviewer sees two clearly separate stories.

**42. Source note corrected after chapter publication**
Given a published contribution whose source note is later corrected → When
correction is saved → Then the contribution is marked SOURCE_UPDATED, not
silently rewritten → Unchanged: prior published wording, reproducible →
Attribution: original + correction note → Source: corrected note linked →
Review: authorized reviewer confirms/amends/supersedes/withdraws →
Understanding: reviewer sees both what was said and what was corrected.

**43. Source note entered in error**
Given a source is marked entered-in-error → When Patient Story evaluates
dependent contributions → Then affected contributions show SOURCE_CORRECTED
or SOURCE_SUPERSEDED, never presented as still verified → Unchanged: audit
trail → Attribution: preserved → Source: error status linked → Review:
required → Understanding: reviewer never mistakes an erroneous source for
current truth.

**44. Source becomes restricted or unavailable**
Given a source becomes access-restricted for the current user → When
Patient Story renders the contribution → Then it shows SOURCE_RESTRICTED
rather than exposing or silently dropping the claim → Unchanged: content for
authorized users → Attribution: preserved → Source: restricted-status shown
→ Review: per access policy → Understanding: reviewer understands why a
claim's source isn't visible to them specifically.

**45. Goal fulfilled shortly before closure**
Given a goal is fulfilled just before episode closure → When Final Chapter
is created → Then the goal shows FULFILLED with its confirming source →
Unchanged: prior goal states → Attribution: source of fulfillment evidence →
Source: confirming note → Review: clinician-confirmed → Understanding:
reviewer sees a genuine, sourced outcome, not an assumed happy ending.

**46. Unresolved family disagreement at closure**
Given a family conflict never reached a documented outcome → When Final
Chapter is created → Then it displays CONTINUED DISAGREEMENT at closure,
never silently resolved → Unchanged: original conflicting statements →
Attribution: both perspectives preserved → Source: original notes → Review:
responsible workflow's last documented status → Understanding: reviewer
knows the disagreement was real and never adjudicated by the product.

**47. Transfer handoff completed through an authorized workflow**
Given an authorized transfer/HIE workflow includes selected Patient Story
information → When the handoff packet is produced → Then it includes only
authorized, source-attributed information, excludes unsupported AI
synthesis → Unchanged: sending provider's Patient Story → Attribution:
preserved in the packet → Source: authoritative transfer workflow → Review:
per that workflow's own authorization → Understanding: receiving party gets
attributed facts, not an implied story continuation.

**48. Post-death bereavement note**
Given a bereavement contact note is created after death → When linked to
the closed episode → Then it does not create a new chapter or clinical
content, and remains within the bereavement workflow's own privacy rules →
Unchanged: Final Chapter → Attribution: bereavement workflow → Source:
bereavement record → Review: per bereavement policy → Understanding:
reviewer does not see bereavement counseling content mixed into the clinical
journey.

**49. Late documentation concerning a prior chapter**
Given a note is entered after its chapter closed → When Patient Story
evaluates it → Then it is either routed through the amendment workflow,
shown in the current chapter as "Late documentation concerning a prior
review period," or excluded as non-story-worthy/duplicate → Unchanged:
original closed chapter (unless a proper amendment) → Attribution:
original documentation date preserved → Source: the late note → Review:
required before any placement decision → Understanding: reviewer is never
misled about when information was actually known.

**50. Duplicate fact documented by nursing and social work**
Given both disciplines record essentially the same fact → When AI proposes
contributions → Then it is flagged DUPLICATE CONTENT, not published twice →
Unchanged: both source notes remain intact → Attribution: single
attributed statement retains its originating discipline → Source: primary
originating note → Review: reviewer confirms duplicate designation →
Understanding: reviewer sees one clear statement, not redundant noise.

**51. Same event documented from distinct discipline perspectives**
Given nursing and chaplaincy document the same event differently → When AI
proposes contributions → Then both are retained as DISTINCT DISCIPLINE
PERSPECTIVE, not collapsed → Unchanged: each note → Attribution: each
discipline's own → Source: each respective note → Review: each reviewed by
its scope-appropriate discipline (Section 28.2) → Understanding: reviewer
sees the full, undiminished multi-disciplinary picture.

**52. Urgent safety issue identified in a note**
Given a note describes an urgent safety concern → When detected → Then it
is never held pending AI/IDG/chapter review — it routes immediately through
the existing safety/incident workflow (Section 17.1); Patient Story may
later show a reviewed, source-linked contribution describing the event and
response → Unchanged: n/a (urgent path bypasses story-publication delay) →
Attribution: as documented → Source: the originating note → Review: safety
workflow first, story contribution after → Understanding: reviewer
understands Patient Story never gates or delays urgent safety response.

**53. Missing discipline note during an IDG period**
Given a discipline has no note for the period → When the chapter is
prepared → Then it displays DISCIPLINE_NOTE_NOT_AVAILABLE, never "no
concern" or "normal" → Unchanged: chapter readiness criteria (Section 8.2)
→ Attribution: n/a → Source: n/a, explicitly labeled absent → Review: IDG
aware of the gap → Understanding: reviewer distinguishes "nothing wrong"
from "nothing documented."

**54. Prior-episode clinical finding proposed as current**
Given AI or a user attempts to carry a prior episode's clinical finding
(e.g., PPS) into the current episode without new evidence → When evaluated
→ Then it is blocked/flagged per Section 4C's prior-episode content
boundary → Unchanged: prior episode's own record → Attribution: prior
episode, clearly dated → Source: prior episode's note → Review: rejected
unless current-episode evidence exists → Understanding: reviewer never
mistakes historical data for a current-episode finding.

**55. Patient disputes a Patient Story statement**
Given a patient or authorized representative disputes a published statement
→ When the dispute is raised → Then it routes through the applicable
governance process (Section 28.6 — pending confirmation) rather than being
silently edited or deleted by any single user → Unchanged: original
statement remains reproducible → Attribution: dispute is itself documented
and attributed → Source: the disputed contribution's original source →
Review: authorized reviewer/HIM process → Understanding: reviewer sees both
the original statement and the fact that it was disputed, with resolution
handled by the correct authority — this exact process remains an open
governance question until Section 28.6 is resolved.

---

## 27. COMPLIANCE CLASSIFICATION

**Federal requirements (mandatory, within their scope):**
- **42 CFR 418.54** — comprehensive assessment addresses physical,
  psychosocial, emotional, and spiritual needs.
- **42 CFR 418.56** — the interdisciplinary group coordinates patient- and
  family-specific care.
- **42 CFR 418.100** — hospice care optimizes comfort and dignity,
  consistent with patient and family needs and goals, with patient
  needs/goals as priority.
- **42 CFR 418.104** — the clinical record contains past and current
  findings and requires clear, complete, authenticated, dated entries.

Patient Story is **not** a federally prescribed form.

**SNS product policy (not a federal requirement):** Patient Story, the
Patient Identity model, IDG chapters, AI contribution proposals, the
Meaning and Goals lifecycle, the 60-second orientation target,
story-worthiness rules, the episode/readmission model, the Final Chapter
definition, scope-appropriate review, contribution-disposition categories,
and the exact layout/interaction design are all SNS product decisions, not
regulatory mandates.

---

## 28. RESOLVED PRODUCT DECISIONS AND OPEN GOVERNANCE QUESTIONS

### 28.1 Family-Versus-Family Conflict

A family-versus-family conflict may be marked appropriately addressed only
when the responsible workflow documents one of the following outcomes
(product meanings only, not authorized database states):

- CLARIFIED_BY_PATIENT
- CLARIFIED_BY_AUTHORIZED_REPRESENTATIVE
- VERIFIED_BY_AUTHORITATIVE_DOCUMENT
- RECONCILED
- CONTINUED_DISAGREEMENT
- NO_LONGER_RELEVANT
- UNABLE_TO_VERIFY

**Responsible workflow by subject:**
- Family or caregiver relationship conflict → social work, MFT,
  mental-health workflow, IDG when care planning is affected
- Spiritual or meaning-related conflict → spiritual-care workflow, IDG when
  care planning is affected
- Clinical treatment conflict → physician, authorized prescriber,
  responsible clinical workflow
- Legal authority, representative, surrogate, or advance-directive conflict
  → authoritative legal-authority or advance-care-planning workflow
- Plan-of-care impact → IDG and plan-of-care workflow

Patient Story displays: responsible workflow, responsible discipline,
current status, source evidence, documented outcome. **Patient Story does
not close the conflict merely because a reviewer read it.**

### 28.2 Scope-Appropriate Review

No discipline has universal approval authority over the entire Patient
Story.

- **Nursing** may review: nursing observations, symptom changes, functional
  changes, ADL changes, safety findings, nutrition findings, caregiver
  observations, nursing interventions and response.
- **Social work, MFT, or mental-health roles** may review: psychosocial
  findings, caregiver burden, family dynamics, coping, resource barriers,
  placement concerns, support-system changes.
- **Spiritual care** may review: spiritual concerns, existential concerns,
  meaning, ritual, unfinished business, sources of comfort, spiritual
  goals.
- **Physician or Medical Director** review is required for:
  physician-level disease-trajectory interpretation, prognosis-related
  interpretation, eligibility-related clinical interpretation, treatment
  conclusions, physician-authored findings.
- **Hospice aides** may contribute direct observations within aide scope.
  Aide observations implying diagnosis, prognosis, or clinical
  interpretation require review by the appropriate licensed discipline.
- **Volunteers** may contribute: direct patient statements, patient
  interests, quality-of-life goals, engagement observations within
  volunteer scope. Volunteers may not originate: diagnoses, prognosis
  conclusions, clinical symptom interpretations, eligibility conclusions.
- **IDG** may approve: interdisciplinary synthesis, chapter summary, team
  priorities, unresolved issues, Next-Period Focus. IDG approval does not
  remove the original discipline attribution.

Patient Identity may use a streamlined review workflow, but every published
statement remains sourced, attributed, reviewed, dated, and auditable.

### 28.3 Introduction Amendments

The Introduction may be amended after the first chapter closes only for:
factual correction; corrected attribution; missing historical referral
information; missing historical admission information; newly available
source material that genuinely describes the original admission starting
point.

Later clinical developments do not rewrite the Introduction. Later changes
belong in the applicable chapter. Later goals belong in the current Meaning
and Goals thread and the applicable chapter. Later caregiver circumstances
belong in the applicable chapter.

Every Introduction amendment must preserve: prior wording; amended wording;
reason for amendment; source; author or reviewer; date and time;
attribution; amendment history.

The Introduction must not: silently regenerate; be rewritten to make later
events appear predictable; backdate later findings into admission context;
become certification or eligibility prose.

### 28.4 Next-Period Focus

Next-Period Focus is an IDG workflow artifact displayed in Patient Story —
it is not an ordinary Story Contribution. It may display: unresolved
issues, monitoring priorities, assigned discipline follow-up, caregiver
risks, pending assessments, goals requiring review, recertification
preparation, documented anticipated transitions, unresolved conflicts
requiring follow-up.

At the next IDG: addressed items may be marked addressed; unresolved items
carry forward; changed priorities require a documented update; deferred
items remain visible; items may not silently disappear. Supporting clinical
facts remain separate, source-linked Story Contributions.

Patient Story does not independently: assign staff; enter orders; modify
the plan of care; change visit frequency; authorize interventions; change
certification status.

### 28.5 Transfer Handoff

A transfer closes the sending hospice provider's Patient Story for that
episode. The sending hospice's Final Chapter remains part of the sending
provider's read-only historical clinical record. Patient Story is not
automatically transmitted as the transfer record.

When an authorized transfer, release-of-information, interoperability, or
health-information-exchange workflow permits it, selected source-linked
information may accompany the authoritative transfer materials.

Any transfer summary or handoff must: use the authorized transfer workflow;
identify the sending hospice; identify the receiving hospice when
documented; preserve source attribution; include only authorized
information; use the documented transfer effective date; include
unresolved care needs when authorized and relevant; exclude unsupported AI
synthesis; exclude hidden source information inaccessible to the receiving
party; avoid implying that the receiving hospice continues the same Patient
Story.

The receiving hospice maintains its own episode record under its
authorized record system. The receiving hospice's later documentation does
not become part of the sending provider's Patient Story. A transfer does
not: continue chapter numbering; merge records; merge stories; make the
receiving hospice a contributor to the closed sending-provider story.

### 28.6 Open Governance Questions (privacy, HIM, legal, compliance)

Before architecture authorization, privacy, HIM, compliance, and legal
review must determine:

- Whether Patient Story is included in patient-access requests.
- Whether Patient Story appears in the designated record set (see Section
  2.1).
- How a patient or authorized representative disputes a statement
  (see Scenario 55, Section 26.2).
- How attribution disputes are handled.
- How amendments are requested and documented.
- Whether any content may be restricted under applicable policy or law.
- How sensitive information about another person is handled.
- How disclosures and record exports represent AI proposals versus
  authenticated contributions.
- How record retention applies to historical Patient Story versions.

**These questions must not be silently decided by engineering.** They
remain open pending formal privacy/HIM/legal review — this is the only
category of question this document leaves unresolved, by design.

---

## 29. APPROVAL STATUS

**Document control:**
- Patient Story v1 — SUPERSEDED
- Patient Story v2 — SUPERSEDED BY RECONCILIATION
- Patient Story v2.1 — SUPERSEDED, folded into V3
- Patient Story v2.2 — SUPERSEDED, folded into V3
- Patient Story v2.3 — SUPERSEDED, folded into V3
- Patient Story v2.4 — SUPERSEDED, folded into V3
- **Patient Story V3 (this document, this revision) — CONSOLIDATED
  AUTHORITATIVE PRODUCT DEFINITION**

No V3.1 or further addendum will be issued — all future corrections revise
this document directly.

```
PATIENT STORY V3

STATUS:
CONSOLIDATED WORKING PRODUCT DEFINITION

PRODUCT DEFINITION:
READY FOR PRODUCT VALIDATION AFTER THE REVISIONS IN THIS DOCUMENT

REGULATORY BOUNDARIES:
DOCUMENTED

PRIVACY / HIM / LEGAL QUESTIONS:
PENDING CONFIRMATION WHERE IDENTIFIED (Section 2.1, Section 28.6)

PRODUCT QUESTIONS:
RESOLVED EXCEPT QUESTIONS DISCOVERED DURING PRODUCT VALIDATION AND FORMAL
PRIVACY / HIM / LEGAL REVIEW

ARCHITECTURE AUTHORIZED:      NO
CODE AUTHORIZED:              NO
SCHEMA AUTHORIZED:            NO
MIGRATIONS AUTHORIZED:        NO
APIs AUTHORIZED:              NO
ROUTES AUTHORIZED:            NO
IMPLEMENTATION READY:         NO
```

---

## 30. PRODUCT VALIDATION PLAN

Patient Story must be validated as a product concept before architecture is
authorized. Use de-identified or synthetic cases unless authorized
historical-record testing and all required safeguards are confirmed.

### 30.1 Representative validators
- [ ] Admitting RN
- [ ] Case manager RN
- [ ] Physician or Medical Director
- [ ] Social worker, MFT, or mental-health role
- [ ] Spiritual-care role
- [ ] Hospice aide representative
- [ ] Volunteer-program representative
- [ ] IDG coordinator
- [ ] Quality or compliance reviewer
- [ ] Privacy or HIM reviewer
- [ ] Authorized auditor or surveyor proxy

### 30.2 Patient Identity
- [ ] Users distinguish Patient Identity from demographics.
- [ ] Users understand that Patient Identity is stable but not static.
- [ ] Users identify attribution immediately.
- [ ] Users distinguish important relationships from legal authority.
- [ ] Users understand that prior-episode identity is proposed, not
      inherited.

### 30.3 Introduction
- [ ] Users identify why hospice was considered.
- [ ] Users identify why hospice was considered at that time.
- [ ] Users identify the admission baseline.
- [ ] Users distinguish patient statements, family reports, clinician
      observations, and source documents.
- [ ] Users understand that later developments do not rewrite the
      Introduction.

### 30.4 Chapters and IDG
- [ ] IDG users identify what changed since the previous review.
- [ ] IDG users identify hospice response.
- [ ] IDG users identify unresolved issues.
- [ ] IDG users identify current patient and family priorities.
- [ ] Users understand milestones remain inside chapters.
- [ ] Users understand recertification is a cross-chapter lens.
- [ ] Routine documentation does not create false progression.
- [ ] Meaningful stability can be represented.

### 30.5 Source trust
- [ ] Users open the exact source and version.
- [ ] Users see source author and date.
- [ ] Users see supporting context.
- [ ] Users understand that AI proposed but did not publish the content.
- [ ] Users identify the human reviewer.
- [ ] Users recognize duplicate, corroborating, distinct perspectives, and
      conflict (Section 18.6).
- [ ] Users do not mistake Patient Story for the authoritative source note.

### 30.6 Voice
- [ ] Raw audio cannot publish.
- [ ] An unreviewed transcript cannot publish.
- [ ] Uncertain speaker attribution blocks publication.
- [ ] Patient, family, representative, and clinician speech remain
      distinct.
- [ ] Background conversation is excluded.
- [ ] Clinician questions are not attributed to the patient.
- [ ] Transcript correction precedes contribution analysis.

### 30.7 Conflicts
- [ ] Conflicts display side by side.
- [ ] Users identify the responsible workflow.
- [ ] Users identify the documented outcome.
- [ ] Patient Story does not appear to adjudicate.

### 30.8 Goals
- [ ] Current and historical goals remain distinguishable.
- [ ] Revised goals preserve prior goals.
- [ ] Fulfilled goals identify sources.
- [ ] Actionable goals identify a follow-up owner and disposition (18.2).
- [ ] Patient Story does not independently authorize clinical action.

### 30.9 Episodes
- [ ] Readmission creates a new story.
- [ ] Chapter numbering resets.
- [ ] Prior stories remain read-only.
- [ ] Prior identity does not automatically carry forward.
- [ ] Prior clinical findings remain historical (Section 4C).
- [ ] Closed episodes remain visible if the Final Chapter is pending.

### 30.10 Final Chapter
- [ ] Closure type matches the authoritative record.
- [ ] Closure date matches the authoritative record.
- [ ] Final-period summary is source-grounded.
- [ ] Unresolved issues remain visible.
- [ ] Last-known Meaning and Goals states remain visible.
- [ ] Death content does not infer cause or circumstances.
- [ ] Discharge content does not speculate about readmission.
- [ ] Revocation wording remains neutral.
- [ ] Transfer content does not merge records.
- [ ] Corrections remain visible and additive.
- [ ] Bereavement content stays within its own boundary (22.3.1).

### 30.11 Auditor and reviewer
- [ ] Reviewer follows progression across chapters.
- [ ] Reviewer compares baseline and later findings.
- [ ] Reviewer identifies the source behind each claim.
- [ ] Reviewer identifies documented hospice response.
- [ ] Reviewer distinguishes Patient Story from certification, physician
      narrative, plan of care, orders, legal authority, and source notes.
- [ ] Patient Story reduces navigation burden without replacing source
      review.

### 30.12 Usability
- [ ] IDG users orient to the patient in under 60 seconds.
- [ ] New team members identify who the patient is and what matters in
      under 60 seconds.
- [ ] Patient Story remains readable.
- [ ] Patient Story does not become a note dump.
- [ ] Users distinguish Timeline from Patient Story.
- [ ] Users understand that Patient Story does not determine eligibility.

### 30.13 Accessibility
- [ ] Keyboard-only use is possible in the prototype.
- [ ] Focus order is understandable.
- [ ] Status is not conveyed by color alone.
- [ ] Attribution and source links have accessible labels.
- [ ] Conflict and uncertainty remain understandable without visual
      styling.

---

*End of Patient Story Product Definition V3.*
