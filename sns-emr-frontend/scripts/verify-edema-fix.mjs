import { chromium } from "@playwright/test";

const BASE_URL = "http://localhost:5173";
const LOGIN_EMAIL = "rsuason@loveandfaithhospice.com";
const LOGIN_PASSWORD = "LoveFaithHospice2026!";
const PATIENT_ID = "53fe69e1-fcd5-4b49-8203-9b890b18b7d6";
const ASSESSMENT_ID = "84234eb9-bfb9-4222-8287-4f4e8475c593";

const BASELINE = {
  cardiovascularOverview: "Unable to Assess", cardiovascularUnableToAssessReason: "Patient unresponsive",
  cardiovascularUnableToAssessOther: "", cardiovascularFindingsConfirmedThisVisit: false,
  pulseRhythm: "", pulseRate: "", pulseStrength: "", pulseSites: [], pulseQuality: "",
  skinColor: "", skinColorOther: "", heartSounds: "", heartSoundsOther: "",
  coolExtremities: false, varicoseVeins: false, stasisUlcer: false,
  jvd: "", peripheralCirculation: "", peripheralCirculationOther: "",
  edema: { present: "No", location: [], severity: "", pitting: "" },
  chestPain: { present: "", type: "", frequency: "" },
  bpStatus: "", bpSymptoms: [], orthostaticFinding: "", dizziness: "", fatigue: "", syncope: "",
  cardiacDyspnea: false, heartFailurePresent: false, heartFailureType: [],
  pacemaker: false, internalDefibrillator: false, centralVenousLine: false,
  clinicalStatusChange: "Initial Assessment", notes: "",
};

async function apiSaveCardio(page, cardiovascular) {
  return page.evaluate(async ({ assessmentId, cardiovascular }) => {
    const token = localStorage.getItem("sns-hospice-solutions-access-token");
    const getRes = await fetch(`/visits/rnica/${assessmentId}`, { credentials: "include", headers: { Authorization: `Bearer ${token}` } });
    const full = await getRes.json();
    const newFormData = { ...full.formData, cardiovascular };
    const putRes = await fetch(`/visits/rnica/${assessmentId}`, {
      method: "PUT", credentials: "include",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ formData: newFormData, fieldProvenance: full.fieldProvenance || [] }),
    });
    return putRes.status;
  }, { assessmentId: ASSESSMENT_ID, cardiovascular });
}

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1200 } });
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await page.getByLabel(/email/i).fill(LOGIN_EMAIL);
  await page.getByLabel(/^password/i).fill(LOGIN_PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForTimeout(2000);

  // Set up: Existing Review path, edema.present = Yes, but location/severity/pitting
  // are BLANK -- exactly the trap scenario the user reported (just flipped Yes,
  // nothing characterized yet).
  await apiSaveCardio(page, {
    ...BASELINE,
    cardiovascularOverview: "Existing Cardiovascular Findings Review",
    cardiovascularUnableToAssessReason: "",
    edema: { present: "Yes", location: [], severity: "", pitting: "" },
  });

  await page.evaluate((patientId) => window.sessionStorage.setItem("sns-hospice-solutions-active-patient", patientId), PATIENT_ID);
  await page.goto(`${BASE_URL}/nursing-assessment`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  await page.locator(".rnica-rail__label", { hasText: "Body Systems" }).first().click();
  await page.waitForTimeout(700);
  await page.locator(".rnica-bodysystems__trigger", { hasText: "Cardiovascular" }).first().click();
  await page.waitForTimeout(700);

  const text = await page.locator('[data-card-title="Circulation & Perfusion"]').innerText();
  console.log("=== Circulation & Perfusion text dump ===\n", text);
  const hasLocation = /EDEMA LOCATION/i.test(text);
  const hasSeverity = /EDEMA SEVERITY/i.test(text);
  const hasType = /EDEMA TYPE/i.test(text);
  console.log(`\nEDEMA LOCATION header present: ${hasLocation}`);
  console.log(`EDEMA SEVERITY header present: ${hasSeverity}`);
  console.log(`EDEMA TYPE header present: ${hasType}`);

  const locator = page.locator('[data-card-title="Circulation & Perfusion"]');
  await locator.scrollIntoViewIfNeeded();
  await page.screenshot({ path: "scripts/cardio-audit-output/edema/06-fix-verification-blank-children.png", fullPage: true });

  // Restore baseline.
  const restoreStatus = await apiSaveCardio(page, BASELINE);
  console.log("Restore status:", restoreStatus);
  const verify = await page.evaluate(async (assessmentId) => {
    const token = localStorage.getItem("sns-hospice-solutions-access-token");
    const res = await fetch(`/visits/rnica/${assessmentId}`, { credentials: "include", headers: { Authorization: `Bearer ${token}` } });
    const full = await res.json();
    return full.formData.cardiovascular;
  }, ASSESSMENT_ID);
  console.log("Verified baseline after restore:\n", JSON.stringify(verify, null, 2));

  await browser.close();

  if (!hasLocation || !hasSeverity || !hasType) {
    console.error("\nFAIL: one or more edema child field groups did not render.");
    process.exitCode = 1;
  } else {
    console.log("\nPASS: Edema Location/Severity/Type all render immediately when Present flips to Yes, even with blank children.");
  }
}
main().catch((e) => { console.error(e); process.exitCode = 1; });
