# RNICA Nursing Workflow Analysis (Deliverable — Step 3)

**Status:** Research and analysis only. No UI, field, validation, HOPE/SFV mapping, or database
change. This document reframes the already-approved Field Inventory and Nurse Journey Maps around
**nursing cognition** — how an RN actually thinks and scans — rather than data-model grouping.
It exists to answer the owner's redirect: stop comparing fields, start comparing *thought process*
to *current layout*.

**Pilot note:** the owner has recommended Neurological over Respiratory as the pilot system,
citing it as the clearest architecture-failure example in the reviewed screenshots. This document
does not decide the pilot — it provides the nursing-workflow basis needed to make that decision
well, for all 10 systems, so the choice is evidence-based rather than screenshot-driven alone.
Neurological's analysis below is written first and in the most depth for that reason.

**Method:** Every field named below already exists in `RNICA_BODY_SYSTEMS_FIELD_INVENTORY.md`.
No field is invented here. "Should remain collapsed / always visible" are proposed **visual
hierarchy judgments** — analysis, not implementation — flagged for RN validation before any
build.

---

## 1. Neurological

1. **First assessed:** Level of Consciousness (`consciousness`) — a nurse cannot meaningfully
   assess orientation, cognition, or communication until she knows if the patient is arousable at
   all. This is the correct cognitive entry point and should anchor the top of the screen.
2. **Second assessed:** Orientation (`orientation.*`) and general demeanor/symptoms
   (`symptomsDemeanor`) — a nurse naturally follows "is he awake" with "does he know who/where/when
   he is" and "how does he seem" (agitated, anxious, calm) in the same glance.
3. **Most important findings:** LOC change from baseline, new disorientation, BIMS score trend
   (`hopeItems.n0500/n0510/n0520`), new motor deficit (`motorDeficit`), new communication loss —
   these are the findings that most directly signal decline or an acute event.
4. **Contextual findings:** Sensory aids (`sensoryAids`), sleep pattern (`sleepRest.*`),
   psychiatric history (`psychiatricHistoryType`) — clinically relevant but rarely the reason a
   nurse opened this section today; useful background, not the first thing scanned.
5. **Should remain collapsed until needed:** BIMS detail scoring, full communication/hearing/vision
   sub-checklists, sleep-pattern detail — these are real assessments but are secondary to the
   LOC/orientation/motor-deficit headline and currently compete for the same visual weight.
6. **Should always remain visible:** LOC, Orientation, Motor Deficit present/absent — these three
   together tell a nurse in one glance whether this patient has changed neurologically since last
   visit.
7. **Should trigger POC review:** New or worsening motor deficit, new disorientation, BIMS decline,
   new seizure activity (`seizureHistory`).
8. **Should trigger HOPE review:** BIMS (`n0500/n0510/n0520`) is itself a HOPE-scored item — any
   entry here is HOPE-relevant by definition.
9. **Should trigger SFV review:** No field in Neurological is currently SFV-flagged in the
   inventory — confirmed absence, not an omission in this analysis. (This is itself worth a
   clinical question: should a new/worsening motor deficit or acute confusion ever trigger SFV?
   Flagged for RN input, not decided here.)
10. **Should trigger physician notification:** Acute LOC decline, new focal motor deficit, new
    seizure — these represent the kind of acute neurologic change that in most hospice programs
    warrants same-day physician communication regardless of POC/HOPE/SFV status.

---

## 2. Cardiovascular

1. **First assessed:** Chest pain screen (`chestPain.present`) — the single highest-acuity, most
   time-sensitive finding in this system; a nurse checks for it before anything else.
2. **Second assessed:** Heart sounds and pulse quality (`heartSounds`, `pulseQuality`) — the core
   auscultation/palpation exam that follows immediately after ruling out acute chest pain.
3. **Most important findings:** New/worsening chest pain, new/worsening edema
   (`edema.present/severity`), new heart-failure symptoms (`heartFailurePresent`) — these three
   are the classic hospice cardiac-decline triad.
