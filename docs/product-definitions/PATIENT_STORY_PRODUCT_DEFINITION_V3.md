# PATIENT STORY
# PRODUCT DEFINITION V3
## CONSOLIDATED AUTHORITATIVE DOCUMENT

*Supersedes and fully incorporates V1, V2, V2.1, V2.2, V2.3, and V2.4. This is
the single working product definition. No further version-numbered addenda
will be issued — future corrections revise this document directly.*

*Product-definition mode only. No code, schema, migrations, APIs, routes,
services, UI implementation, or state machines are authorized by this
document.*

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

---

## 3. PRIMARY AND SECONDARY USERS

**Primary:** IDG members, admitting/primary RN and other direct-care
clinicians, social work, chaplaincy, Medical Director/attending.

**Secondary:** Auditors and surveyors, new team members onboarding to an
existing patient, quality/compliance reviewers.

---

## 4. CORE DEFINITIONS

- **Patient Identity** — durable, person-centered context describing who the
  patient is: relationships, values, culture, fears, priorities. Not
  demographics. Not chapter-bound. Evolves over time rather than being fixed
  at a point in time. (Term "Patient Identity Snapshot" is retired — see
  Section 4B.)
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

### 4B. Terminology Correction: "Patient Identity Snapshot" → "Patient Identity"

The term "Snapshot" is retired everywhere in this document and all prior
versions. It implied a fixed point-in-time capture, which conflicts with the
approved model that Patient Identity evolves (Section 5).

### 4C. Episode References (prior episodes)

A new Patient Story may reference prior hospice episodes for historical
context:

> **Previous Hospice Episode** — Admission: 01/12/2026 · Discharge:
> 06/18/2026 · Disposition: Discharged Alive

The previous episode is viewable but **strictly read-only** and is not
incorporated into the new story automatically.

A closed episode may appear as a read-only reference as soon as its closure
record exists, even if its Final Chapter narrative is not yet complete
(see Section 22.7 for the exact rule — this replaces the earlier, too-rigid
"no reference until Final Chapter exists" position).

**Identity reuse across episodes:** Patient Identity elements (preferred
name, important relationships, cultural/spiritual preferences, sources of
meaning, good-death preferences, important goals) may be **proposed** for
reuse from a prior episode. Nothing is copied forward automatically — every
proposed item requires re-review and re-confirmation in the new episode,
since caregivers, priorities, goals, living arrangements, legal
representatives, or cultural/spiritual needs may have changed since the
prior episode closed.

**Net rule: Identity is reusable. Identity is not inherited.**

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
one. See Section 9 for exactly which discipline may review which kind of
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

**Amendment rule (resolves former Section 28 Question 3):** the Introduction
may be amended after the first chapter closes **only** for:
- factual correction
- missing historical admission context
- corrected attribution
- newly available source material that genuinely describes the admission
  starting point

Later clinical developments do not rewrite the Introduction — later clinical
changes belong in the applicable chapter, and later goals belong in the
current Meaning and Goals thread and applicable chapter.

Every Introduction amendment must preserve: prior wording, amended wording,
reason, author, date, source, and attribution. The Introduction must never
be rewritten to make later events appear predictable, and it never becomes
certification or eligibility prose.

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

---

## 9. DISCIPLINE CONTRIBUTION AND SCOPE-APPROPRIATE REVIEW RULES

*(Expanded — resolves former Section 28 Question 2.)*

Each discipline may contribute story material grounded in its own documented
encounters within the current episode. A contribution becomes part of
Patient Story only when source-linked, correctly attributed, and reviewed by
a reviewer with scope-appropriate authority. Routine, unchanged
documentation does not itself become a new contribution.

**No discipline has universal approval authority over the entire Patient
Story.** Review authority is scoped:

- **Nursing** reviews nursing observations, symptoms, function, safety, and
  nursing response.
- **Social work, MFT, or mental-health roles** review psychosocial, family,
  caregiver, coping, resource, and placement contributions.
- **Spiritual care** reviews spiritual, existential, meaning, ritual, and
  spiritual-goal contributions.
- **Physicians or the Medical Director** review physician-level disease
  trajectory, prognosis context, and treatment interpretation.
