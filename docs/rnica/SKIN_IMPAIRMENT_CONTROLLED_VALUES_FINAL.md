# SNS RNICA Skin Impairment Workspace — Final Controlled Values and UI Behavior

**Status:** APPROVED FOR IMPLEMENTATION  
**Purpose:** Final product specification for the RNICA Skin Impairment Workspace.  
**Applies to:** Admission RN comprehensive assessment only.  
**Implementation rule:** Implement this document exactly. Do not add, remove, rename, or reinterpret options without Product Owner approval.

---

## 1. Final screen model

Use one stable desktop workspace:

1. **One large Patient Wound Map** with numbered markers.
2. **One compact Select Wound dropdown**.
3. **One fixed wound editor** whose position does not move when a different wound is selected.
4. **One assessment-level Wound Assessment Narrative**.
5. **One photo timeline per numbered wound**.

### Keep

- Large Patient Wound Map.
- Front and Back map controls.
- Numbered markers matching wound numbers.
- Compact Select Wound dropdown.
- One fixed wound editor.
- `+ Add Wound` action.

### Remove

- Large Wound Inventory table as the wound selector.
- Secondary or mini body map inside the wound editor.
- Duplicate wound selectors.
- Generic `Skin Open or Intact` control.
- `Status Since Prior` from RNICA.
- `Treat`, `Resolved`, and `COC` admission-status options.
- Repeated narrative fields for every wound.
- Required-photo warnings.
- Technical migration or system notes in the clinician UI.

---

## 2. Select Wound dropdown

### Label

`Select Wound`

### Item format

- `#1 — Coccyx — Pressure Injury — Stage 1`
- `#2 — Location Needed — Pressure Injury — Stage Required`
- `#3 — Left Posterior Calf — Pressure Injury — Stage 2`
- `#4 — Left Forearm — Skin Tear`
- `#5 — Perineum — Moisture-Associated Skin Damage`

### Behavior

- Sort by wound number ascending.
- Keep the selector in one fixed screen position.
- Switching wounds changes values only; the editor must not move or reflow.
- Selecting a dropdown item highlights the matching map marker.
- Selecting a map marker updates the dropdown.
- Wound numbers remain stable and are never reused after deletion.
- At more than 10 wounds, provide type-ahead search within the dropdown.
- The dropdown popover scrolls internally.
- Do not display a second wound inventory selector.

### Incomplete labels

Use concise inline labels:

- `Location Needed`
- `Stage Required`
- `Measurements Required`
- `Reason Not Measured Required`

---

## 3. Add Wound

Use one action:

`+ Add Wound`

The new wound receives the next stable wound number, then opens the fixed editor.

### First required field

`Condition Type`

### Condition Type options

| Display label | Stored value |
|---|---|
| Pressure Injury | `pressure_injury` |
| Skin Tear | `skin_tear` |
| Moisture-Associated Skin Damage | `moisture_associated_skin_damage` |
| Surgical Wound | `surgical_wound` |
| Diabetic Foot Ulcer | `diabetic_foot_ulcer` |
| Venous Ulcer | `venous_ulcer` |
| Arterial Ulcer | `arterial_ulcer` |
| Other Non-Pressure Ulcer | `other_non_pressure_ulcer` |
| Malignant/Fungating Wound | `malignant_fungating_wound` |
| Traumatic Wound | `traumatic_wound` |
| Rash | `rash` |
| Bruising | `bruising` |
| Excoriation | `excoriation` |
| Open Lesion | `open_lesion` |
| Peristomal Skin Condition | `peristomal_skin_condition` |
| Other Skin Condition | `other_skin_condition` |

### Rules

- `Pressure Injury` must be an explicit visible option.
- Selecting `Pressure Injury` shows Stage/Category.
- Non-pressure conditions never show Pressure Injury Stage/Category.
- `Other Skin Condition` requires a short description.
- Do not infer Condition Type from location.
- A heel impairment may be pressure, diabetic, arterial, traumatic, or another condition.

---

## 4. Admission classification

### Label

`Present at Admission`

### Options

- Yes
- No
- Unknown

### Rules

- Required for every active impairment.
- `Unknown` does not require a separate mandatory explanation in RNICA; the assessment narrative may explain uncertainty when clinically important.

### Remove from RNICA

Do not show lifecycle options:

- Treat
- Resolved
- COC
- Status Since Prior
- Improving
- Worsening
- Healing
- Stable/No Significant Change

RNICA establishes the admission baseline. Follow-up status belongs to a future visit workflow.

---