4. **Contextual findings:** Pacemaker/ICD presence, varicose veins, stasis ulcer — relevant history,
   not today's acute picture.
5. **Should remain collapsed until needed:** Device history (pacemaker/ICD/CVL), skin
   color/perfusion detail unless perfusion is actually abnormal.
6. **Should always remain visible:** Chest pain status, edema severity, heart-failure status — the
   three findings a nurse needs to answer "is this patient's heart failure worsening today."
7. **Should trigger POC review:** New/worsening edema, new chest pain, new heart-failure symptoms.
8. **Should trigger HOPE review:** No field here currently carries a HOPE code per the inventory —
   confirmed absence.
9. **Should trigger SFV review:** No field here is currently SFV-flagged — confirmed absence
   (worth an RN question: should worsening edema or new chest pain be SFV-eligible the way
   dyspnea already is in Respiratory? Flagged, not decided).
10. **Should trigger physician notification:** New chest pain, rapidly worsening edema, new
    arrhythmia findings.

---

## 3. Respiratory

1. **First assessed:** Shortness-of-breath severity (`sobSeverity`) — this is both the clinical
   entry point (a nurse asks "how is your breathing" before auscultating) and the HOPE/SFV-gating
   field; it is correctly the highest-priority field in this system today.
2. **Second assessed:** Lung sounds and respiratory pattern (`lungSounds`, `respirations`) — the
   physical exam that follows the subjective symptom report.
3. **Most important findings:** SOB severity (Moderate/Severe/At rest), abnormal lung sounds, active
   oxygen use and whether it is meeting need — the findings that most directly answer "is this
   patient in respiratory distress today."
4. **Contextual findings:** Cough type, sputum character — relevant but secondary to the
   dyspnea/lung-sounds headline.
5. **Should remain collapsed until needed:** Ventilator/tracheostomy detail fields (already flagged
   in Unresolved Decisions as needing a "present" trigger before this can even work); oxygen detail
   fields when the patient is not on oxygen.
6. **Should always remain visible:** SOB severity, lung sounds, oxygen-in-use status — a nurse
   should be able to answer "is this patient short of breath, and if so what are we already doing
   about it" without scrolling.
7. **Should trigger POC review:** SOB severity Moderate/Severe, new abnormal lung sounds, any change
   to oxygen therapy.
8. **Should trigger HOPE review:** `sobSeverity` is HOPE J2051B by definition.
9. **Should trigger SFV review:** `sobSeverity` Moderate/Severe already SFV-required per the
   inventory — this is the one system where the SFV linkage is already fully wired end-to-end and
   should be the model for how other systems eventually get the same treatment.
10. **Should trigger physician notification:** SOB at rest, new hypoxia (low SpO2 on current
    delivery), any ventilator/trach status change.

---

## 4. Infection

1. **First assessed:** Current active infection status (`currentInfections`) — the nurse's first
   question is simply "is there a known active infection right now."
2. **Second assessed:** Temperature and recurrence history (`temperature`, `recurrentInfection`) —
   objective confirmation and pattern context immediately follow.
3. **Most important findings:** New active infection, resistant-organism history
   (`antibioticResistantInfection`), fever — these directly affect precautions and physician
   notification.
4. **Contextual findings:** Historical infection pattern (`infectionHistory`), precaution type when
   no active infection exists.
5. **Should remain collapsed until needed:** Full precaution detail when no infection/resistant
   organism is present.
6. **Should always remain visible:** Current active infection status, fever status, resistant
   organism flag — the three facts that change how everyone else on the team should behave around
   this patient today.
7. **Should trigger POC review:** New active infection, new antibiotic-resistant organism finding.
8. **Should trigger HOPE review:** No field here currently carries a HOPE code — confirmed absence.
9. **Should trigger SFV review:** No field here is currently SFV-flagged — confirmed absence.
10. **Should trigger physician notification:** New active infection, new fever, new resistant
    organism, any sepsis-pattern combination of findings.

