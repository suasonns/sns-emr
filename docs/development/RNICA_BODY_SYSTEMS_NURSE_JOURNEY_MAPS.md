# RNICA Body Systems — Nurse Journey Maps (Deliverable 4)

**Status:** Design/research artifact only. No UI, control, validation, or field change has been made.
These maps describe an intended nurse sequence for a future focused-workspace implementation; they
are not yet built. Every field named below is cross-checked against the actual field inventory
(`RNICA_BODY_SYSTEMS_FIELD_INVENTORY.md`) — none are invented.

**Format per system:** Starting point → sequence (steps, each naming real fields) → conditional
branches → normal path → abnormal path → device path (if applicable) → treatment-review path →
POC path → completion criteria (marked **pending** where the Requirement Matrix hasn't been
approved) → fields sourced from other modules → fields sent downstream.

---

## 1. Neurological
**Starting point:** Level of Consciousness + Mental Status symptoms/demeanor.
1. Determine current status — `consciousness` (LOC), `symptomsDemeanor`.
2. Assess orientation — `orientation.time/place/person/situation`, `orientation.disoriented`.
3. Assess cognition — `hopeItems.n0500/n0510/n0520` (BIMS), `cognition`, `delirium`, `seizureHistory`.
4. Assess communication & sensory — `communication`, `hearing`, `vision`, `sensoryDeficits`, `sensoryAids`.
5. Assess motor/balance — `motorDeficit` → if Yes: `affectedSide`, `deficitType`; `balance`.
6. Review behavioral/psychiatric history — `psychiatricHistoryType`, `psychiatricHistory`.
7. Assess sleep/rest — `sleepRest.*`.
8. Document notes — `notes`.
9. Add actionable findings to POC.

- **Conditional branch:** `motorDeficit = Yes` → reveal `affectedSide`, `deficitType` (not yet implemented — currently always visible).
- **Normal path:** Alert, oriented ×4, BIMS 13–15, no motor deficit, no psychiatric history → quick pass through steps 1–3, steps 4–7 largely "within normal limits."
- **Abnormal path:** Reduced LOC, disorientation, low BIMS, delirium, or motor deficit present → each should visually escalate (not yet implemented; today all fields render identically regardless of value).
- **Device path:** Sensory aids (glasses/hearing aids) — currently mixed in with clinical status fields (Hearing/Vision radios), not visually separated from a device list.
- **Fields sourced from other modules:** None directly; BIMS values are cross-consumed by Structured Findings.
- **Fields sent downstream:** `hopeItems.n0500/n0510/n0520` → HOPE export; BIMS sum + `cognition` → Structured Findings panel.
- **Completion criteria:** **Pending** — no required-field matrix approved for this system yet.

---

## 2. Cardiovascular
**Starting point:** Chest pain / heart-failure symptom screen (highest-acuity items first).
1. Screen current symptoms — `chestPain.present` (tri-state) → if Yes: `chestPain.type`; `bpSymptoms`.
2. Cardiac exam — `heartSounds`, `pulseQuality`, `jvd` (tri-state).
3. Circulation/perfusion — `pulseSites`, `peripheralCirculation`, `skinColor`, `coolExtremities`.
4. Fluid status — `edema.present` (tri-state) → if Yes: `edema.location`, `edema.severity`.
5. Conditions & devices — `heartFailurePresent` → if Yes: `heartFailureType`; `pacemaker`, `internalDefibrillator`, `centralVenousLine`, `varicoseVeins`, `stasisUlcer`.
6. Review linked NYHA summary (Functional Status owns NYHA; Body Systems displays read-only) — **not yet built**.
7. Document notes — `notes`.
8. Add actionable findings to POC.

- **Conditional branch (not yet implemented):** `chestPain.present = Yes` → `chestPain.type`; `edema.present = Yes` → `edema.location`/`edema.severity`; `heartFailurePresent = Yes` → `heartFailureType`.
- **Normal path:** No chest pain, no edema, no heart failure, regular pulse → steps 1–4 all quick negatives.
- **Abnormal path:** Chest pain, 3+/4+ edema, or heart failure present → these three should visually anchor the "abnormal findings" area (not yet implemented).
- **Device path:** Pacemaker/ICD/CVL — currently flat checkboxes with no grouping separate from clinical findings.
- **Cross-module duplicate risk:** `skinColor` (free text here) vs. Skin's `skinColorFinding` (structured); `edema.*` here vs. Skin's `skinEdema.*` — **unresolved, listed in the inventory**.
- **Fields sent downstream:** `edema.present/severity` → Structured Findings ("Edema documented").
- **Completion criteria:** **Pending.**