## 5. Anatomical location

Location uses a dialog opened by:

- `Set Location` when blank.
- `Change Location` when already documented.

When the dialog is closed, show one read-only line:

`Location: Left posterior calf`

Do not show a mini body map in the wound editor.

### Body Region options

- Head and Face
- Neck
- Shoulder, Chest, and Torso
- Upper Extremity
- Pelvis and Perineal Region
- Lower Extremity
- Foot and Ankle
- Special Sites

### Side options

- Left
- Right
- Bilateral
- Not Applicable

For midline sites, do not show a Side selector. Store `midline` automatically.

### Surface/Orientation options

Show only anatomically valid values:

- Anterior
- Posterior
- Medial
- Lateral
- Dorsal
- Plantar
- Palmar
- Circumferential
- Not Applicable

### Location rules

- Pressure Injury may use the complete anatomical library.
- Diabetic Foot Ulcer is restricted to foot/ankle sites.
- Venous Ulcer is restricted to lower-leg, calf, ankle, and malleolar sites.
- Arterial Ulcer is restricted to supported lower-extremity distal sites.
- Skin Tear, Surgical Wound, Traumatic Wound, Malignant/Fungating Wound, Rash, Bruising, Excoriation, Open Lesion, and Other Skin Condition may use broad anatomy.
- MASD prioritizes moisture-exposed regions but retains `Other Anatomical Site`.
- Do not silently substitute a nearby location.
- Exact structured location is authoritative.

### Consistent wording

Use `Surface/Orientation` for both primary and extension locations.

---

## 6. Pressure Injury Stage/Category

### Options

- Stage 1
- Stage 2
- Stage 3
- Stage 4
- Unstageable
- Deep Tissue Pressure Injury
- Unable to Determine

### Rules

- Required for every Pressure Injury.
- `Unable to Determine` requires a short reason.
- Do not show `Skin Open or Intact`.
- Do not infer stage from location, measurements, free text, or photographs.

### Measurement requirements

- **Stage 1:** Length, width, and depth are not required.
- **Stage 2:** Length and width required, or one Reason Not Measured. Depth optional.
- **Stage 3:** Length, width, and depth required, or one Reason Not Measured.
- **Stage 4:** Length, width, and depth required, or one Reason Not Measured.
- **Unstageable:** Length and width required, or one Reason Not Measured. Depth not required.
- **Deep Tissue Pressure Injury:** Measurements optional when a discrete area can be measured. Depth not required.
- **Unable to Determine:** Reason required; measurements are not forced.

---

## 7. Device-related Pressure Injury

### Label

`Device-Related Pressure Injury?`

### Options

- No
- Yes

### Behavior

When `Yes`, require:

- Device description
- Anatomical location
- Stage/Category

Device-related status never replaces the anatomical location.

---

## 8. Wound Bed Visible

### Options

- Yes
- No
- Partially
- Unable to Assess

### Visibility

Show for:

- Pressure Injury Stage 2, Stage 3, Stage 4, and Unstageable
- Diabetic Foot Ulcer
- Venous Ulcer
- Arterial Ulcer
- Other Non-Pressure Ulcer
- Malignant/Fungating Wound
- Open or dehisced Surgical Wound
- Open Lesion
- Traumatic Wound when open

Hide for:

- Stage 1
- Deep Tissue Pressure Injury
- Rash
- Bruising
- MASD without an open erosion
- Excoriation without an open lesion

---

## 9. Drainage Amount

### Options

- None
- Scant
- Small
- Moderate
- Large
- Unable to Assess

### Rules

- Single-select.
- Required for open-wound conditions.
- If `None`, set Drainage Character to `Not Applicable` and disable the character control.

---

## 10. Drainage Character

### Options

- Serous
- Sanguineous
- Serosanguineous
- Purulent
- Other
- Not Applicable

### Rules

- Single-select.
- Required when Drainage Amount is not `None` or `Unable to Assess`.
- `Other` requires a short explanation.
- `Not Applicable` is automatically selected when Drainage Amount is `None`.

---

## 11. Odor

### Options

- None
- Present
- Unable to Assess

### Rules

- Single-select.
- No before/after cleansing question.
- No severity follow-up.

---

## 12. Surrounding Skin

### Options

- Intact
- Red/Erythematous
- Macerated
- Fragile
- Warm
- Indurated
- Other

### Rules

- Multi-select.
- `Other` requires a short explanation.
- This control describes skin surrounding the impairment. It is not the removed generic `Skin Open or Intact` field.

---

