# Infection Architecture & Summary Confirmation Report (Items 7, 9–12)

**Date:** 2026-10-06
**Scope:** Formal, code-cited confirmation of items 7 and 9–12 of the owner's 22-item directive. No behavior changes were required for these items — each was verified against the current codebase and, where only a comment was inaccurate, corrected (see §6).

## Item 7 — Single Canonical Allergy Source

**Confirmed: one canonical source, zero duplicate-creation paths.**

- **Model:** `backend/app/models/patient_allergy.py` — single table `patient_allergies`.
- **API:** `backend/app/api/patient_allergies.py` — single REST resource (`GET`/`POST`/`DELETE` under `/patients/{patient_id}/allergies`). `DELETE` is a soft delete (`active=false`); `GET` filters `active=true`.
- **Frontend client:** `sns-emr-frontend/src/api/medications.ts` — `listPatientAllergies` / `addPatientAllergy` / `removePatientAllergy`, used uniformly everywhere allergies are read or written.
- **Canonical UI owner:** `AllergiesCard` (`RNICA.jsx` ~line 8353) — the only component that creates/edits/removes allergy records. Shared by Infection, Facesheet's Structured Allergies panel, and Medications safety checks — all three render the *same* `patient_allergies` rows; an allergy entered in any one of them appears in the other two immediately.
- **Secondary read (not a duplicate creation path):** the Infection Summary/Structured Findings rail (`RNICA.jsx` ~line 17225, `infectionAllergyAlerts`) independently calls `listPatientAllergies` purely to format severity-ordered alert lines for the Summary. It writes nothing — it is a read-only consumer of the same canonical data, not a second allergy store.

## Item 9–10 — Summary / Structured Findings Display Rules

Verified in `computeBodySystemFindings`, `case "infection"` (`RNICA.jsx` ~line 11138):

1. **All documented allergies appear, every severity included** — `extra.allergyAlerts` (built from `formatAllergyAlertLines`, ~line 8340) is pushed into the findings list unconditionally; nothing filters out mild/unclassified entries.
2. **Severest-first ordering** — `formatAllergyAlertLines` sorts by `ALLERGY_SEVERITY_RANK` (`ANAPHYLAXIS: 0, SEVERE: 1, MODERATE: 2, MILD: 3`, unknown last), so the clinically riskiest allergy always leads.
3. **Required owner-specified display order (section 11) is implemented exactly:**
   - A. Allergies
   - B. Active Infection
   - C. Current resistant organism
   - D. Antibiotic therapy and precautions
   - E. Immunosuppression
   - F. Infection history and other documented findings (history-of-resistant-organism included here, separate from the *current* resistant-organism line in C)
4. **Naming:** Infection's findings/summary code path contains no "Cognitive Screen" references — that term is scoped exclusively to the Neurological section's own card (`"SNS Cognitive Screen"`, ~lines 13089/15003/15077). No cross-contamination between sections.

## Item 11 — Grouped Allergy Display

Verified in `AllergiesCard` (`RNICA.jsx` ~line 8468): saved allergies are grouped by `allergen_type` into one heading per category (`Medication Allergies`, `Food Allergies`, `Environmental Allergies`, `Other Sensitivities`), each showing only non-empty categories, independent of any Infection Overview workflow state (Allergies render once in "Patient Reference Information", category `profile`, never duplicated by workflow-state branching).

## Item 12 — "REQUIRES FOLLOW-UP" Rule (exact current logic)

Implemented as `computeInfectionRequiresFollowUp(d)` (`RNICA.jsx` ~line 11212). The badge is driven **only** by genuine infection-clinical findings, explicitly excluding allergy/immunosuppression facts:

```
requiresFollowUp =
     activeInfections.length > 0                    // d.currentInfections, excluding "None"
  || resistantCurrent.length > 0                     // d.antibioticResistantInfection, excluding "None"
  || resistantHistory.length > 0                     // d.historyOfResistantInfections, excluding "None"
  || activeAntibiotics                               // d.antibioticTherapyStatus !== "Not receiving antibiotics"
  || nonStandardPrecautions                          // any d.precautions !== "Standard"
  || infectionHistoryDocumented                      // d.recurrentInfection, or infectionHistoryTypes, or free-text d.infectionHistory
```

**Rationale (per in-code comment):** a documented allergy or immunosuppressed status is a patient-safety *fact*, not itself an infection follow-up trigger — it is computed separately from `primaryIssues` (which still *displays* allergy/immunosuppression findings in the Summary, per items 9–10 above) so the badge reflects only findings that require *infection-specific* clinical action. This is already covered by passing automated assertions in `verify-infection-rebuild.mjs` (`Immunosuppression alone: "REQUIRES FOLLOW-UP" NOT shown` / `Genuine infection finding: IS shown`).

## Additional confirmation found during this review (not separately itemized, but directly relevant)

- **"Unable to Assess" has already been removed from Infection Overview's live options** (`RNICA.jsx` ~line 15635): the segmented control now offers only `No Current Infection Concern`, `Existing Infection Findings Review`, `New or Worsening Infection Findings`. The two legacy reason fields are `legacyReadOnly` — they still display a value saved on a pre-existing record, but are never offered as a live/editable option on any new or in-progress assessment. This matches the clinical conclusion that infection status is determinable from records/observation/labs rather than patient participation.
- **Infection Overview correctly renders before Patient Reference Information**: `BODY_SYSTEM_CATEGORY_ORDER = ["core", "symptoms", "functional", "disease", "treatments", "response", "observation", "profile"]` places `profile` (Allergies, Immune Status) **last**, after `core` (Infection Overview). The nurse's first question — "is there a current infection concern?" — is answered before any allergy/immune-status review. A stale comment that incorrectly described this ordering as reversed was corrected (commit `fa79c84`); no behavior change was needed.

## Determination

Items 7, 9, 10, 11, and 12 are **confirmed satisfied by existing code** — no further implementation changes required for these items.
