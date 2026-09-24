// RNICA 13-screen presentation taxonomy.
//
// This is a PRESENTATION-ONLY grouping layer (Phase B of the RNICA redesign
// authorization). It does not add, remove, or change any clinical field,
// validation rule, response set, or backend behavior -- it only defines how
// the existing assessment modules (see rnIcaClinicalNavigation.js) are
// grouped and labeled for navigation.
//
// Module ownership per screen is taken directly from the repository's own
// authoritative design docs -- NOT re-derived here:
//   - docs/tenant-platform/RNICA_SCREEN_AUTHORITY_MATRIX.md (v2, screen
//     ownership/consumes/produces per screen)
//   - docs/tenant-platform/RNICA_REDESIGN_SOURCE_OF_TRUTH.md (Screens 1-13,
//     "Always visible" / "Do not touch" per screen)
// Screens 1 (Patient Story), 11 (Compliance & Readiness), 12 (AI Action
// Center), and the amendment-history portion of 13 (Finalization) are
// documented as owning NO module ("Owns: Nothing" / "Presentation only") --
// their content already exists as cross-cutting rail panels (RNICA
// Intelligence, Validation/readiness, AmendmentPanel) rather than as a
// legacy form module. Selecting one of these screens navigates to the
// existing screen that already surfaces that panel and scrolls/highlights
// it, instead of duplicating or rebuilding it.

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
    // RNICA_SCREEN_AUTHORITY_MATRIX.md #2: "legacy demographics, vitals,
    // referrals modules".
    moduleKeys: ["demographics", "vitals", "referrals"],
  },
  {
    // [PRODUCT-AUTHORITY DECISION -- 2026-09-22, final] Order 3-5 is
    // Pain & Symptom Burden, Diagnosis & LCD, Functional Status -- see
    // docs/tenant-platform/RNICA_NAVIGATION_SPECIFICATION.md and
    // RNICA_SCREEN_AUTHORITY_MATRIX.md #3. Identify pain/symptom burden
    // before establishing diagnosis; interpret functional status last,
    // with both in context.
    key: "painSymptomBurden",
    label: "Pain & Symptom Burden",
    moduleKeys: ["pain", "symptomImpact"],
  },
  {
    key: "diagnosisLcd",
    label: "Diagnosis & LCD",
    moduleKeys: ["diagnoses"],
  },
  {
    key: "functionalStatus",
    label: "Functional Status",
    moduleKeys: ["performanceStatus"],
  },
  {
    key: "bodySystems",
    label: "Body Systems",
    // RNICA_REDESIGN_SOURCE_OF_TRUTH.md Screen 6: the ten body-system
    // domains only. SFV and Imminent Death are covered under their own
    // screens per the Source of Truth (Screen 8, Safety & Clinical Risk).
    moduleKeys: [
      "neurological", "cardiovascular", "respiratory", "infection",
      "gastrointestinal", "nutrition", "endocrine", "genitourinary",
      "musculoskeletal", "skin",
    ],
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
    label: "Safety & Clinical Risk",
    // RNICA_REDESIGN_SOURCE_OF_TRUTH.md Screen 8: fall risk, oxygen safety,
    // home/disaster safety, imminent-death screening -- legacy `safety` and
    // `imminentDeath` modules, plus SFV per the Feature-to-UI Wiring Matrix.
    moduleKeys: ["safety", "imminentDeath", "sfv"],
  },
  {
    key: "acpGoalsOfCare",
    label: "ACP & Goals of Care",
    moduleKeys: ["advancedCarePlanning"],
  },
  {
    key: "ordersPoc",
    label: "Orders & POC",
    moduleKeys: ["admissionsOrder", "ordersHub"],
  },
  {
    key: "complianceReadiness",
    label: "Compliance & Readiness",
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
    key: "aiActionCenter",
    label: "AI Action Center",
    // RNICA_SCREEN_AUTHORITY_MATRIX.md #12: "Owns: No clinical source
    // data." Backed by getRnicaIntelligence -- the existing RNICA
    // Intelligence rail panel.
    moduleKeys: [],
    crossCutting: true,
    landingModuleKey: "finalization",
    railTarget: "intelligence",
  },
  {
    key: "finalization",
    label: "Finalization",
    // RNICA_SCREEN_AUTHORITY_MATRIX.md #13: narrative, readiness,
    // attestation, signature, lock, amendment, and audit review all live
    // here today (AmendmentPanel is rendered inside the finalization
    // module -- see RNICA.jsx:6099).
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