- **Hospice aides** contribute observations within aide scope. Unsupported
  clinical conclusions require review by the appropriate licensed
  discipline.
- **Volunteers** contribute direct observations, engagement, and
  patient-stated quality-of-life interests within volunteer scope.
  Volunteers do not originate diagnostic or prognostic conclusions.
- **IDG** reviews interdisciplinary chapter synthesis without erasing
  originating discipline attribution.

Patient Identity may use a streamlined review process, but every statement
remains sourced, attributable, reviewed, and auditable regardless of which
discipline's scope it falls into.

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
next review point, whether it requires action through another workflow,
whether it is actionable/aspirational/informational, and — if fulfilled or
revised — what source confirms it. Not every goal becomes an order or
plan-of-care intervention, but no actionable goal is left without a visible
follow-up owner, and Patient Story never independently authorizes the
response.

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

## 16. CONFLICT REPRESENTATION

*(Corrected — Patient Story is not an actor.)*

Patient Story displays conflicting perspectives side by side with clear
attribution and source links.

Patient Story **records** clarification, verification, reconciliation, or
continued disagreement performed through the responsible authorized
workflow. Patient Story **never independently determines** which account is
correct.

Conflicts involving legal authority, code status, advance directives,
treatment direction, orders, or disposition must link to their authoritative
record and workflow.

Patient Story may display:
- responsible follow-up discipline
- current conflict status
- date last reviewed
- documented outcome
- continued disagreement
- linked authoritative record

**Patient Story may not adjudicate.**

**Family-versus-family conflict closure rule** (resolves former Section 28
Question 1): a family-versus-family conflict may be considered appropriately
addressed when the responsible workflow documents one of these outcomes:

- clarified directly by the patient
- clarified by an authorized representative within the representative's
  authority
- verified through an authoritative document
- reconciled through an authorized clinical or interdisciplinary process
- continued disagreement documented with an operational care plan
- no longer relevant
- unable to verify

Possible responsible owners: social work/mental-health workflow (family-
system conflict), spiritual-care workflow (meaning/spiritual conflict),
physician/responsible clinician (treatment conflict), advance-care-planning/
legal-authority workflow (representative, directive, or surrogate issues),
IDG (interdisciplinary care-plan impact).

Patient Story records the owner and documented outcome. Patient Story does
not resolve the conflict.

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

---

## 18. CLINICIAN REVIEW

Every contribution requires human review, by a reviewer with scope-
appropriate authority (Section 9), before publication. Reviewer sees:
proposed contribution, category, exact source excerpt, source note/author/
date, attribution, related existing content, possible conflict/duplicate.
Reviewer actions: Accept, Edit and Accept, Reject, Defer, Mark Duplicate,
Mark Conflict, Change Attribution, Change Category. Editing the contribution
never edits the source note; rejecting never removes source information.

---

## 19. IDG WORKFLOW

