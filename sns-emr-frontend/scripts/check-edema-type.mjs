import { chromium } from "@playwright/test";

const BASE_URL = "http://localhost:5173";
const LOGIN_EMAIL = "rsuason@loveandfaithhospice.com";
const LOGIN_PASSWORD = "LoveFaithHospice2026!";
const PATIENT_ID = "53fe69e1-fcd5-4b49-8203-9b890b18b7d6";
const ASSESSMENT_ID = "84234eb9-bfb9-4222-8287-4f4e8475c593";

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

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1400 } });
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await page.getByLabel(/email/i).fill(LOGIN_EMAIL);
  await page.getByLabel(/^password/i).fill(LOGIN_PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForTimeout(2000);

  await apiSaveCardio(page, {
    ...BASELINE,
    cardiovascularOverview: "Existing Cardiovascular Findings Review",
    cardiovascularUnableToAssessReason: "",
    edema: { present: "Yes", location: ["Bilateral lower extremities"], severity: "3+", pitting: "Pitting" },
  });

  await page.evaluate((patientId) => window.sessionStorage.setItem("sns-hospice-solutions-active-patient", patientId), PATIENT_ID);
  await page.goto(`${BASE_URL}/nursing-assessment`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  await page.locator(".rnica-rail__label", { hasText: "Body Systems" }).first().click();
  await page.waitForTimeout(700);
  await page.locator(".rnica-bodysystems__trigger", { hasText: "Cardiovascular" }).first().click();
  await page.waitForTimeout(700);

  const typeInfo = await page.evaluate(() => {
    const card = document.querySelector('[data-card-title="Circulation & Perfusion"]');
    if (!card) return "CARD NOT FOUND";
    const labels = Array.from(card.querySelectorAll("*")).filter((el) => el.children.length === 0 && /edema type/i.test(el.textContent || ""));
    if (labels.length === 0) return "EDEMA TYPE LABEL NOT FOUND";
    const label = labels[0];
    let container = label;
    for (let i = 0; i < 4 && container; i++) container = container.parentElement;
    return container ? container.innerHTML.slice(0, 2000) : "NO CONTAINER";
  });
  console.log("EDEMA TYPE region HTML:\n", typeInfo);

  const locator = page.locator('[data-card-title="Circulation & Perfusion"]');
  await locator.scrollIntoViewIfNeeded();
  await page.screenshot({ path: "scripts/cardio-audit-output/edema/05-edema-type-check.png", fullPage: true });

  await apiSaveCardio(page, BASELINE);
  await browser.close();
}
main().catch((e) => { console.error(e); process.exitCode = 1; });