---

## 5. Gastrointestinal

1. **First assessed:** Nausea and vomiting screen (`nausea`, `vomiting`) — these are the
   HOPE/SFV-gating, patient-reported symptom entry point, and the most acute/distressing GI
   symptoms a hospice patient experiences.
2. **Second assessed:** Bowel pattern and last BM (`bowelStatus`, `lastBM`, `constipation`,
   `diarrhea`) — immediately follows because opioid-related constipation is the single most common
   GI issue this population faces, and the auto-assessment banner already surfaces it first in the
   data model.
3. **Most important findings:** Active nausea/vomiting, constipation/diarrhea status, abdominal
   distension or new tenderness (`abdomen`, `abdominalGirth`) — these directly drive symptom-
   management POC actions.
4. **Contextual findings:** Bowel sounds character, stool character detail when bowel pattern is
   otherwise normal.
5. **Should remain collapsed until needed:** Ostomy/feeding-tube device detail unless a device is
   actually present; full stool-character checklist when bowel pattern is Regular/Continent.
6. **Should always remain visible:** Nausea/vomiting status, constipation/diarrhea status, last BM
   date — the three facts a nurse checks on every single hospice visit regardless of chief
   complaint.
7. **Should trigger POC review:** New/worsening nausea or vomiting, new constipation/diarrhea,
   abdominal distension.
8. **Should trigger HOPE review:** Nausea (J2051D), Vomiting (J2051E), Diarrhea (J2051F),
   Constipation (J2051G) — four of this system's fields are directly HOPE-coded.
9. **Should trigger SFV review:** The same four symptoms are SFV-gating when Moderate/Severe per
   the inventory — GI is (with Respiratory) one of the two systems where SFV linkage already fully
   exists and should inform how the other 8 systems eventually get treated.
10. **Should trigger physician notification:** Persistent vomiting, suspected bowel obstruction
    pattern (distension + absent bowel sounds + no BM), uncontrolled diarrhea.

---

## 6. Nutrition

1. **First assessed:** Weight-loss auto-calculation (`weightLossAutoCalc`) — this is already
   presented as a computed banner, and is the correct entry point since unintentional weight loss
   is a primary hospice-decline indicator independent of anything else in this system.
2. **Second assessed:** Appetite and oral intake (`appetite`, `dietType`, `fluidIntake`) — the
   nurse's next natural question after "has weight changed" is "is he eating/drinking."
3. **Most important findings:** Significant weight loss, poor appetite, aspiration risk
   (`swallowingIssues`), inadequate hydration — the findings most tied to terminal decline
   trajectory and to safety (aspiration).
4. **Contextual findings:** Oral cavity findings, denture status — relevant to comfort, not
   typically the acute concern.
5. **Should remain collapsed until needed:** Artificial-feeding detail unless a feeding
   device/method is actually in use; full oral-cavity checklist when appetite/intake are otherwise
   adequate.
6. **Should always remain visible:** Weight-loss status, appetite, swallowing/aspiration risk — the
   three facts most predictive of nutritional decline and safety risk.
7. **Should trigger POC review:** New significant weight loss, new dysphagia/aspiration risk, poor
   appetite persisting across visits.
8. **Should trigger HOPE review:** No field here currently carries a HOPE code per the inventory —
   confirmed absence (worth an RN question, since weight loss is clinically HOPE-adjacent even if
   not directly coded today).
9. **Should trigger SFV review:** No field here is currently SFV-flagged — confirmed absence.
10. **Should trigger physician notification:** New aspiration events, rapid unintentional weight
    loss, inability to maintain oral intake.

---

## 7. Endocrine

1. **First assessed:** Endocrine impairment screen (`endocrineImpairment`) — establishes whether
   there is any endocrine involvement at all before going further.
2. **Second assessed:** Diabetes status (`diabetes.type`) — the single most common and most
   actionable endocrine condition in this population; naturally follows the impairment screen.
