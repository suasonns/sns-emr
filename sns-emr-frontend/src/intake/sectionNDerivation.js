// CMS HOPE Section N (N0500 Scheduled Opioid, N0510 PRN Opioid, N0520 Bowel
// Regimen) derivation from the patient's actual Current Medications list.
//
// Ownership: the Current Medications workflow (`MedicationOrdersCard`,
// `backend/app/api/medications.py`) is the single source of truth for what
// medications a patient is actually on. This module ONLY reads that data
// (via the `drug_classes` field the API already returns from
// drug_safety_service.get_drug_classes) and computes a suggested Section N
// answer. It never becomes a second source of truth: RNICA.jsx must always
// let the RN review/override the suggestion before it is saved to
// formData.medications (see MedicationSectionNAutoAssessCard), and nothing
// here writes to the assessment directly.
//
// A medication contributes to Section N only while it is ACTIVE (no
// end_date / status !== "discontinued") — a discontinued opioid does not
// currently justify N0500/N0510 = Yes.

const OPIOID_CLASS = "OPIOIDS";
// drug_classes.json's "LAXATIVES" class already includes stool softeners
// (e.g. docusate) alongside stimulant laxatives (senna, bisacodyl) and
// osmotic agents (polyethylene glycol) — there is no separate class key.
const BOWEL_REGIMEN_CLASSES = ["LAXATIVES"];

// Real-world medication orders record PRN-ness as free text inside the
// `frequency` field (e.g. "Q4H PRN", "PRN for breakthrough pain") — the
// backend `Medication.is_prn` column exists but is never set by
// `add_medication` today, so it is not a reliable signal yet. This regex
// mirrors how frequency is actually documented.
const PRN_PATTERN = /\bprn\b/i;

function isActive(med) {
  if (!med) return false;
  if (med.status) return med.status !== "discontinued";
  return !med.end_date;
}

function hasClass(med, classNames) {
  const classes = med?.drug_classes;
  if (!Array.isArray(classes) || classes.length === 0) return false;
  return classes.some((c) => classNames.includes(String(c).toUpperCase()));
}

function isPrnOrder(med) {
  return PRN_PATTERN.test(med?.frequency || "");
}

function describeMed(med) {
  const parts = [med?.medication_name, med?.dosage, med?.route, med?.frequency].filter(Boolean);
  return parts.join(" ") || "(unnamed medication)";
}

/**
 * Derive a suggested CMS HOPE Section N answer set from a patient's
 * medication list (as returned by `listMedications()`).
 *
 * Returns:
 *   {
 *     scheduledOpioid: boolean,   // suggested N0500
 *     prnOpioid: boolean,         // suggested N0510
 *     bowelRegimen: boolean,      // suggested N0520 support (Initiated/continued)
 *     opioidPresent: boolean,     // any active opioid, scheduled or PRN
 *     derivedFrom: {
 *       scheduledOpioid: string[],  // human-readable source medication descriptions
 *       prnOpioid: string[],
 *       bowelRegimen: string[],
 *     },
 *   }
 */
export function deriveSectionNFromMedications(medications) {
  const active = (Array.isArray(medications) ? medications : []).filter(isActive);

  const opioidMeds = active.filter((m) => hasClass(m, [OPIOID_CLASS]));
  const scheduledOpioidMeds = opioidMeds.filter((m) => !isPrnOrder(m));
  const prnOpioidMeds = opioidMeds.filter(isPrnOrder);
  const bowelRegimenMeds = active.filter((m) => hasClass(m, BOWEL_REGIMEN_CLASSES));

  return {
    scheduledOpioid: scheduledOpioidMeds.length > 0,
    prnOpioid: prnOpioidMeds.length > 0,
    bowelRegimen: bowelRegimenMeds.length > 0,
    opioidPresent: opioidMeds.length > 0,
    derivedFrom: {
      scheduledOpioid: scheduledOpioidMeds.map(describeMed),
      prnOpioid: prnOpioidMeds.map(describeMed),
      bowelRegimen: bowelRegimenMeds.map(describeMed),
    },
  };
}
