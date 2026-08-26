import { RNICA_BODY_SYSTEM_MODULES } from "../../config/bodySystems";

export const RNICA_ASSESSMENT_MODULES = [
  { key: "demographics", label: "Patient Demographics", formSection: "demographics", regulator: "HOPE", hope: ["A1110", "A1005", "A1010"] },
  { key: "caregiverAssessment", label: "Caregiver Assessment", formSection: "demographics", completionPath: "pcg", validationPrefix: "demographics.pcg", regulator: "CDPH" },
  { key: "advancedCarePlanning", label: "Advanced Care Planning", formSection: "demographics", completionPath: "advancedCarePlanning", validationPrefix: "demographics.advancedCarePlanning", regulator: "CDPH" },
  { key: "vitals", label: "Vitals", formSection: "vitals" },
  { key: "pain", label: "Pain Assessment", formSection: "pain", regulator: "HOPE", hope: ["J0900", "J0915"] },
  { key: "symptomImpact", label: "Symptom Impact", formSection: "symptomImpact", regulator: "HOPE", hope: ["J2051"] },
  { key: "diagnoses", label: "Diagnoses", formSection: "diagnoses", regulator: "HOPE", hope: ["I0010", "J0050"] },
  { key: "performanceStatus", label: "Performance Status", formSection: "performanceStatus", regulator: "HOPE", hope: ["M1190"] },
  ...RNICA_BODY_SYSTEM_MODULES,
  { key: "imminentDeath", label: "Imminent Death", formSection: "imminentDeath", regulator: "HOPE", hope: ["J0050"] },
  { key: "sfv", label: "SFV", formSection: "sfv", regulator: "HOPE", hope: ["J2050", "J2052", "J2053"] },
  { key: "safety", label: "Safety", formSection: "safety" },
  { key: "psychosocial", label: "Psychosocial", formSection: "psychosocial" },
  { key: "spiritual", label: "Spiritual", formSection: "spiritual" },
  { key: "bereavement", label: "Bereavement", formSection: "bereavement" },
  { key: "personalCare", label: "Personal Care", formSection: "personalCare" },
  { key: "teachingNeeds", label: "Teaching Needs", formSection: "teachingNeeds" },
  { key: "admissionsOrder", label: "Admissions Order", formSection: "admissionsOrder" },
  { key: "ordersHub", label: "Hospice Orders Hub", formSection: "medications" },
  { key: "referrals", label: "Referrals", formSection: "referrals" },
  { key: "finalization", label: "Finalization", formSection: "finalization", regulator: "HOPE", hope: ["F2000", "F2100", "F2200"] },
];

const EXPECTED_MODULE_KEYS = [
  "demographics", "caregiverAssessment", "advancedCarePlanning", "vitals", "pain",
  "symptomImpact", "diagnoses", "performanceStatus", "neurological", "cardiovascular",
  "respiratory", "infection", "gastrointestinal", "nutrition", "endocrine",
  "genitourinary", "musculoskeletal", "skin", "imminentDeath", "sfv", "safety",
  "psychosocial", "spiritual", "bereavement", "personalCare", "teachingNeeds",
  "admissionsOrder", "ordersHub", "referrals", "finalization",
];

export function validateRnIcaClinicalNavigation(routes, availableFormSections = [], isOngoingAssessment = false) {
  const errors = [];
  // SFV (Symptom Follow-Up Visit) only applies to the one-time RN Initial
  // Comprehensive Assessment -- ongoing/recert visits never include it.
  // This must be an explicit, caller-supplied flag (not inferred from
  // routes.length): both modes can independently produce a 29- or
  // 30-route list depending on other future module changes, and a
  // route-count heuristic silently mismatches the actual mode.
  const expectedKeys = isOngoingAssessment
    ? EXPECTED_MODULE_KEYS.filter((key) => key !== "sfv")
    : EXPECTED_MODULE_KEYS;
  const expected = expectedKeys.map((key) => RNICA_ASSESSMENT_MODULES.find((module) => module.key === key));
  const ids = new Set();
  const availableSections = new Set(availableFormSections);
  if (routes.length !== expected.length) {
    errors.push(`RNICA navigation must contain ${expected.length} modules, received ${routes.length}`);
  }
  routes.forEach((route, index) => {
    if (ids.has(route.key)) errors.push(`Duplicate RNICA module key: ${route.key}`);
    ids.add(route.key);
    if (!route.formSection) errors.push(`RNICA module ${route.key} has no form section`);
    if (availableSections.size > 0 && !availableSections.has(route.formSection)) {
      errors.push(`RNICA module ${route.key} targets missing form section ${route.formSection}`);
    }
    if (route.key !== expectedKeys[index]) {
      errors.push(`RNICA module ${index + 1} must be ${expectedKeys[index] || "absent"}, received ${route.key}`);
    }
    const expectedRegulator = isOngoingAssessment && expected[index]?.regulator === "HOPE"
      ? null
      : expected[index]?.regulator || null;
    if ((route.regulator || null) !== expectedRegulator) {
      errors.push(`RNICA module ${route.key} has an incorrect regulatory badge`);
    }
  });
  if (routes[routes.length - 1]?.key !== "finalization") errors.push("Finalization must be the last RNICA module");

  return { valid: errors.length === 0, errors };
}

export function validateBodyMapRegions({ anterior, posterior, assetWidth, assetHeight, viewBoxWidth, viewBoxHeight }) {
  const errors = [];
  const allRegions = [...anterior, ...posterior];
  const ids = new Set();

  if (assetWidth / assetHeight !== viewBoxWidth / viewBoxHeight) {
    errors.push("Body-map asset and overlay aspect ratios differ");
  }
  allRegions.forEach((region) => {
    if (!region.id || !region.label) errors.push("Every body-map region must have its own persisted id and display label");
    if (ids.has(region.id)) errors.push(`Duplicate body-map region id: ${region.id}`);
    ids.add(region.id);
    if (region.x < 0 || region.x > viewBoxWidth || region.y < 0 || region.y > viewBoxHeight) {
      errors.push(`Body-map region ${region.id} is outside the overlay viewBox`);
    }
    if (/(foot|feet|toe|heel|sole|achilles|malleolus)/i.test(`${region.id} ${region.label}`) && region.y < viewBoxHeight * 0.85) {
      errors.push(`Distal foot region ${region.id} is not at the bottom of the body map`);
    }
    if (/abdomen|navel/i.test(`${region.id} ${region.label}`) && (region.y < viewBoxHeight * 0.3 || region.y > viewBoxHeight * 0.55)) {
      errors.push(`Abdominal region ${region.id} is outside the abdominal band`);
    }
  });
  ["right_toes", "left_toes", "right_heel", "left_heel", "right_sole", "left_sole"].forEach((id) => {
    if (!ids.has(id)) errors.push(`Body-map distal landmark is missing: ${id}`);
  });

  return { valid: errors.length === 0, errors };
}