---

## 3. Respiratory (Owner-designated pilot system)
**Starting point:** Shortness-of-breath screen (`sobSeverity`, HOPE J2051B / SFV trigger).
1. Determine current respiratory status — `sobSeverity` (SFV-triggering), `exertionLevel`.
2. SFV/HOPE SOB workflow — `shortnessOfBreathScreened`, `screeningDate`, `treatmentInitiated`, `treatmentDate`, `treatmentDeclined`.
3. Respiratory exam — `lungSounds`, `respirations` (pattern), `coughType`, `sputumCharacter`.
4. Oxygen use — `oxygenTherapy.inUse` → if Yes: `oxygenTherapy.type/litersPerMinute/hoursPerDay/deliveryMode/satOnO2`; else `oxygenTherapy.onRoomAir`.
5. Airway support — ventilator/tracheostomy fields (`ventilator.*`) — **currently no explicit "present" boolean; needs one added or an existing field repurposed as the trigger before progressive disclosure can work — flagged as an unresolved decision, not resolved here**.
6. Review active respiratory treatments (read-only summary from Meds/Treatment — not yet built).
7. Document response & exceptions — no dedicated "response" field exists today (owner directive calls for one) — **flagged as a possible new field, explicitly not added under the freeze**.
8. Document notes — `notes`.
9. Add actionable findings to POC.

- **Conditional branch (not yet implemented):** `oxygenTherapy.inUse = Yes` → reveal oxygen detail fields; ventilator/trach fields need a trigger field first (see step 5 flag).
- **Normal path:** SOB = None, no oxygen, no ventilator/trach → steps 1, 3 quick negatives, steps 4–5 collapsed/hidden entirely once progressive disclosure exists.
- **Abnormal path:** SOB Moderate/Severe/At rest, abnormal lung sounds, or oxygen/ventilator in use → should visually anchor the top of the workspace.
- **Device path:** Oxygen delivery type/flow, ventilator settings, tracheostomy type/size.
- **Fields sent downstream:** `sobSeverity` → SFV trigger logic (external to Body Systems, already exists); `oxygenTherapy.inUse` → Structured Findings ("Continuous oxygen therapy in use...").
- **Completion criteria:** **Pending** — per owner directive, Respiratory is the pilot; completion rules should be defined here first, once approved, before any other system.

---

## 4. Infection
**Starting point:** Current active infection status (`currentInfections`).
1. Determine current infection status — `currentInfections`.
2. Infection site/type — same field's option list (Sepsis/UTI/Respiratory tract/IV site/Wound/etc.) — no separate "site" field exists distinct from this checkbox group today.
3. Symptoms/objective findings — `temperature` (**duplicate risk with `vitals.temperature`, unresolved**), `recurrentInfection`.
4. Recent infection history — `historyOfResistantInfections`, `infectionHistory`.
5. Precautions when applicable — `precautions`, `antibioticResistantInfection`.
6. Current antimicrobial treatment — `antibioticUse` (boolean only; no drug/date detail fields exist today).
7. Response to treatment — no dedicated field exists today (flagged, not added).
8. Notes — `notes`.
9. Add actionable findings to POC.

- **Normal path:** No current infection, no antibiotic use, no precautions beyond Standard.
- **Abnormal path:** Active infection or resistant-organism history present.
- **Fields sourced from other modules:** Allergies (`patientAllergies` custom widget) lives in this same section but is logically a separate concern the owner directive says "do not duplicate allergy documentation" against.
- **Fields sent downstream:** `currentInfections` → Structured Findings.
- **Completion criteria:** **Pending.**

---

