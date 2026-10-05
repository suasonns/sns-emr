import { chromium } from "@playwright/test";

const BASE_URL = process.env.VERIFY_BASE_URL || "http://localhost:5173";
const LOGIN_EMAIL = "rsuason@loveandfaithhospice.com";
const LOGIN_PASSWORD = "LoveFaithHospice2026!";
const PATIENT_ID = "53fe69e1-fcd5-4b49-8203-9b890b18b7d6";
const ASSESSMENT_ID = "84234eb9-bfb9-4222-8287-4f4e8475c593";

async function apiGetFull(page) {
  return page.evaluate(async (assessmentId) => {
    const token = localStorage.getItem("sns-hospice-solutions-access-token");
    const res = await fetch(`/visits/rnica/${assessmentId}`, { credentials: "include", headers: { Authorization: `Bearer ${token}` } });
    return res.json();
  }, ASSESSMENT_ID);
}

async function apiSaveInfection(page, infection) {
  return page.evaluate(async ({ assessmentId, infection }) => {
    const token = localStorage.getItem("sns-hospice-solutions-access-token");
    const getRes = await fetch(`/visits/rnica/${assessmentId}`, { credentials: "include", headers: { Authorization: `Bearer ${token}` } });
    const full = await getRes.json();
    const newFormData = { ...full.formData, infection };
    const putRes = await fetch(`/visits/rnica/${assessmentId}`, {
      method: "PUT", credentials: "include",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ formData: newFormData, fieldProvenance: full.fieldProvenance || [] }),
    });
    return putRes.status;
  }, { assessmentId: ASSESSMENT_ID, infection });
}

async function getInfection(page) {
  return page.evaluate(async (assessmentId) => {
    const token = localStorage.getItem("sns-hospice-solutions-access-token");
    const res = await fetch(`/visits/rnica/${assessmentId}`, { credentials: "include", headers: { Authorization: `Bearer ${token}` } });
    const full = await res.json();
    return full.formData.infection;
  }, ASSESSMENT_ID);
}

const BASELINE_INFECTION = {
  allergies: [], allergyDetails: "",
  infectionOverview: "", infectionUnableToAssessReason: "", infectionUnableToAssessOther: "",
  currentInfections: [], currentInfectionOther: "",
  antibioticResistantInfection: [], historyOfResistantInfections: [],
  immunosuppressed: false, immunosuppressionReason: "", immunosuppressionReasonOther: "",
  antibioticUse: false, antibioticTherapyStatus: "", antibioticMedicationName: "", antibioticTreatmentEffective: "",
  temperature: "", recurrentInfection: false, infectionHistory: "", infectionHistoryTypes: [], infectionHistoryOther: "",
  precautions: [], notes: "", clinicalStatusChange: "", infectionExistingFindingsEditMode: false,
};

const DOCUMENTED_INFECTION = {
  ...BASELINE_INFECTION,
  infectionOverview: "Existing Infection Findings Review",
  currentInfections: ["Respiratory tract"],
  antibioticResistantInfection: [],
  historyOfResistantInfections: ["MRSA"],
  antibioticTherapyStatus: "Currently receiving antibiotics",
  antibioticMedicationName: "Keflex",
  precautions: ["Contact"],
  clinicalStatusChange: "Stable",
};