3. **Most important findings:** Diabetes type/dependency, recent glucose control
   (`diabetes.glucoseMonitoring`, `.lastHbA1c`), thyroid abnormality (`thyroid.assessment`) — these
   drive medication and monitoring decisions.
4. **Contextual findings:** Glycemic symptom checklist (`endocrineSymptoms`) when glucose control is
   already documented as stable.
5. **Should remain collapsed until needed:** All diabetes detail fields (dependency, monitoring
   frequency, HbA1c, insulin/oral agent detail) when the patient is not diabetic — this is the
   clearest, least controversial progressive-disclosure candidate of any system, since
   "Not diabetic" already exists as an explicit option today.
6. **Should always remain visible:** Endocrine impairment status, diabetes type — the two facts that
   determine whether anything else in this system is even relevant to this patient.
7. **Should trigger POC review:** New/worsening glycemic symptoms, HbA1c trending worse, new thyroid
   abnormality.
8. **Should trigger HOPE review:** No field here currently carries a HOPE code — confirmed absence.
9. **Should trigger SFV review:** No field here is currently SFV-flagged — confirmed absence.
10. **Should trigger physician notification:** Hypo/hyperglycemic symptoms, significant HbA1c
    change, new thyroid storm/myxedema-pattern findings.

---

## 8. Genitourinary

1. **First assessed:** Current urinary status (`urinaryStatus`) — establishes continence/retention/
   catheter status in one field before anything downstream is meaningful.
2. **Second assessed:** Urine characteristics and output (`urineCharacteristics`, `urineColor`,
   `urineOutput`) — the objective findings that follow the status screen.
3. **Most important findings:** New retention, new catheter-related complication (blockage, leakage,
   infection signs), significant output change — the findings most likely to need same-visit
   intervention.
4. **Contextual findings:** Catheter care/irrigation detail when the catheter is functioning
   normally.
5. **Should remain collapsed until needed:** Full catheter-detail fields (type, size, insertion
   date, irrigation orders) unless `urinaryStatus` actually indicates catheter use — another clean,
   low-controversy progressive-disclosure candidate.
6. **Should always remain visible:** Urinary status, output/frequency concerns — a nurse should be
   able to answer "is this patient's urinary system currently a problem" at a glance.
7. **Should trigger POC review:** New retention, new incontinence pattern, catheter complication.
8. **Should trigger HOPE review:** No field here currently carries a HOPE code — confirmed absence.
9. **Should trigger SFV review:** No field here is currently SFV-flagged — confirmed absence.
10. **Should trigger physician notification:** Suspected catheter-related infection, acute
    retention, significant hematuria.

---

## 9. Musculoskeletal
*(Flagged in Unresolved Decisions as the system with the most cross-module ownership conflict —
this workflow analysis is written around the fields that clearly belong here, and explicitly
brackets the disputed Falls-owned fields.)*

1. **First assessed:** Current strength/weakness and gait (`weakness`, `gait`) — the functional
   baseline a nurse checks before anything structural.
2. **Second assessed:** Range of motion and structural findings (`romLimitations`,
   `musculoskeletalIssues`) — follows naturally once baseline strength/gait is known.
3. **Most important findings:** New weakness, new gait change, new contracture/rigidity, pain with
   movement (`painWithMovement`) — the findings most tied to functional decline and comfort.
4. **Contextual findings:** Assistive-device inventory when device use is unchanged from baseline.
5. **Should remain collapsed until needed:** Full contracture/rigidity location detail unless
   presence is actually documented; the disputed `fallHistory.*` fields should not be re-displayed
   here at all pending the ownership decision already flagged — duplicating them in the interim
   would only worsen, not reduce, the documentation-safety risk this analysis exists to prevent.
6. **Should always remain visible:** Weakness/gait status, contracture/rigidity presence — the two
   facts most predictive of functional decline trajectory.
