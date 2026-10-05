import { chromium } from "@playwright/test";
import fs from "fs";

const BASE_URL = process.env.VERIFY_BASE_URL || "http://localhost:5176";
const LOGIN_EMAIL = "rsuason@loveandfaithhospice.com";
const LOGIN_PASSWORD = "LoveFaithHospice2026!";
const PATIENT_ID = "53fe69e1-fcd5-4b49-8203-9b890b18b7d6";
const ASSESSMENT_ID = "84234eb9-bfb9-4222-8287-4f4e8475c593";
const OUT_DIR = "scripts/respiratory-rebuild-output";
fs.mkdirSync(OUT_DIR, { recursive: true });

const BASELINE_RESPIRATORY = {
  notes: "", coughType: "", lungSounds: [],
  ventilator: {
    tracheostomySize: "", tracheostomyType: "",
    longTermVentilator: false, shortTermVentilator: false,
    ventilatorTypeAndSettings: "",
  },
  sobSeverity: "Moderate", respirations: [], exertionLevel: "",
  oxygenTherapy: {
    type: "", inUse: false, satOnO2: "", onRoomAir: false,
    hoursPerDay: "", deliveryMode: "", litersPerMinute: "",
  },
  screeningDate: "", treatmentDate: "", sputumCharacter: "",
  treatmentDeclined: false, treatmentInitiated: false,
  clinicalStatusChange: "", shortnessOfBreathScreened: false,
  respiratoryOverview: "", respiratoryUnableToAssessReason: "", respiratoryUnableToAssessOther: "",
};

// A "fully documented" record -- every one of the 5 clinical cards holds
// at least one real value -- used to prove "Existing Respiratory
// Findings Review" shows the COMPLETE previous picture, not a filtered
// subset.
const FULLY_DOCUMENTED_RESPIRATORY = {
  notes: "Patient tolerating current regimen well.",
  coughType: "Productive", lungSounds: ["Crackles", "Diminished"],
  ventilator: {
    tracheostomySize: "6.0", tracheostomyType: "Cuffed",
    longTermVentilator: false, shortTermVentilator: true,
    ventilatorTypeAndSettings: "AC/VC 400x14 PEEP 5",
  },
  sobSeverity: "Moderate", respirations: ["Labored", "Tachypnea"], exertionLevel: "Minimal exertion",
  oxygenTherapy: {
    type: "Nasal cannula", inUse: true, satOnO2: "92", onRoomAir: false,
    hoursPerDay: "24", deliveryMode: "Continuous", litersPerMinute: "2",
  },
  screeningDate: "2026-10-01", treatmentDate: "2026-10-02", sputumCharacter: "Thick, yellow",
  treatmentDeclined: false, treatmentInitiated: true,
  clinicalStatusChange: "Declining", shortnessOfBreathScreened: true,
  respiratoryOverview: "Existing Respiratory Findings Review",
  respiratoryUnableToAssessReason: "", respiratoryUnableToAssessOther: "",
};

async function apiSaveRespiratory(page, respiratory) {
  return page.evaluate(async ({ assessmentId, respiratory }) => {
    const token = localStorage.getItem("sns-hospice-solutions-access-token");
    const getRes = await fetch(`/visits/rnica/${assessmentId}`, { credentials: "include", headers: { Authorization: `Bearer ${token}` } });
    const full = await getRes.json();
    const newFormData = { ...full.formData, respiratory };
    const putRes = await fetch(`/visits/rnica/${assessmentId}`, {
      method: "PUT", credentials: "include",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ formData: newFormData, fieldProvenance: full.fieldProvenance || [] }),
    });
    return putRes.status;
  }, { assessmentId: ASSESSMENT_ID, respiratory });
}

async function getRespiratory(page) {
  return page.evaluate(async (assessmentId) => {
    const token = localStorage.getItem("sns-hospice-solutions-access-token");
    const res = await fetch(`/visits/rnica/${assessmentId}`, { credentials: "include", headers: { Authorization: `Bearer ${token}` } });
    const full = await res.json();
    return full.formData.respiratory;
  }, ASSESSMENT_ID);
}