## 5. Gastrointestinal
**Starting point:** Current GI status via the Constipation auto-assessment (`constipationAutoAssess`, driven by `lastBM`).
1. Current GI status — auto-suggested constipation banner, `nausea`, `vomiting`, `diarrhea`, `constipation` (all SFV-triggering).
2. Appetite/intake — owned by Nutrition; Body Systems should show a linked summary only (not yet built; today GI has no appetite field, which is correct/no duplicate).
3. Nausea & vomiting detail — `vomitingOccurrences24h` (should be conditional on `vomiting ≠ None`).
4. Abdominal exam — `bowelSounds`, `abdomen`, `ascites`, `abdominalGirth`.
5. Bowel pattern — `bowelStatus`, `bowelFrequency`, `stoolCharacter`.
6. Last bowel movement — `lastBM`.
7. Constipation/diarrhea detail — already captured in step 1; `reasonBowelRegimenNotInitiated` when applicable.
8. Dysphagia/aspiration — **not present in GI today**; lives in Nutrition (`swallowingIssues`) — owner directive: "Nausea remains owned by GI... do not duplicate the same symptom in Pain," and separately flags GI/Nutrition swallowing overlap as unresolved.
9. Devices — `feedingTube.present` → if Yes: `feedingTube.type`; `ostomy.present` → if Yes: `ostomy.type` (**overlaps `stoolCharacter`'s Colostomy/Ileostomy options and Nutrition's `artificialFeeding` — unresolved**).
10. Treatment summary — read-only, not yet built.
11. Notes — `notes`.
12. Add actionable findings to POC.

- **Completion criteria:** **Pending.**

---