7. **Should trigger POC review:** New weakness, new contracture, new significant pain with movement.
8. **Should trigger HOPE review:** No field here currently carries a HOPE code — confirmed absence.
9. **Should trigger SFV review:** No field here is currently SFV-flagged — confirmed absence.
10. **Should trigger physician notification:** Acute new weakness/paralysis (possible neurologic
    event — should also prompt Neurological cross-check), acute severe pain with movement.

---

## 10. Skin / Wounds

1. **First assessed:** Body Map / overall skin integrity overview (`skinConditionsPresent`,
   `skinStatus`) — a nurse's first question is "where are the areas of concern," which the Body Map
   already visually anchors.
2. **Second assessed:** Braden subscale assessment (`braden.*`) — immediately follows because it is
   both a risk-prediction tool and a required structured score, not an optional add-on.
3. **Most important findings:** Any new wound, Braden score entering High Risk, any skin color/
   temperature/moisture finding outside normal — these are the findings most tied to pressure-injury
   prevention, the single highest-stakes documentation category in this system.
4. **Contextual findings:** Skin turgor, additional skin findings (bruising, excoriation) when no
   wound or high Braden risk is present.
5. **Should remain collapsed until needed:** Full wound-detail fields (measurements, drainage,
   staging) when `woundList` is empty; full skin-characteristic checklist when Braden risk is Low
   and no wound exists.
6. **Should always remain visible:** Body Map summary, Braden total score and risk level, wound
   count — the three facts a nurse and the IDG team most need at a glance for pressure-injury
   accountability.
7. **Should trigger POC review:** New wound, Braden score entering Moderate/High risk, any wound
   deterioration.
8. **Should trigger HOPE review:** M1190 (Skin Conditions) is directly HOPE-coded.
9. **Should trigger SFV review:** No field here is currently SFV-flagged — confirmed absence (worth
   an RN question: should a new Stage 3/4 pressure injury be SFV-eligible the way dyspnea already
   is?).
10. **Should trigger physician notification:** New Stage 3/4 or unstageable wound, signs of wound
    infection, rapid Braden score decline.

---

## Cross-System Observations (Nursing-Cognition Level, Not Data-Model Level)

- **Every system analyzed above has the same underlying shape:** one or two "gate" findings that
  determine relevance/urgency (chest pain, SOB, nausea/vomiting, weight loss, diabetes status,
  urinary status, weakness/gait, skin integrity, LOC, current infection), followed by a physical-
  exam layer, followed by device/history detail that is usually irrelevant unless the gate finding
  says otherwise. This is the single most consistent pattern across all 10 systems and is the
  strongest evidence for a **uniform two-tier visual hierarchy** (always-visible gate findings +
  progressively-disclosed detail) rather than 10 different bespoke layouts.
- **Only Respiratory and GI currently have their gate findings wired all the way through to
  HOPE + SFV.** Every other system's "most important findings" (per this analysis) have no HOPE or
  SFV linkage today. This is not necessarily a defect — it may be entirely correct that only
  dyspnea and GI symptoms are HOPE J2051-scored — but it does mean Respiratory and GI are the two
  systems where the nursing-cognition priority and the HOPE/SFV priority are already the same
  thing, which is exactly why the owner's instinct that Respiratory "already works better" is
  correct even though Neurological may still be the right pilot for the *visual hierarchy*
  problem specifically.
- **Neurological is the system with the most simultaneous "gate-tier" findings** (LOC, Orientation,
  Motor Deficit are all arguably equally urgent, not a single clean gate like chest pain or SOB) —
  this is the concrete, nursing-cognition-level explanation for why Neurological reads as the most
  "overwhelming" screen in the owner's screenshots, independent of field count. Cardiovascular and
  GI have one dominant gate finding each; Neurological effectively has three competing for the same
  visual priority. This is the strongest evidence yet, beyond "it has the most fields," for why
  Neurological may be the harder and therefore more valuable pilot to solve first.