async function login(page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await page.getByLabel(/email/i).fill(LOGIN_EMAIL);
  await page.getByLabel(/^password/i).fill(LOGIN_PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForTimeout(2000);
  await page.evaluate((patientId) => window.sessionStorage.setItem("sns-hospice-solutions-active-patient", patientId), PATIENT_ID);
}

async function setTheme(page, mode) {
  await page.evaluate((m) => window.localStorage.setItem("sns-hospice-theme-mode", m), mode);
}

async function loadRespiratoryAccordion(page) {
  await page.goto(`${BASE_URL}/nursing-assessment`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.locator(".rnica-rail__label", { hasText: "Body Systems" }).first().click();
  await page.waitForTimeout(600);
  await page.locator(".rnica-bodysystems__trigger", { hasText: "Respiratory" }).first().click();
  await page.waitForTimeout(600);
}

async function loadRespiratoryAccordionMobile(page) {
  await page.goto(`${BASE_URL}/nursing-assessment`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  // Mobile top-level screen nav is hidden behind a "Workflow" trigger that
  // opens the RnicaWorkflowSheet overlay (see RNICACommandWorkspace.jsx);
  // the desktop rail used by loadRespiratoryAccordion() is not rendered
  // on narrow viewports at all.
  await page.locator(".rnica-screen__mobile-nav-trigger", { hasText: "Workflow" }).first().click();
  await page.waitForTimeout(400);
  await page.locator(".rnica-rail-sheet .rnica-rail__label", { hasText: "Body Systems" }).first().click();
  await page.waitForTimeout(600);
  await page.locator(".rnica-bodysystems__trigger", { hasText: "Respiratory" }).first().click();
  await page.waitForTimeout(600);
}

async function cardTitles(page) {
  return page.locator('[data-card-title]').evaluateAll((els) => els.map((e) => e.getAttribute("data-card-title")));
}

let failures = 0;
function check(label, cond) {
  console.log(`${cond ? "PASS" : "FAIL"}: ${label}`);
  if (!cond) failures++;
}

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1200 } });
  page.on("console", (msg) => { if (msg.type() === "error") console.log("BROWSER CONSOLE ERROR:", msg.text()); });
  page.on("pageerror", (err) => console.log("BROWSER PAGE ERROR:", err.message));
  await login(page);
  await setTheme(page, "light");

  const ALL_FIVE = ["Dyspnea / SOB", "Respiratory Assessment", "Cough / Secretions", "Oxygen Therapy", "Ventilator / Airway Support"];

  // --- State 1: "No Current Respiratory Concern" with preserved prior data ---
  await apiSaveRespiratory(page, { ...FULLY_DOCUMENTED_RESPIRATORY, respiratoryOverview: "No Current Respiratory Concern", clinicalStatusChange: "Stable / No Change" });
  await loadRespiratoryAccordion(page);
  let titles = await cardTitles(page);
  console.log("State 1 (No Current Concern) card titles:", titles);
  check("State 1: Overview card present", titles.includes("Respiratory Overview"));
  for (const t of ALL_FIVE) check(`State 1: ${t} hidden entirely (no duplicate/collapsed copy)`, !titles.includes(t));
  check("State 1: Clinical Status Change still shown", titles.includes("Clinical Status Change"));
  check("State 1: Notes still shown", titles.includes("Notes"));
  check("State 1: no more than 3 cards render (Overview + Clinical Status Change + Notes)", titles.length === 3);
  const bannerText = await page.locator(".rnica-cv-preserved-findings-banner").innerText().catch(() => "");
  console.log("State 1 banner text:", JSON.stringify(bannerText));
  check("State 1: single concise banner present pointing to Existing Review", /No current respiratory concern documented/i.test(bannerText) && /Existing Respiratory Findings Review/i.test(bannerText));
  check("State 1: banner is a single short line (no card-name enumeration paragraph)", bannerText.length < 220);
  await page.screenshot({ path: `${OUT_DIR}/state1-no-current-concern-desktop-light.png`, fullPage: true });

  // --- State 2: "Existing Respiratory Findings Review" -- must default to
  // a COMPACT REVIEW SUMMARY (not the 5-card editor). This replaces the
  // 2026-10-18 assertion that State 2 == State 3 (both show all 5 cards
  // fully) -- the owner rejected that as two nearly-identical workflows.
  // The one canonical editor is now reached only via "Edit Existing
  // Findings" or "New or Worsening Respiratory Findings". ---
  await apiSaveRespiratory(page, FULLY_DOCUMENTED_RESPIRATORY);
  await loadRespiratoryAccordion(page);
  titles = await cardTitles(page);
  console.log("State 2 (Existing Review, default/not editing) card titles:", titles);
  for (const t of ALL_FIVE) check(`State 2 (review mode): ${t} card NOT present (no duplicate editor)`, !titles.includes(t));
  check("State 2 (review mode): Respiratory Findings Review summary card present", titles.includes("Respiratory Findings Review"));
  check("State 2 (review mode): Clinical Status Change present", titles.includes("Clinical Status Change"));
  check("State 2 (review mode): Notes present", titles.includes("Notes"));
  check("State 2 (review mode): exactly 4 cards render (Overview + Findings Review + Clinical Status Change + Notes)", titles.length === 4);
  const reviewSummaryText = await page.locator('[data-card-title="Respiratory Findings Review"]').innerText();
  console.log("State 2 review summary text:", JSON.stringify(reviewSummaryText));
  check("State 2 (review mode): summary shows Dyspnea finding", /Dyspnea/i.test(reviewSummaryText) && /Moderate/i.test(reviewSummaryText));
  check("State 2 (review mode): summary shows Lung Sounds finding", /Lung Sounds/i.test(reviewSummaryText) && /Crackles/i.test(reviewSummaryText));
  check("State 2 (review mode): summary shows Oxygen finding", /Oxygen/i.test(reviewSummaryText) && /2 L\/min/i.test(reviewSummaryText));
  check("State 2 (review mode): summary shows Clinical Status", /Clinical Status/i.test(reviewSummaryText) && /Declining/i.test(reviewSummaryText));
  check("State 2 (review mode): Edit Existing Findings action present", /Edit Existing Findings/i.test(reviewSummaryText));
  await page.screenshot({ path: `${OUT_DIR}/state2-existing-review-desktop-light.png`, fullPage: true });

  // --- State 2b: click "Edit Existing Findings" -- must reach the SAME
  // canonical editor (identical 5 cards) as New or Worsening, fully, with
  // no per-field filtering, plus a reversible "Back to Review" action. ---
  await page.getByRole("button", { name: /Edit Existing Findings/i }).click();
  await page.waitForTimeout(400);
  titles = await cardTitles(page);
  console.log("State 2b (Existing Review, editing) card titles:", titles);
  for (const t of ALL_FIVE) check(`State 2b (editing): ${t} card present (exactly once)`, titles.filter((x) => x === t).length === 1);
  check("State 2b (editing): Findings Review summary card no longer present", !titles.includes("Respiratory Findings Review"));
  const dyspneaText = await page.locator('[data-card-title="Dyspnea / SOB"]').innerText();
  check("State 2b (editing): SOB Severity visible", /SOB SEVERITY/i.test(dyspneaText));
  check("State 2b (editing): Exertion Level visible", /EXERTION LEVEL/i.test(dyspneaText));
  check("State 2b (editing): Screening date field visible (no longer filtered)", /SOB SCREENING DATE/i.test(dyspneaText));
  check("State 2b (editing): Back to Review action visible", /Back to Review/i.test(dyspneaText));
  const respAssessText = await page.locator('[data-card-title="Respiratory Assessment"]').innerText();
  check("State 2b (editing): Lung Sounds visible", /LUNG SOUNDS/i.test(respAssessText));
  check("State 2b (editing): Respiration Pattern visible", /RESPIRATION PATTERN/i.test(respAssessText));
  const ventText = await page.locator('[data-card-title="Ventilator / Airway Support"]').innerText();
  check("State 2b (editing): Ventilator Type and Settings visible", /VENTILATOR TYPE AND SETTINGS/i.test(ventText));
  await page.screenshot({ path: `${OUT_DIR}/state2b-existing-review-editing-desktop-light.png`, fullPage: true });

  // --- State 2c: click "Back to Review" -- must return to the compact
  // summary, proving the toggle is reversible without leaving the section. ---
  await page.getByRole("button", { name: /Back to Review/i }).click();
  await page.waitForTimeout(400);
  titles = await cardTitles(page);
  console.log("State 2c (back to review) card titles:", titles);
  check("State 2c (back to review): Findings Review summary card present again", titles.includes("Respiratory Findings Review"));
  for (const t of ALL_FIVE) check(`State 2c (back to review): ${t} card NOT present`, !titles.includes(t));

  // --- State 2d: explicitly Save, then re-fetch via a fresh API call
  // (bypassing React state entirely) -- proves the edit-mode flag was
  // really persisted back to false, not just reset in local component
  // state, so "Existing Respiratory Findings Review" always re-opens on
  // the review summary after a real reload/new session. ---
  await page.getByRole("button", { name: /^Save assessment$/i }).click();
  await page.waitForTimeout(800);
  const afterBackToReview = await getRespiratory(page);
  console.log("respiratoryExistingFindingsEditMode after Back to Review + Save:", afterBackToReview.respiratoryExistingFindingsEditMode);
  check("State 2d: respiratoryExistingFindingsEditMode persisted back to false", afterBackToReview.respiratoryExistingFindingsEditMode === false);
  await loadRespiratoryAccordion(page);
  titles = await cardTitles(page);
  check("State 2d (fresh reload): Findings Review summary card present (edit mode did not persist as a stale open editor)", titles.includes("Respiratory Findings Review"));

  // --- State 3: "New or Worsening Respiratory Findings" -- same canonical
  // card set as State 2's editor, no duplicate second copy of the cards. ---
  await apiSaveRespiratory(page, { ...FULLY_DOCUMENTED_RESPIRATORY, respiratoryOverview: "New or Worsening Respiratory Findings" });
  await loadRespiratoryAccordion(page);
  titles = await cardTitles(page);
  console.log("State 3 (New or Worsening) card titles:", titles);
  for (const t of ALL_FIVE) check(`State 3: ${t} card present (exactly once)`, titles.filter((x) => x === t).length === 1);
  check("State 3: total card count matches State 2 (no duplication)", titles.length === 8);
  await page.screenshot({ path: `${OUT_DIR}/state3-new-or-worsening-desktop-light.png`, fullPage: true });

  // --- State 4: "Unable to Assess" -- only reason/other + Clinical Status
  // Change + Notes; 5 clinical cards hidden. ---
  await apiSaveRespiratory(page, { ...FULLY_DOCUMENTED_RESPIRATORY, respiratoryOverview: "Unable to Assess", respiratoryUnableToAssessReason: "Patient unresponsive" });
  await loadRespiratoryAccordion(page);
  titles = await cardTitles(page);
  console.log("State 4 (Unable to Assess) card titles:", titles);
  for (const t of ALL_FIVE) check(`State 4: ${t} hidden`, !titles.includes(t));
  check("State 4: Clinical Status Change still shown", titles.includes("Clinical Status Change"));
  check("State 4: Notes still shown", titles.includes("Notes"));
  check("State 4: exactly 3 cards render (Overview + Clinical Status Change + Notes)", titles.length === 3);
  await page.screenshot({ path: `${OUT_DIR}/state4-unable-to-assess-desktop-light.png`, fullPage: true });

  // --- Legacy checkbox audit: the 7 converted fields must no longer
  // render as <input type="checkbox">; they must render as booleanPill
  // chip buttons instead. ---
  await apiSaveRespiratory(page, { ...FULLY_DOCUMENTED_RESPIRATORY, respiratoryOverview: "New or Worsening Respiratory Findings" });
  await loadRespiratoryAccordion(page);
  const respiratorySectionCheckboxCount = await page.locator('[data-card-title="Dyspnea / SOB"] input[type="checkbox"], [data-card-title="Oxygen Therapy"] input[type="checkbox"], [data-card-title="Ventilator / Airway Support"] input[type="checkbox"]').count();
  check("Legacy checkbox audit: no <input type=checkbox> remains in converted Respiratory fields", respiratorySectionCheckboxCount === 0);
  const pillCount = await page.locator('[data-card-title="Dyspnea / SOB"] button[aria-pressed], [data-card-title="Oxygen Therapy"] button[aria-pressed], [data-card-title="Ventilator / Airway Support"] button[aria-pressed]').count();
  console.log("Boolean pill elements found in converted cards:", pillCount);
  check("Legacy checkbox audit: booleanPill buttons render for the 7 converted fields (>=7)", pillCount >= 7);

  // --- Four-mode visual verification: Desktop Dark + Mobile Light/Dark,
  // of the NEW "Existing Respiratory Findings Review" summary card
  // specifically (the part that changed this session) -- not just the
  // pre-existing full editor. ---
  await apiSaveRespiratory(page, { ...FULLY_DOCUMENTED_RESPIRATORY, respiratoryOverview: "Existing Respiratory Findings Review" });
  await setTheme(page, "dark");
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForTimeout(800);
  await page.locator(".rnica-rail__label", { hasText: "Body Systems" }).first().click();
  await page.waitForTimeout(600);
  await page.locator(".rnica-bodysystems__trigger", { hasText: "Respiratory" }).first().click();
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${OUT_DIR}/state2-existing-review-desktop-dark.png`, fullPage: true });
  check("Desktop dark: Findings Review summary card present", (await cardTitles(page)).includes("Respiratory Findings Review"));

  const mobilePage = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await login(mobilePage);
  await setTheme(mobilePage, "light");
  await mobilePage.reload({ waitUntil: "networkidle" });
  await mobilePage.waitForTimeout(600);
  await loadRespiratoryAccordionMobile(mobilePage);
  await mobilePage.screenshot({ path: `${OUT_DIR}/state2-existing-review-mobile-light.png`, fullPage: true });
  check("Mobile light: Findings Review summary card present", (await cardTitles(mobilePage)).includes("Respiratory Findings Review"));
  await setTheme(mobilePage, "dark");
  await mobilePage.reload({ waitUntil: "networkidle" });
  await mobilePage.waitForTimeout(800);
  await mobilePage.locator(".rnica-screen__mobile-nav-trigger", { hasText: "Workflow" }).first().click();
  await mobilePage.waitForTimeout(400);
  await mobilePage.locator(".rnica-rail-sheet .rnica-rail__label", { hasText: "Body Systems" }).first().click();
  await mobilePage.waitForTimeout(600);
  await mobilePage.locator(".rnica-bodysystems__trigger", { hasText: "Respiratory" }).first().click();
  await mobilePage.waitForTimeout(600);
  await mobilePage.screenshot({ path: `${OUT_DIR}/state2-existing-review-mobile-dark.png`, fullPage: true });
  check("Mobile dark: Findings Review summary card present", (await cardTitles(mobilePage)).includes("Respiratory Findings Review"));
  await mobilePage.close();

  // --- Restore true baseline and independently re-verify ---
  const restoreStatus = await apiSaveRespiratory(page, BASELINE_RESPIRATORY);
  console.log("Restore status:", restoreStatus);
  await browser.close();

  const browser2 = await chromium.launch();
  const page2 = await browser2.newPage();
  await login(page2);
  const restored = await getRespiratory(page2);
  console.log("Independently re-verified restored respiratory data:\n", JSON.stringify(restored, null, 2));
  const canonicalize = (v) => (v && typeof v === "object" && !Array.isArray(v))
    ? JSON.stringify(Object.keys(v).sort().reduce((acc, k) => { acc[k] = canonicalize(v[k]); return acc; }, {}))
    : JSON.stringify(v);
  const matches = canonicalize(restored) === canonicalize(BASELINE_RESPIRATORY);
  check("Baseline independently re-verified as fully restored (key-order-insensitive)", matches);
  await browser2.close();

  console.log(failures === 0 ? "\nALL CHECKS PASSED" : `\n${failures} CHECK(S) FAILED`);
  process.exitCode = failures === 0 ? 0 : 1;
}
main().catch((e) => { console.error(e); process.exitCode = 1; });
