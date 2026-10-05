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

async function apiSaveRespiratory(page, respiratory, visitDate) {
  return page.evaluate(async ({ assessmentId, respiratory, visitDate }) => {
    const token = localStorage.getItem("sns-hospice-solutions-access-token");
    const getRes = await fetch(`/visits/rnica/${assessmentId}`, { credentials: "include", headers: { Authorization: `Bearer ${token}` } });
    const full = await getRes.json();
    const newFormData = {
      ...full.formData,
      respiratory,
      visitMeta: visitDate !== undefined ? { ...full.formData.visitMeta, visitDate } : full.formData.visitMeta,
    };
    const putRes = await fetch(`/visits/rnica/${assessmentId}`, {
      method: "PUT", credentials: "include",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ formData: newFormData, fieldProvenance: full.fieldProvenance || [] }),
    });
    return putRes.status;
  }, { assessmentId: ASSESSMENT_ID, respiratory, visitDate });
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

async function loadRespiratoryAccordion(page) {
  await page.goto(`${BASE_URL}/nursing-assessment`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.locator(".rnica-rail__label", { hasText: "Body Systems" }).first().click();
  await page.waitForTimeout(600);
  await page.locator(".rnica-bodysystems__trigger", { hasText: "Respiratory" }).first().click();
  await page.waitForTimeout(600);
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

  const full = await apiGetFull(page);
  console.log("visitMeta.visitDate =", full.formData?.visitMeta?.visitDate);
  console.log("mode (inferred from existing assessment) soc_date check skipped (facesheet is separate endpoint)");

  // Reset respiratory: blank dates, booleans off. Seed a known visit date
  // (the test patient/assessment has neither a facesheet SOC date nor a
  // visit date set, so without this there is genuinely no known date for
  // the effect to use -- this isolates the auto-fill behavior itself.
  await apiSaveRespiratory(page, {
    notes: "", coughType: "", lungSounds: [],
    ventilator: { tracheostomySize: "", tracheostomyType: "", longTermVentilator: false, shortTermVentilator: false, ventilatorTypeAndSettings: "" },
    sobSeverity: "Moderate", respirations: [], exertionLevel: "",
    oxygenTherapy: { type: "", inUse: false, satOnO2: "", onRoomAir: false, hoursPerDay: "", deliveryMode: "", litersPerMinute: "" },
    screeningDate: "", treatmentDate: "", sputumCharacter: "",
    treatmentDeclined: false, treatmentInitiated: false,
    clinicalStatusChange: "", shortnessOfBreathScreened: false,
    respiratoryOverview: "New or Worsening Respiratory Findings",
    respiratoryUnableToAssessReason: "", respiratoryUnableToAssessOther: "",
  }, "2026-10-01");

  await loadRespiratoryAccordion(page);

  const beforeToggle = await getRespiratory(page);
  console.log("Before toggle -> full respiratory:", JSON.stringify(beforeToggle));
  const visitDateCheck = await apiGetFull(page);
  console.log("visitMeta.visitDate after seeding:", visitDateCheck.formData?.visitMeta?.visitDate);

  // Toggle "Screened for shortness of breath" ON via UI.
  const screenBtn = page.getByRole("button", { name: /Screened for shortness of breath/i }).first();
  console.log("screen button count:", await screenBtn.count());
  await screenBtn.click();
  await page.waitForTimeout(400);
  await page.getByRole("button", { name: /^Save assessment$/i }).click();
  await page.waitForTimeout(900);

  const afterScreenToggle = await getRespiratory(page);
  console.log("After screening toggle ON -> full respiratory:", JSON.stringify(afterScreenToggle));
  check("screeningDate auto-filled to the known visit date (2026-10-01) after toggling screened ON", afterScreenToggle.screeningDate === "2026-10-01");
  check("treatmentDate still blank (treatmentInitiated still false)", !afterScreenToggle.treatmentDate);

  // Toggle "Treatment for shortness of breath initiated" ON via UI.
  await page.getByRole("button", { name: /Treatment for shortness of breath initiated/i }).first().click();
  await page.waitForTimeout(400);
  await page.getByRole("button", { name: /^Save assessment$/i }).click();
  await page.waitForTimeout(900);
  const afterTreatToggle = await getRespiratory(page);
  console.log("After treatment toggle ON -> treatmentDate:", afterTreatToggle.treatmentDate);
  check("treatmentDate auto-filled to the known visit date (2026-10-01) after toggling treatment-initiated ON", afterTreatToggle.treatmentDate === "2026-10-01");

  // Manually override the screening date and confirm the effect does not
  // stomp it back.
  const dateInput = page.locator('input[type="date"]').first();
  await dateInput.fill("2020-01-01");
  await page.waitForTimeout(400);
  await page.getByRole("button", { name: /^Save assessment$/i }).click();
  await page.waitForTimeout(900);
  const afterManualOverride = await getRespiratory(page);
  console.log("After manual override -> screeningDate:", afterManualOverride.screeningDate);
  check("manual override of screeningDate persists (not overwritten by auto-fill)", afterManualOverride.screeningDate === "2020-01-01");

  console.log(failures === 0 ? "\nALL CHECKS PASSED" : `\n${failures} CHECK(S) FAILED`);

  // Restore baseline so this test doesn't leave the shared assessment mutated.
  await apiSaveRespiratory(page, {
    notes: "", coughType: "", lungSounds: [],
    ventilator: { tracheostomySize: "", tracheostomyType: "", longTermVentilator: false, shortTermVentilator: false, ventilatorTypeAndSettings: "" },
    sobSeverity: "Moderate", respirations: [], exertionLevel: "",
    oxygenTherapy: { type: "", inUse: false, satOnO2: "", onRoomAir: false, hoursPerDay: "", deliveryMode: "", litersPerMinute: "" },
    screeningDate: "", treatmentDate: "", sputumCharacter: "",
    treatmentDeclined: false, treatmentInitiated: false,
    clinicalStatusChange: "", shortnessOfBreathScreened: false,
    respiratoryOverview: "", respiratoryUnableToAssessReason: "", respiratoryUnableToAssessOther: "",
  }, "");

  await browser.close();
  process.exit(failures === 0 ? 0 : 1);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
