// RNICA approved 9-step workflow navigation taxonomy.
//
// This is a PRESENTATION-ONLY grouping layer. It does not add, remove, or
// change any clinical field, validation rule, response set, or backend
// behavior -- it only defines how the existing assessment modules (see
// rnIcaClinicalNavigation.js) are grouped and labeled for navigation.
//
// [OWNER DECISION -- 2026-09-25, "FINAL GITHUB IMPLEMENTATION PACKAGE"]
// Superseded the prior 13(+Other)-screen taxonomy (numbered accordion,
// one entry per data domain). RNICA navigation represents WORKFLOW, not a
// one-to-one map of every data domain. The approved, exact 9-step order is:
//   1. Patient Story
//   2. Evidence & Intake
//   3. Clinical Review    (NEW -- synthesis workspace; see below)
//   4. Functional Status
//   5. Pain Assessment    (renamed from "Pain & Symptom Burden")
//   6. Caregiver & Support
//   7. Safety & Risk       (renamed from "Safety & Clinical Risk")
//   8. Compliance          (renamed from "Compliance & Readiness")
//   9. Finalize            (renamed from "Finalization")
// Do not add additional primary navigation items and do not reintroduce
// HOPE Administrative Review, Diagnosis & LCD, Body Systems, ACP & Goals of
// Care, Orders & POC, or AI Action Center as their own top-level steps --
// per owner direction their underlying modules still exist and are still
// fully RN-documentable, just re-homed as noted per screen below:
//
//   - HOPE Administrative Review's "demographics" module (CMS Section A:
//     A1005/A1010/A1110 x2/A1905/A1910) is now owned by Evidence & Intake
//     (2nd sub-item, alongside vitals) -- "HOPE should be populated from
//     Evidence & Intake" per owner direction. Same component
//     (HopeAdministrativeReview), same formData.demographics /
//     formData.livingSituation persistence -- only its screen membership
//     changed. See RNICACommandWorkspace.jsx's dedicated
//     `activeSection === "demographics"` render branch.
//   - Diagnosis & LCD ("diagnoses"), Body Systems (the ten body-system
//     modules), and ACP & Goals of Care ("advancedCarePlanning") are now
//     owned by Clinical Review -- owner direction: "Clinical Review...
//     may contain: Diagnosis & LCD, Disease Trajectory, Prognosis Support,
//     Supporting Evidence, Clinical Narrative, ACP & Goals of Care...
//     without becoming separate navigation entries." Body Systems was not
//     enumerated by name in owner direction; it is grouped here rather
//     than left without any navigation home, consistent with the same
//     "Clinical Review is the synthesis workspace" principle and the
//     approved mockup's Clinical Review screen showing a Systems Review
//     Summary. Flagged for explicit owner confirmation.
//   - Orders & POC ("admissionsOrder", "ordersHub", "referrals") are now
//     owned by Clinical Review -- owner direction: "Orders remain
//     available from Clinical Review / Plan of Care integration."
//   - AI Action Center is removed entirely as a navigation entry (no
//     screen owns it). "AI Action Center remains globally available. Do
//     not place AI Action Center inside RNICA workflow navigation." Its
//     content (RNICA Intelligence) remains visible inline on the
//     Finalization screen (unchanged) -- a persistent global header
//     button is a separate, not-yet-built UI affordance outside the scope
//     of this navigation restructuring.
//
// Each screen still groups the same, unchanged module routes -- no field,
// validation, or persistence path changes as a result of this file.