async function login(page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await page.getByLabel(/email/i).fill(LOGIN_EMAIL);
  await page.getByLabel(/^password/i).fill(LOGIN_PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForTimeout(2000);
  await page.evaluate((patientId) => window.sessionStorage.setItem("sns-hospice-solutions-active-patient", patientId), PATIENT_ID);
}

async function loadInfectionAccordion(page) {
  await page.goto(`${BASE_URL}/nursing-assessment`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.locator(".rnica-rail__label", { hasText: "Body Systems" }).first().click();
  await page.waitForTimeout(600);
  await page.locator(".rnica-bodysystems__trigger", { hasText: "Infection" }).first().click();
  await page.waitForTimeout(600);
}

const HIDEABLE_CARD_TITLES = [
  "Active Infection", "Resistant Organisms",
  "Infection History", "Antibiotic Therapy", "Precautions", "Temperature",
];
// OWNER DIRECTIVE (2026-10-05) "Shared Information = Render Once" --
// Allergies + Immune Status are patient-profile data; they must render
// exactly once and NEVER be hidden/rebuilt by any Infection Overview
// state.
const ALWAYS_VISIBLE_PROFILE_CARD_TITLES = ["Allergies", "Immune Status"];

async function cardTitleCount(page, title) {
  return page.locator(`[data-card-title="${title}"]`).count();
}

let failures = 0;
function check(label, cond) {
  console.log(`${cond ? "PASS" : "FAIL"}: ${label}`);
  if (!cond) failures++;
}

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1200 } });
  page.on("pageerror", (err) => console.log("BROWSER PAGE ERROR:", err.message));
  await login(page);

  // ── State 0: Initial Unselected State (owner directive 2026-10-05
  // item 4) -- before the nurse answers the first Infection question,
  // ONLY Infection Overview + the always-visible profile cards render;
  // every other card (including Clinical Status Change / Notes) stays
  // hidden, and the Summary reads the exact required wording. ──
  await apiSaveInfection(page, { ...BASELINE_INFECTION });
  await loadInfectionAccordion(page);
  for (const title of HIDEABLE_CARD_TITLES) {
    check(`Initial state: "${title}" card hidden`, (await cardTitleCount(page, title)) === 0);
  }
  check(`Initial state: "Clinical Status Change" card hidden`, (await cardTitleCount(page, "Clinical Status Change")) === 0);
  check(`Initial state: "Notes" card hidden`, (await cardTitleCount(page, "Notes")) === 0);
  for (const title of ALWAYS_VISIBLE_PROFILE_CARD_TITLES) {
    check(`Initial state: "${title}" card still visible (patient profile, never gated)`, (await cardTitleCount(page, title)) === 1);
  }
  const initialSummaryText = await page.locator('[data-section="infection"] .rnica-bodysystem-summary').first().innerText();
  // NOTE: the exact "Infection assessment not yet documented." wording is
  // asserted independently, against synthetic data with zero allergies,
  // in RNICA.infectionUnableToAssessRemoval.test.js (vitest) -- this
  // shared dev-environment patient already carries legitimately
  // documented baseline allergies (pcn/egg), so `hasAllergyAlerts` is
  // correctly true here and the summary correctly shows those allergy
  // lines instead of the not-yet-documented sentence (owner directive
  // 2026-10-05 "All Documented Allergies Must Appear" -- allergies must
  // never be hidden behind an Infection Overview gate, not even the
  // initial one). Only confirm no genuine infection finding is invented.
  check(`Initial state: Summary does not fabricate a genuine infection finding`, !/Active infection:|Current resistant organism:|Currently receiving antibiotics|precautions required/.test(initialSummaryText));
  check(`Initial state: "REQUIRES FOLLOW-UP" not shown`, (await page.locator('[data-section="infection"] .rnica-bodysystem-summary__flag').count()) === 0);

  // ── State 1: No Current Infection Concern (over documented data) ──
  await apiSaveInfection(page, { ...DOCUMENTED_INFECTION, infectionOverview: "No Current Infection Concern" });
  await loadInfectionAccordion(page);
  for (const title of HIDEABLE_CARD_TITLES) {
    check(`No Concern: "${title}" card hidden`, (await cardTitleCount(page, title)) === 0);
  }
  check(`No Concern: "Infection Findings Review" summary card NOT shown`, (await cardTitleCount(page, "Infection Findings Review")) === 0);
  for (const title of ALWAYS_VISIBLE_PROFILE_CARD_TITLES) {
    check(`No Concern: "${title}" card still visible (patient profile, never gated)`, (await cardTitleCount(page, title)) === 1);
  }
  check(`No Concern: "Clinical Status Change" card still visible`, (await cardTitleCount(page, "Clinical Status Change")) === 1);
  check(`No Concern: "Notes" card still visible`, (await cardTitleCount(page, "Notes")) === 1);
  check(`No Concern: preserved-data banner shown (documented findings exist)`, (await page.locator(".rnica-cv-preserved-findings-banner").count()) === 1);

  // ── State 2 (LEGACY ONLY): "Unable to Assess" is no longer offered as
  // a selectable Infection Overview option (owner directive 2026-10-05,
  // "Infection Is Not A Patient-Interview Workflow" -- no valid hospice
  // clinical scenario justifies it). A record saved before this change
  // that already holds this literal stored value must keep displaying
  // it read-only (never silently dropped/rewritten); the live control
  // must show exactly 3 selectable options with no way to newly pick it
  // again. ──
  await apiSaveInfection(page, { ...DOCUMENTED_INFECTION, infectionOverview: "Unable to Assess", infectionUnableToAssessReason: "Patient unresponsive" });
  await loadInfectionAccordion(page);
  const overviewOptionTexts = (await page.locator('[data-card-title="Infection Overview"] button').allInnerTexts())
    .map((t) => t.trim()).filter(Boolean);
  check(`Legacy Unable to Assess: segmented control no longer offers "Unable to Assess" as a live option`,
    !overviewOptionTexts.some((t) => /^Unable to Assess$/i.test(t)));
  check(`Legacy Unable to Assess: exactly 3 live Overview options remain`, overviewOptionTexts.length === 3);
  check(`Legacy Unable to Assess: "Previously recorded" legacy chip shown for the stored value`,
    (await page.getByText(/Previously recorded.*Unable to Assess/i).count()) > 0);
  check(`Legacy Unable to Assess: legacy reason still displayed read-only (never deleted)`,
    (await page.getByText(/Previously documented reason: Patient unresponsive/i).count()) > 0);
  for (const title of HIDEABLE_CARD_TITLES) {
    check(`Legacy Unable to Assess: "${title}" card hidden`, (await cardTitleCount(page, title)) === 0);
  }
  for (const title of ALWAYS_VISIBLE_PROFILE_CARD_TITLES) {
    check(`Legacy Unable to Assess: "${title}" card still visible (patient profile, never gated)`, (await cardTitleCount(page, title)) === 1);
  }
  check(`Legacy Unable to Assess: "Clinical Status Change" card still visible`, (await cardTitleCount(page, "Clinical Status Change")) === 1);
  check(`Legacy Unable to Assess: "Notes" card still visible`, (await cardTitleCount(page, "Notes")) === 1);

  // ── REQUIRES FOLLOW-UP decoupling (owner directive 2026-10-05 item
  // 12) -- a documented allergy or immunosuppressed status ALONE must
  // never force "Requires Follow-Up"; only genuine infection-clinical
  // findings may. ──
  await apiSaveInfection(page, { ...BASELINE_INFECTION, immunosuppressed: true, immunosuppressionReason: "Cancer treatment" });
  await loadInfectionAccordion(page);
  check(`Immunosuppression alone: finding line shown in Summary`,
    /Immunosuppressed/.test(await page.locator('[data-section="infection"] .rnica-bodysystem-summary').first().innerText()));
  check(`Immunosuppression alone: "REQUIRES FOLLOW-UP" NOT shown`, (await page.locator('[data-section="infection"] .rnica-bodysystem-summary__flag').count()) === 0);

  await apiSaveInfection(page, { ...BASELINE_INFECTION, currentInfections: ["UTI"] });
  await loadInfectionAccordion(page);
  check(`Genuine infection finding (Active UTI): "REQUIRES FOLLOW-UP" IS shown`, (await page.locator('[data-section="infection"] .rnica-bodysystem-summary__flag').count()) === 1);

  // ── State 3: Existing Infection Findings Review (review summary, not editor) ──
  await apiSaveInfection(page, { ...DOCUMENTED_INFECTION, infectionExistingFindingsEditMode: false });
  await loadInfectionAccordion(page);
  for (const title of HIDEABLE_CARD_TITLES) {
    check(`Existing Review: "${title}" editor card hidden (review summary only)`, (await cardTitleCount(page, title)) === 0);
  }
  check(`Existing Review: "Infection Findings Review" summary card shown exactly once`, (await cardTitleCount(page, "Infection Findings Review")) === 1);
  for (const title of ALWAYS_VISIBLE_PROFILE_CARD_TITLES) {
    check(`Existing Review: "${title}" card still visible (patient profile, never gated)`, (await cardTitleCount(page, title)) === 1);
  }
  const summaryText = await page.locator('[data-card-title="Infection Findings Review"]').innerText();
  check(`Existing Review: summary shows Active Infection`, /Respiratory tract/.test(summaryText));
  check(`Existing Review: summary shows Resistant Organisms history`, /MRSA/.test(summaryText));
  check(`Existing Review: summary shows Antibiotic Therapy`, /Keflex/.test(summaryText));
  check(`Existing Review: summary shows Precautions`, /Contact/.test(summaryText));
  check(`Existing Review: "Edit Existing Findings" action present`, (await page.getByRole("button", { name: /Edit Existing Findings/i }).count()) === 1);

  // Click "Edit Existing Findings" -> canonical editor opens, exactly once.
  await page.getByRole("button", { name: /Edit Existing Findings/i }).click();
  await page.waitForTimeout(400);
  for (const title of HIDEABLE_CARD_TITLES) {
    check(`Existing Review + Edit mode: "${title}" editor card shown exactly once`, (await cardTitleCount(page, title)) === 1);
  }
  check(`Existing Review + Edit mode: "Infection Findings Review" summary card gone (no duplicate)`, (await cardTitleCount(page, "Infection Findings Review")) === 0);
  check(`Existing Review + Edit mode: "Back to Review" action present`, (await page.getByRole("button", { name: /Back to Review/i }).count()) === 1);
  for (const title of ALWAYS_VISIBLE_PROFILE_CARD_TITLES) {
    check(`Existing Review + Edit mode: "${title}" card still visible exactly once (patient profile, never duplicated)`, (await cardTitleCount(page, title)) === 1);
  }

  // ── State 4: New or Worsening Infection Findings (full editor, always) ──
  await apiSaveInfection(page, { ...DOCUMENTED_INFECTION, infectionOverview: "New or Worsening Infection Findings", infectionExistingFindingsEditMode: false });
  await loadInfectionAccordion(page);
  for (const title of HIDEABLE_CARD_TITLES) {
    check(`New/Worsening: "${title}" editor card shown exactly once`, (await cardTitleCount(page, title)) === 1);
  }
  check(`New/Worsening: no "Infection Findings Review" summary duplicate`, (await cardTitleCount(page, "Infection Findings Review")) === 0);
  for (const title of ALWAYS_VISIBLE_PROFILE_CARD_TITLES) {
    check(`New/Worsening: "${title}" card still visible exactly once (patient profile, never duplicated)`, (await cardTitleCount(page, title)) === 1);
  }

  // ── OWNER DIRECTIVE (2026-10-05) "Shared Information = Render Once",
  // same-day follow-up "Workflow-First Ordering" -- Allergies + Immune
  // Status must render in a "Patient Reference Information" group
  // positioned AFTER every workflow-driven group ("Core Findings" /
  // Infection Overview, "Disease-Specific Findings", "Clinical Status
  // Change", "Nurse Observation"), never before. A nurse opening
  // Infection must reach the overview question first. ──
  const groupHeadings = await page.locator(".rnica-bodysystem-group__heading").allInnerTexts();
  const profileIdx = groupHeadings.findIndex((t) => /Patient Reference Information/i.test(t));
  const coreIdx = groupHeadings.findIndex((t) => /Core Findings/i.test(t));
  check(`New/Worsening: "Patient Reference Information" group heading renders exactly once`, groupHeadings.filter((t) => /Patient Reference Information/i.test(t)).length === 1);
  check(`New/Worsening: "Patient Reference Information" group renders AFTER "Core Findings" (Infection Overview) group`, profileIdx !== -1 && coreIdx !== -1 && profileIdx > coreIdx);

  // ── Allergy Type: add MULTIPLE allergies across DIFFERENT types in the
  // same workflow (owner correction 2026-10-05 "Allergies Are Not A
  // Single Choice" -- no category switching/section-mode, multiple
  // simultaneous types, grouped display). Owner correction (same day,
  // later) "Document The Allergy First, Classify It Second" removed the
  // quick-fill pill row entirely; the Type dropdown (not a button) now
  // immediately follows the Allergen input, so this helper selects the
  // dropdown option instead of clicking a pre-entry pill button. ──
  async function addAllergy(typeLabel, allergenText, options = {}) {
    await page.getByPlaceholder("Allergen (e.g. penicillin)").first().fill(allergenText);
    await page.locator("select").filter({ has: page.locator(`option:text-is("${typeLabel}")`) }).first().selectOption({ label: typeLabel });
    if (options.reactionText) {
      await page.getByPlaceholder(/Reaction/i).first().fill(options.reactionText);
    }
    if (options.severityLabel) {
      await page.locator("select").filter({ has: page.locator(`option:text-is("${options.severityLabel}")`) }).first().selectOption({ label: options.severityLabel });
    }
    await page.getByRole("button", { name: /\+ Add Allergy/i }).first().click();
    await page.waitForTimeout(700);
  }
  await addAllergy("Medication", "Penicillin (verify-script)", { severityLabel: "Severe", reactionText: "Hives" });
  await addAllergy("Food", "Milk (verify-script)", { severityLabel: "Moderate", reactionText: "GI upset" });
  await addAllergy("Environmental", "Latex (verify-script)");
  await addAllergy("Other / Sensitivity", "Adhesive Tape (verify-script)");

  const profileText = await page.locator("text=Current Allergy Profile").first().locator("xpath=..").innerText();
  check(`Allergy Type: all 4 simultaneous types present (no category switching)`,
    /Penicillin \(verify-script\)/.test(profileText) &&
    /Milk \(verify-script\)/.test(profileText) &&
    /Latex \(verify-script\)/.test(profileText) &&
    /Adhesive Tape \(verify-script\)/.test(profileText));
  check(`Allergy Type: grouped display shows "Medication Allergies" heading`, /Medication Allergies/i.test(profileText));
  check(`Allergy Type: grouped display shows "Food Allergies" heading`, /Food Allergies/i.test(profileText));
  check(`Allergy Type: grouped display shows "Environmental Allergies" heading`, /Environmental Allergies/i.test(profileText));
  check(`Allergy Type: grouped display shows "Other Sensitivities" heading`, /Other Sensitivities/i.test(profileText));

  // ── Summary accuracy (owner directive 2026-10-05 "All Documented
  // Allergies Must Appear") -- the Infection Summary card must surface
  // EVERY documented allergy regardless of severity (no suppressing mild
  // allergies), most-severe-first, using the exact same allergy records
  // just added above. ──
  await apiSaveInfection(page, { ...DOCUMENTED_INFECTION, infectionOverview: "Existing Infection Findings Review", infectionExistingFindingsEditMode: false });
  await loadInfectionAccordion(page);
  const allergySummaryText = await page.locator('[data-section="infection"] .rnica-bodysystem-summary').first().innerText();
  check(`Summary: shows Severe medication allergy (Penicillin/Hives)`, /Medication allergy: Penicillin \(verify-script\) \(Severe\)(.|\n)*Hives/.test(allergySummaryText));
  check(`Summary: shows Moderate food allergy (Milk/GI upset)`, /Food allergy: Milk \(verify-script\) \(Moderate\)(.|\n)*GI upset/.test(allergySummaryText));
  check(`Summary: Severe allergy line appears before Moderate allergy line`,
    allergySummaryText.indexOf("Penicillin (verify-script)") < allergySummaryText.indexOf("Milk (verify-script)"));
  check(`Summary: unsevered allergies (Latex, Adhesive Tape) still included (no suppression by severity)`,
    /Latex \(verify-script\)/.test(allergySummaryText) && /Adhesive Tape \(verify-script\)/.test(allergySummaryText));

  // Confirm allergy profile is NOT suppressed/rebuilt across Infection
  // Overview states (owner: "Allergies should not change based on"
  // Overview selection -- it is standing patient info, not gated).
  for (const overview of ["No Current Infection Concern", "Unable to Assess", "New or Worsening Infection Findings"]) {
    await apiSaveInfection(page, { ...DOCUMENTED_INFECTION, infectionOverview: overview });
    await loadInfectionAccordion(page);
    const txt = await page.locator("text=Current Allergy Profile").first().locator("xpath=..").innerText();
    check(`Allergy Type: profile still visible+unchanged under Overview="${overview}"`,
      /Penicillin \(verify-script\)/.test(txt) && /Milk \(verify-script\)/.test(txt) && /Latex \(verify-script\)/.test(txt) && /Adhesive Tape \(verify-script\)/.test(txt));
  }

  // Clean up the test allergies so this script doesn't leave permanent data.
  // NOTE: `text=${text}` + `xpath=..` previously matched an ANCESTOR container
  // (the whole allergy-group div, which also contains unrelated rows like the
  // patient's real "pcn"/"egg" entries) rather than the single row div, so the
  // click target was unreliable and silently left duplicates behind across
  // repeated runs. A direct-child CSS combinator (`div:has(> span:text-is(...))`)
  // narrows to the exact row div whose immediate child span is the allergen label.
  for (const text of ["Penicillin (verify-script)", "Milk (verify-script)", "Latex (verify-script)", "Adhesive Tape (verify-script)"]) {
    for (let guard = 0; guard < 10; guard++) {
      const row = page.locator(`div:has(> span:text-is("${text}"))`).first();
      if ((await row.count()) === 0) break;
      await row.getByRole("button", { name: /Remove/i }).click();
      await page.waitForTimeout(400);
    }
  }

  console.log(failures === 0 ? "\nALL CHECKS PASSED" : `\n${failures} CHECK(S) FAILED`);

  // Restore baseline so this script doesn't leave the shared assessment mutated.
  await apiSaveInfection(page, BASELINE_INFECTION);

  await browser.close();
  process.exit(failures === 0 ? 0 : 1);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