## 13. Signs of Infection Observed

### Options

- No
- Yes
- Unable to Determine

When `Yes`, show multi-select Observed Findings:

- Redness
- Warmth
- Increased Drainage
- Purulent Drainage
- Odor
- Induration
- Other

`Other` requires a short explanation.

When the answer changes from `Yes` to `No` or `Unable to Determine`, clear Observed Findings after warning the user if findings were entered.

---

## 14. Measurements

### Fields

- Length (cm)
- Width (cm)
- Depth (cm)
- Measurement Date
- Measurement Method
- If Not Measured, Reason

### Measurement Method options

- Ruler/Tape
- Wound Tracing
- Photography With Scale
- Other

`Other` requires a short explanation.

### Rules

- Measurement Method is required when any numeric measurement is entered.
- Do not use zero to mean not measured.
- Do not allow numeric measurements and a Reason Not Measured at the same time.
- Selecting a Reason Not Measured clears and disables applicable numeric fields after confirmation.
- Entering a numeric measurement clears the Reason Not Measured after confirmation.

### If Not Measured, Reason options

- Patient Discomfort
- Patient Declined
- Caregiver Declined
- Dressing/Device Could Not Be Removed
- Unable to Visualize
- Unable to Reposition Safely
- Pain or Symptom Burden
- Safety Concern
- Imminent Death/Active Dying
- Not Clinically Indicated Today
- Diffuse Area Not Discretely Measurable
- Technical Limitation
- Other

`Other` requires a short explanation.

---

## 15. Skin Tear

### Label

`Flap Status`

### Options

- Flap Intact
- Flap Partial Loss
- Flap Complete Loss
- Unable to Determine
- Not Applicable

Show only when Condition Type is `Skin Tear`.

---

## 16. Surgical Wound

### Label

`Closure Status`

### Options

- Approximated/Closed
- Partially Open
- Dehisced
- Healing by Secondary Intention
- Unable to Determine

Show only when Condition Type is `Surgical Wound`.

---

## 17. MASD

### Label

`Moisture Source`

### Options

- Incontinence
- Perspiration
- Wound Drainage
- Peristomal Output
- Other
- Unable to Determine

`Other` requires a short explanation.

---

## 18. Advanced Wound Findings

Keep collapsed by default.

### Undermining Present

- No
- Yes
- Unable to Determine

When `Yes`, show:

- Clock Start
- Clock End
- Maximum Depth (cm)

### Tunneling Present

- No
- Yes
- Unable to Determine

When `Yes`, allow repeatable rows:

- Clock Position
- Depth (cm)

### Slough Present

- No
- Yes
- Unable to Determine

When `Yes`, show:

- Estimated Percentage
- Description

### Eschar Present

- No
- Yes
- Unable to Determine

When `Yes`, show:

- Estimated Percentage
- Description

### Exposed Structure

Multi-select:

- None Observed
- Adipose
- Fascia
- Muscle
- Tendon
- Cartilage
- Bone
- Other
- Unable to Determine

`Other` requires a short explanation.

### Stage gating

- Stage 1 and Deep Tissue Pressure Injury: hide Advanced Wound Findings.
- Stage 2: only `None Observed` or `Unable to Determine` for Exposed Structure.
- Stage 3: allow Adipose; do not allow exposed fascia, muscle, tendon, cartilage, or bone.
- Stage 4: allow the full list.
- Unstageable: show Slough and Eschar; do not require Depth.

---

## 19. Photos

Photos are optional supporting evidence and never block completion.

### Photo Source

- Visiting RN
- Supervising RN
- LVN
- Wound Specialist
- Administrator Upload
- Hospital Record
- Other Clinical Source

### Captured By Role

- RN
- LVN
- Wound Nurse
- Clinical Supervisor
- Physician
- Other Licensed Clinician
- Unknown/External Record

### Required photo metadata when a photo is uploaded

- Wound number
- Photo date
- Photo source
- Captured By Role
- Uploaded by authenticated user
- Upload timestamp

### Optional metadata

- Captured-by name
- Caption/notes

Remove required-photo warnings. Use neutral text:

`No photos attached.`

---

## 20. Photo Timeline

Maintain one timeline per numbered wound.

Allow chronological review of photos from:

- Visiting RN
- Supervising RN
- LVN
- Wound Specialist
- Administrator Upload
- Hospital Record
- Other Clinical Source

Provide:

- Newest First
- Oldest First
- Side-by-side comparison of any two dates

Photo comparison supports clinical review but does not automatically determine improvement, stability, or worsening.