## 6. Nutrition
**Starting point:** Weight-loss auto-calculation (`weightLossAutoCalc` custom renderer) + current nutritional status.
1. Current nutritional status — `weightLossAutoCalc` summary, `weightLossPastSixMonths`.
2. Oral intake — `dietType`, `fluidIntake`.
3. Appetite — `appetite`.
4. Weight/weight change — anthropometric reference (`nutritionAnthropometricReference` custom).
5. Hydration — `fluidIntake` (shared with step 2; no separate hydration-specific field exists today).
6. Measurements — anthropometric reference custom widget.
7. Dietary requirements — `dietType` (same field as step 2; no separate "requirements" field exists).
8. Feeding assistance — not present as a distinct field today (owner directive names it; flagged, not added).
9. Artificial nutrition — `npoStatus`, `artificialFeeding` (**overlaps GI's feeding-device fields, unresolved**).
10. Functional impact — not present; would link to Functional Status/ADL (owner directive calls for a linked summary, not yet built).
11. Treatment summary — not yet built.
12. Notes — `notes`.
13. Add actionable findings to POC.

- **Completion criteria:** **Pending.**

---

## 7. Endocrine
**Starting point:** Impairment screen (`endocrineImpairment`).
1. Current endocrine status — `endocrineImpairment`.
2. Diabetes present — `diabetes.type` → if ≠ "Not diabetic": reveal `diabetes.dependency`, glucose monitoring, HbA1c, insulin/oral hypoglycemic detail (progressive disclosure not yet implemented).
3. Glucose monitoring — `diabetes.glucoseMonitoring`, `diabetes.lastHbA1c/.lastHbA1cDate`.
4. Glycemic symptoms — `endocrineSymptoms` (Polydipsia/Polyuria overlap here).
5. Endocrine devices — none distinctly modeled (insulin pump, etc. not present as a separate device field today).
6. Disease-specific findings — `thyroid.assessment` → if ≠ Normal: `thyroid.notes`.
7. Treatment summary — `currentEndocrineMeds` (**duplicates `diabetes.insulinType`/`.oralHypoglycemics`, unresolved**).
8. Response — no dedicated field exists today.
9. Notes — `notes`.
10. Add actionable findings to POC.

- **Completion criteria:** **Pending.**

---

## 8. Genitourinary
**Starting point:** Current urinary status (`urinaryStatus`).
1. Current urinary status — `urinaryStatus`.
2. Continence — same field (Continent/Stress/Urge/Functional/Total incontinence options within `urinaryStatus`).
3. Retention — same field ("Retention" option within `urinaryStatus`); no separate retention-detail field exists.
4. Urinary symptoms — `frequency`, `urineCharacteristics`, `urineColor`.
5. Output concerns — `urineOutput`, `twentyFourHourVolume`.
6. Catheter present — `catheter.present` → if Yes: reveal `catheter.type/size/insertionDate/lastChangeDate/condition/urineCharacteristics/irrigation.*/catheterCare` (progressive disclosure not yet implemented; **also overlaps `urinaryStatus = Catheterized`, unresolved**).
7. Renal-related findings — no dedicated renal-disease field exists today (owner directive names oliguria/uremic symptoms/hyperkalemia/pericarditis/hepatorenal/fluid overload as hospice-relevant; none of these are currently modeled anywhere in GU — **flagged as a genuine gap, not fabricated as fields here**).
8. Treatment summary — not yet built.
9. Notes — `notes`.
10. Add actionable findings to POC.

- **Completion criteria:** **Pending.**

---

## 9. Musculoskeletal
**Starting point:** Current status (`weakness`, `gait`).
1. Current musculoskeletal status — `weakness`, `gait`.
2. Strength — `strength`.
3. Range of motion — `romLimitations`.
4. Contractures — `contractures`/`contracturesPresent` (**duplicate pair, unresolved**) → if present: `contracturesLocation`.
5. Structural findings — `musculoskeletalIssues`, `rigidity`/`rigidityPresent` (**duplicate pair, unresolved**), `paralysis` (**overlaps Neurological's motor-deficit fields, unresolved**).
6. Movement-related pain — `painWithMovement`.
7. Assistive devices — `assistiveDevices` (**owner directive: overlaps the separate, protected Falls Assessment module — cross-module duplicate already flagged by the owner**).
8. Functional impact summary — `mobility.ambulatoryStatus/.endurance/.transferAbility`; `balance` (**duplicate field name/definition vs. Neurological's own `balance`, unresolved**).
9. Treatment summary — not yet built.
10. Notes — `fallHistory.fallsLast90Days/.fallInjuries` (**owner directive: Falls Assessment is separately owned; these two fields currently live inside Musculoskeletal in violation of that stated ownership boundary — the single largest structural conflict found in this inventory**), `notes`.
11. Add actionable findings to POC.

- **Completion criteria:** **Pending.**
- **Owner attention required:** `fallHistory.*` and `assistiveDevices` need an explicit ownership decision (keep in Musculoskeletal as a body-system evidence source vs. relocate/link to the protected Falls module) before any Nurse-Miss Prevention or completion logic can be built for this system.

---

## 10. Skin / Wounds
**Starting point:** Body Map + skin integrity overview.
1. Skin integrity overview — Body Map (renders inside the Skin Assessment card), `skinConditionsPresent`, `skinStatus`.
2. Skin characteristics — `skinTurgor`, `skinMoisture` (**overlaps `skinStatus`'s "Dry" option, unresolved**), `skinTemperature`, `skinColorFinding` (**overlaps `skinStatus`'s Cyanotic/Jaundice/Mottled options and CV's free-text `skinColor`, unresolved**), `additionalSkinFindings`.
3. Pressure risk — Braden subscales (`braden.*`) → `pressureInjuryRisk` (**should be derived from the Braden sum rather than independently selected — flagged as a data-integrity risk, not changed**).
4. Wounds — `woundList` custom renderer (structured records: location, type, stage, measurements, drainage).
5. Treatment summary — read-only, sourced from Meds/Treatment or Orders & POC (not yet built; must not duplicate treatment entry per owner directive).
6. Notes — `notes` (not currently present as a distinct field in the Skin config — **gap: no `notes` field exists in the Skin section today**, unlike every other body system).
7. Add actionable findings to POC.

- **Completion criteria:** **Pending.**
- **Gap found:** Skin/Wounds has no free-text Notes field today, unlike all 9 other body systems — flagged for owner decision (add one, consistent with every other system, or confirm it's intentionally out of scope here since wound-level notes exist inside `woundList`).

---

## Cross-System Sequencing Observations (not yet actioned)
- Respiratory, Cardiovascular, GI, and Endocrine all have real progressive-disclosure candidates
  (`oxygenTherapy.inUse`, `edema.present`/`chestPain.present`, `feedingTube.present`/`ostomy.present`,
  `diabetes.type`) that are fully wired in the data model today but **not implemented** in the UI —
  building this is pure additive behavior (show/hide), not a field/path change, and is the most
  direct way to reduce visual density without touching a single existing field.
- Musculoskeletal is the system most in conflict with the owner's own "protect Falls/Safety ownership"
  rule (`fallHistory.*`) — this needs an owner decision before Musculoskeletal's journey map can be
  finalized.
- Skin/Wounds is the only system missing a Notes field.