export const RNICA_THIRTEEN_SCREENS = [
  {
    key: "patientStory",
    label: "Patient Story",
    moduleKeys: [],
    crossCutting: true,
    landingModuleKey: "demographics",
    railTarget: "intelligence",
  },
  {
    key: "evidenceIntake",
    label: "Evidence & Intake",
    // Vitals (Clinical Snapshot) render inline, always visible, leading
    // the screen -- see RNICACommandWorkspace.jsx. "demographics" (HOPE
    // Section A administrative items) is folded in here per the
    // 2026-09-25 owner decision above -- not a separate top-level step.
    moduleKeys: ["vitals", "demographics"],
  },
  {
    // [OWNER DECISION -- 2026-09-25] NEW screen. Clinical Review is the
    // synthesis workspace: disease trajectory, hospice support rationale,
    // systems summary, and problem list, consuming Evidence & Intake,
    // Functional Status, Pain, Caregiver & Support, and Safety & Risk. Its
    // own documentation sub-items (Diagnosis & LCD, Body Systems, ACP &
    // Goals of Care, Orders & POC) are folded in here rather than
    // duplicating another documentation form at the top level.
    key: "clinicalReview",
    label: "Clinical Review",
    moduleKeys: [
      "diagnoses", "advancedCarePlanning",
      "neurological", "cardiovascular", "respiratory", "infection",
      "gastrointestinal", "nutrition", "endocrine", "genitourinary",
      "musculoskeletal", "skin",
      "admissionsOrder", "ordersHub", "referrals",
    ],
  },
  {
    key: "functionalStatus",
    label: "Functional Status",
    moduleKeys: ["performanceStatus"],
  },
  {
    key: "painSymptomBurden",
    label: "Pain Assessment",
    // Owner correction 2026-09-25: Symptom Impact Screening ("symptomImpact"
    // / HOPE J2051 A-H) is no longer an RN-facing module -- each symptom is
    // documented once, in its true owning section (Pain, Respiratory, GI,
    // Neuro/Mental Status), and HOPE J2051 is derived from those fields.
    // Only "pain" remains a countable module here.
    moduleKeys: ["pain"],
  },
  {
    key: "caregiverSupport",
    label: "Caregiver & Support",
    // RNICA_REDESIGN_SOURCE_OF_TRUTH.md Screen 7: caregiver capability,
    // living support, psychosocial, spiritual, personal-care, teaching.
    moduleKeys: ["caregiverAssessment", "psychosocial", "spiritual", "bereavement", "personalCare", "teachingNeeds"],
  },
  {
    key: "safetyClinicalRisk",
    label: "Safety & Risk",
    // RNICA_REDESIGN_SOURCE_OF_TRUTH.md Screen 8: fall risk, oxygen safety,
    // home/disaster safety, imminent-death screening -- legacy `safety` and
    // `imminentDeath` modules, plus SFV per the Feature-to-UI Wiring Matrix.
    moduleKeys: ["safety", "imminentDeath", "sfv"],
  },
  {
    key: "complianceReadiness",
    label: "Compliance",
    // RNICA_SCREEN_AUTHORITY_MATRIX.md #11: "Owns: Presentation only."
    // Backed by getRnicaFinalizationReadiness -- same source as the Lock
    // gate. Surfaced today via the Finalization screen's readiness/
    // validation rail.
    moduleKeys: [],
    crossCutting: true,
    landingModuleKey: "finalization",
    railTarget: "validation",
  },
  {
    key: "finalization",
    label: "Finalize",
    // RNICA_SCREEN_AUTHORITY_MATRIX.md #13: narrative, readiness,
    // attestation, signature, lock, amendment, and audit review all live
    // here today (AmendmentPanel is rendered inside the finalization
    // module -- see RNICA.jsx:6099). RNICA Intelligence (formerly reached
    // via the separate "AI Action Center" nav entry) also surfaces inline
    // here.
    moduleKeys: ["finalization"],
  },
];

/**
 * Groups a flat, already-filtered `routes` list (module-level routes, as
 * produced by RNICA.jsx today) into the 13 approved screens. Any module key
 * not found in the taxonomy is placed in a trailing "Other" group instead of
 * being silently dropped -- this is a safety net, not expected in normal use.
 */
export function groupRoutesIntoScreens(routes) {
  const routesByKey = new Map(routes.map((route) => [route.key, route]));
  const consumed = new Set();

  const groups = RNICA_THIRTEEN_SCREENS.map((screen) => {
    const moduleRoutes = screen.moduleKeys
      .map((key) => routesByKey.get(key))
      .filter(Boolean);
    moduleRoutes.forEach((route) => consumed.add(route.key));
    return { ...screen, routes: moduleRoutes };
  });

  const leftover = routes.filter((route) => !consumed.has(route.key));
  if (leftover.length > 0) {
    groups.push({
      key: "other",
      label: "Other",
      moduleKeys: leftover.map((route) => route.key),
      routes: leftover,
    });
  }

  return groups;
}

/** Screen (group) that a given module route key belongs to, or null. */
export function screenForModuleKey(moduleKey) {
  return RNICA_THIRTEEN_SCREENS.find((screen) => screen.moduleKeys.includes(moduleKey)) || null;
}