IDG uses Patient Story as pre-meeting orientation, not a replacement for the
record (Section 25's 60-second usability target). See Section 21A for the
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
them.

### 21A. Next-Period Focus

*(Resolves former Section 28 Question 4.)*

Next-Period Focus is an **IDG workflow artifact displayed in Patient
Story** — it is not an ordinary Story Contribution. It may contain:
unresolved issues, monitoring priorities, assigned discipline follow-up,
caregiver risks, pending assessments, goals due for review, recertification
preparation, and anticipated transitions supported by current
documentation.

At the next IDG: addressed items are marked addressed, unresolved items
carry forward, changed priorities require a documented update, and no item
silently disappears.

Patient Story **displays** Next-Period Focus. Patient Story does not assign
staff, enter orders, or change the plan of care.

---

## 22. FINAL CHAPTER PRODUCT DEFINITION

*(Strengthened per owner correction.)* The Final Chapter closes the hospice
journey **without inventing meaning, eligibility conclusions, cause of
death, or future outcomes.**

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
receiving hospice.

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

### 22.5 Transfer handoff rule

*(Resolves former Section 28 Question 5.)* A transfer closes the current
hospice provider's Patient Story. The current provider's Final Chapter
remains part of the current provider's read-only historical record. Patient
Story itself is **not automatically transmitted** to the receiving hospice.
If SNS supports an authorized transfer packet or health-information-exchange
workflow, selected source-linked information may be included through that
workflow.

Any transfer handoff must: use the authoritative transfer workflow;
identify the sending hospice; identify the receiving hospice when
documented; include only authorized information; preserve source
attribution; exclude unsupported AI synthesis; avoid implying the receiving
hospice is continuing the same Patient Story; avoid assumptions about the
receiving hospice's software system.

The receiving hospice creates its own episode record and story under its
own authority. Standard product wording: "the receiving hospice maintains
its own episode record under its authorized record system" (not "a separate
system," unless that specific fact is confirmed for a given transfer).

### 22.6 Readmission interaction with prior Final Chapters

An authoritative closed episode may appear as a read-only prior-episode
reference **as soon as its closure record exists** — a Final Chapter does
not need to be fully complete first. If the Final Chapter narrative has not
been completed, the reference displays: **"Episode closed. Final Chapter
pending review."** The incomplete Final Chapter becomes a visible quality/
workflow issue, but the prior episode remains read-only, no information
copies automatically, the new admission still creates a new Patient Story,
and completing the prior Final Chapter does not alter the new story. A
valid historical episode is never hidden merely because its narrative
review is pending.

### 22.7 Acceptance criteria

- [ ] Every closed episode has exactly one Final Chapter.
- [ ] Closure type and date match the authoritative discharge/death/
      revocation/transfer record.
- [ ] Unresolved issues at closure remain visible, not silently dropped.
- [ ] Last-known Meaning and Goals state is preserved at closure.
- [ ] No Final Chapter speculates about outcomes beyond what is documented.
- [ ] A closed episode's Final Chapter is never edited to reopen the
      episode; corrections are additive/visible, not silent replacements.
- [ ] A closed episode with a closure record but pending Final Chapter
      narrative still appears as a read-only reference, clearly labeled
      "Final Chapter pending review."
- [ ] Transfer content never merges the receiving hospice's later
      documentation or assumes its software system.

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
disclosure, or record-retention policies.

---

## 24. AUTHORITATIVE WORKFLOW BOUNDARIES

| Domain | Authoritative for | Patient Story's role |
|---|---|---|
| Plan of Care | Interventions | Informs, never substitutes |
| Orders | Authorized clinical actions | Never authorizes or implies an order |
| Advance-Care Planning / legal authority | Code status, representative/surrogate designation | Cross-references only |
| Certification / eligibility | Regulatory eligibility determination, physician narrative | Not a certification, eligibility determination, or independent basis for eligibility; may provide source-linked orientation to documented findings only |
| Conflict resolution (Section 16) | Clarification, verification, reconciliation performed by the responsible clinical/legal/IDG workflow | Displays and records the outcome; never adjudicates |
| Transfer handoff (Section 22.5) | Authorized transfer/HIE workflow | Not automatically transmitted; contributes only through that workflow |

---

## 25. ACCEPTANCE CRITERIA

**Product identity:** Patient Story preserves both Identity and Journey;
Identity is not reduced to demographics; not RNICA-owned; remains distinct
from Timeline, Face Sheet, notes, POC, certification; represents exactly one
hospice episode.

**Episode boundary:** readmission always creates a new story; chapter
numbering never continues across episodes; prior episodes are read-only
references (available even with a pending Final Chapter, per 22.6); Identity
reuse is always proposed, never automatic.

**Governance:** no unsourced/anonymous Identity edits; every Identity
statement carries attribution + accountability metadata; updates are
additive; legal authority never inferred by Patient Story; review authority
is scope-appropriate per discipline (Section 9).

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
family conflict closure follows the seven documented outcomes in Section 16.

**Goals lifecycle:** all 8 statuses representable; superseded goals
preserved; every current goal answers the Section 11 responsibility
questions; no independent authorization of clinical action.

**Privacy:** no care-irrelevant/stigmatizing/gossip content; neutral
wording; minimization stated as a product rule, not a substitute for org
policy.

**Introduction:** explains why hospice was considered, referral/admission
context, baseline, initial caregiver/living situation; preserves patient/
family perspective distinctly; links to sources; clinician-reviewed and
approved; not silently regenerated; amendments after first-chapter-close are
limited to the four permitted reasons in Section 6 and always preserve
prior wording/reason/author/date/source/attribution; never becomes
certification prose.

**Chapters:** each completed IDG period (within an episode) representable as
a chapter; milestones inside correct chapter; no false progression from
routine notes; meaningful stability representable; each material change has
a documented source and (if present) hospice response; unresolved issues
carry forward via Next-Period Focus (21A); prior chapters never silently
rewritten; recertification reviews across chapters within one episode only;
Final Chapter reflects documented closure per Section 22.

**Source & review:** every published contribution links to an authenticated
source; View Source opens the exact record/version; source date/author
visible; excerpt preserves context; reviewing clinician recorded; rejected/
deferred proposals never appear as published facts; duplicates don't create
duplicate statements; conflicts remain visible; AI cannot publish/amend/
lock/delete content.

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

1. Initial story from H&P and referral
2. Duplicate administrative document
3. Authenticated voice note
4. Unauthenticated voice draft
5. Routine stable visit
6. PPS decline
7. Functional decline
8. Caregiver change
9. Important patient wish
10. Goal changes over time (new proposal recorded as REVISED/SUPERSEDED;
    prior stated goal remains visible, attributed, dated)
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
30. Correction to a Final Chapter after closure (must remain additive/
    visible, never a silent rewrite)
31. Death with documented final goals
32. Death with no documented final-period assessment
33. Discharge for extended prognosis
34. Discharge after moving outside the service area
35. Discharge for cause with sensitive supporting documentation
36. Revocation with no documented reason
37. Revocation with a patient-stated reason
38. Transfer to another hospice
39. Other or unclear closure requiring review
40. Episode closed but Final Chapter pending
41. New admission begins while prior Final Chapter is pending
42. Final Chapter correction after a later source correction
43. Goal fulfilled shortly before closure
44. Unresolved family conflict at closure
45. Transfer handoff produced through an authorized workflow

Each scenario (1–45) is validated against the following structure once
product validation begins (Section 30): **Given / When / Then / Content
that must remain unchanged / Attribution requirement / Source requirement /
Review requirement / Expected user understanding.** This structure is
defined as a validation method here; individual scenario write-ups are
produced during the validation sessions described in Section 30, not
invented in advance of real user testing.

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
definition, scope-appropriate review, and the exact layout/interaction
design are all SNS product decisions, not regulatory mandates.

---

## 28. OPEN QUESTIONS

All five previously open product questions have been resolved directly in
this revision (Sections 16, 9, 6, 21A, and 22.5 respectively). No
unresolved product questions remain as of this revision.

Per document control policy (Section 29), further questions may only be
added here if discovered during real product validation (Section 30) —
they are not to be manufactured in advance of that validation.

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
PRODUCT DEFINITION:      READY FOR PRODUCT VALIDATION
ARCHITECTURE AUTHORIZED: NO
CODE AUTHORIZED:         NO
SCHEMA AUTHORIZED:       NO
MIGRATIONS AUTHORIZED:   NO
IMPLEMENTATION-READY:    NO
```

---

## 30. PRODUCT VALIDATION PLAN

Patient Story must be validated as a product concept before architecture is
authorized. Use de-identified or synthetic scenarios unless authorized
historical-data testing safeguards are confirmed.

### 30.1 Representative roles to validate with
- [ ] Admitting RN
- [ ] Case manager RN
- [ ] Social worker, MFT, or mental-health role
- [ ] Spiritual-care role
- [ ] Physician or Medical Director
- [ ] Hospice aide representative
- [ ] Volunteer-program representative
- [ ] IDG coordinator
- [ ] Quality or compliance reviewer
- [ ] Authorized chart reviewer or auditor proxy

### 30.2 Patient Identity
- [ ] Users distinguish Patient Identity from demographics.
- [ ] Users understand that Patient Identity is stable but not static.
- [ ] Users understand attribution immediately.
- [ ] Users can distinguish people important to the patient from legal
      decision-makers.
- [ ] Users understand that prior-episode identity is proposed, not
      inherited.

### 30.3 Introduction
- [ ] Users can identify why hospice was considered.
- [ ] Users can identify why hospice was considered at that time.
- [ ] Users can identify the admission baseline.
- [ ] Users can distinguish patient statements, family reports, clinician
      observations, and source documents.
- [ ] Users recognize that Introduction amendments preserve history.

### 30.4 IDG and chapters
- [ ] IDG users can identify what changed since the previous IDG.
- [ ] IDG users can identify what hospice did in response.
- [ ] IDG users can identify unresolved issues.
- [ ] IDG users can identify current Meaning and Goals.
- [ ] IDG users understand milestones are within chapters.
- [ ] IDG users understand recertification is a cross-chapter lens.
- [ ] Routine stable notes do not produce false progression.
- [ ] Clinically meaningful stability can be represented accurately.

### 30.5 Source and trust
- [ ] Users can open the exact supporting source.
- [ ] Users can see author and source date.
- [ ] Users can see the supporting excerpt in context.
- [ ] Users understand AI proposed the contribution but did not publish it.
- [ ] Users can identify who reviewed the contribution.
- [ ] Users can identify a duplicate or conflict.
- [ ] Users do not mistake Patient Story for the authoritative note.

### 30.6 Voice documentation
- [ ] Raw audio cannot publish content.
- [ ] Unauthenticated transcripts cannot publish content.
- [ ] Uncertain speakers block publication.
- [ ] Patient, family, representative, and clinician speech remain
      distinct.
- [ ] Background conversation is excluded.
- [ ] Clinician questions are not attributed to the patient.
- [ ] Transcript correction occurs before story analysis.

### 30.7 Conflicts
- [ ] Conflicting perspectives appear side by side.
- [ ] Users can identify the responsible follow-up workflow.
- [ ] Users can identify whether the conflict is clarified, reconciled,
      unresolved, or unable to verify.
- [ ] Patient Story does not appear to adjudicate.

### 30.8 Goals
- [ ] Current and historical goals remain distinguishable.
- [ ] Revised goals do not erase prior goals.
- [ ] Fulfilled goals identify supporting evidence.
- [ ] Actionable goals have a visible follow-up owner.
- [ ] Patient Story does not independently authorize an intervention.

### 30.9 Episodes and readmission
- [ ] A readmission starts a new story.
- [ ] Chapter numbering resets.
- [ ] Prior stories remain read-only.
- [ ] Prior identity is never automatically inherited.
- [ ] Users can review prior episodes without merging them.
- [ ] A closed episode with a pending Final Chapter remains visible and
      clearly labeled.

### 30.10 Final Chapter
- [ ] Closure type matches the authoritative record.
- [ ] Closure date matches the authoritative record.
- [ ] Final-period summary contains only reviewed, source-grounded
      information.
- [ ] Unresolved issues remain visible.
- [ ] Last-known Meaning and Goals state is preserved.
- [ ] Death content does not infer cause or circumstances.
- [ ] Discharge content does not speculate about readmission.
- [ ] Revocation content remains neutral.
- [ ] Transfer content does not merge records or assume the receiving
      system.
- [ ] Corrections remain additive and visible.

### 30.11 Auditor and reviewer
- [ ] Reviewer can follow progression across chapters.
- [ ] Reviewer can compare baseline and later findings.
- [ ] Reviewer can identify underlying sources.
- [ ] Reviewer can identify hospice response.
- [ ] Reviewer can distinguish Patient Story from certification, physician
      narrative, plan of care, orders, and legal records.
- [ ] Patient Story reduces navigation burden without replacing source
      review.

### 30.12 Usability
- [ ] IDG users can orient to the patient in under 60 seconds.
- [ ] New team members can identify who the patient is and what matters in
      under 60 seconds.
- [ ] Patient Story remains readable.
- [ ] Patient Story does not become a note dump.
- [ ] No participant confuses Timeline with Patient Story.
- [ ] No participant believes Patient Story independently determines
      eligibility.

### 30.13 Accessibility
- [ ] Keyboard-only review is possible in the prototype.
- [ ] Focus order is understandable.
- [ ] Status is not communicated by color alone.
- [ ] Attribution and source links have accessible labels.
- [ ] Conflict and uncertainty are understandable without relying on
      visual styling alone.

---

*End of Patient Story Product Definition V3.*