---

## 21. Wound Assessment Narrative

Use one assessment-level narrative, not one required narrative per wound.

### Label

`Wound Assessment Narrative`

### Purpose

The single narrative may document:

- Overall wound burden
- Wound numbers requiring explanation
- Clinical ambiguity not captured by selectors
- Family/caregiver education
- Physician communication
- New orders received
- Wound specialist involvement
- Goals of care
- Palliative wound-management context

The narrative is not replaced by checklists, and checklists are not replaced by the narrative.

### Wound Specialist Referral

- Not Needed
- Recommended
- Ordered
- Completed

When not `Not Needed`, show:

- Referral Date
- Recommendation Summary

### New Orders Received

- No
- Yes

When `Yes`, show:

- Orders Narrative Summary

Do not create separate structured fields for every narrative purpose. Keep one narrative plus the existing referral and new-order controls.

---

## 22. Main Patient Wound Map

Keep one large main Patient Wound Map.

### Rules

- Display numbered markers matching wound numbers.
- Markers and Select Wound dropdown remain synchronized.
- Front and Back controls remain.
- Do not show a secondary mini map in the wound editor.
- A wound without a location has no marker and remains selectable from the dropdown.
- Changing wound selection must not resize or move the editor.

---

## 23. Completion rules

A Pressure Injury is complete when applicable required fields are present:

- Condition Type
- Location
- Present at Admission
- Stage/Category
- Stage-required measurements or one valid Reason Not Measured
- Drainage Amount when applicable
- Device description when device-related

A non-pressure condition is complete when applicable required fields are present:

- Condition Type
- Location
- Present at Admission
- Condition-specific classification when applicable
- Measurements or Reason Not Measured when applicable
- Drainage Amount when applicable

Photos never block completion.

---

## 24. Historical records

- Preserve signed historical values exactly as documented.
- Do not rewrite signed records.
- Do not expose migration terminology in the clinician UI.
- For unambiguous editable locations, populate structured values silently.
- For ambiguous historical locations, show:

`Location needs clarification.`

- Historical `Skin Open or Intact` values may display read-only only in signed historical records.
- Do not use historical retired fields in new completion logic.

---

## 25. Required contradictions to prevent

Block or automatically reconcile:

- Pressure Injury without Stage/Category
- Pressure Injury with a non-pressure-only location restriction
- Skin Tear with Pressure Injury Stage/Category
- Diabetic Foot Ulcer at Coccyx
- Venous Ulcer at Ear
- Drainage Amount `None` with a non-N/A Drainage Character
- Numeric measurements plus a Reason Not Measured
- Infection answer `No` with infection findings retained
- Stage 1 with required Depth
- Stage 3 with exposed fascia, muscle, tendon, cartilage, or bone
- Stage 2 with exposed adipose or deeper structures

---

## 26. Implementation order

1. Replace the large Wound Inventory selector with the compact Select Wound dropdown.
2. Restore/retain the large main Patient Wound Map.
3. Remove the secondary mini map.
4. Add Pressure Injury to the visible Condition Type list.
5. Apply the final controlled values above.
6. Make the editor position static across wound selections.
7. Implement contradiction prevention.
8. Run browser acceptance tests.

Do not alter other RNICA sections during this implementation.

---

## 27. Acceptance tests

1. Add a Pressure Injury and confirm Pressure Injury is visible as Condition Type.
2. Select Stage 1 and confirm measurements do not block completion.
3. Select Stage 3 and confirm Length, Width, and Depth or Reason Not Measured are required.
4. Add a Skin Tear and confirm Pressure Injury Stage is absent.
5. Set Drainage Amount to None and confirm Drainage Character becomes Not Applicable.
6. Enter measurements, then select Reason Not Measured; confirm contradictory values cannot remain.
7. Switch between wounds using only the Select Wound dropdown; confirm the editor does not move.
8. Click a map marker; confirm the Select Wound dropdown updates.
9. Select a wound with no location; confirm the editor remains stable and Set Location is available.
10. Confirm the mini map is absent.
11. Upload optional photos from each approved source; confirm wound number linkage and timeline ordering.
12. Confirm photos never block completion.
13. Confirm one assessment-level narrative is stored regardless of wound count.
14. Confirm signed historical records are unchanged.
15. Confirm return to RNICA restores Body Systems → Integumentary and prior scroll position.

---

## Final Product Owner directive

Implement this specification as written. Do not create additional controlled values, selectors, maps, narratives, statuses, or completion rules without explicit Product Owner approval.
