import { chromium } from "@playwright/test";

const BASE_URL = process.env.VERIFY_BASE_URL || "http://localhost:5173";
const LOGIN_EMAIL = "rsuason@loveandfaithhospice.com";
const LOGIN_PASSWORD = "LoveFaithHospice2026!";
const PATIENT_ID = "53fe69e1-fcd5-4b49-8203-9b890b18b7d6";
const ASSESSMENT_ID = "84234eb9-bfb9-4222-8287-4f4e8475c593";

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
  currentInfections: ["Respiratory tract"],
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
  const trigger = page.locator(".rnica-bodysystems__trigger", { hasText: "Infection" }).first();
  await trigger.scrollIntoViewIfNeeded();
  await trigger.click();
  await page.waitForTimeout(700);
  const item = page.locator(".rnica-bodysystems__item", { has: page.locator(".rnica-bodysystems__trigger", { hasText: "Infection" }) }).first();
  await item.scrollIntoViewIfNeeded();
}

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1400 } });
  await login(page);

  await apiSaveInfection(page, { ...DOCUMENTED_INFECTION, infectionOverview: "No Current Infection Concern" });
  await loadInfectionAccordion(page);
  await page.screenshot({ path: "scripts/__screenshots__/infection-1-no-current-concern.png", fullPage: false });

  await apiSaveInfection(page, { ...DOCUMENTED_INFECTION, infectionOverview: "Existing Infection Findings Review", infectionExistingFindingsEditMode: false });
  await loadInfectionAccordion(page);
  await page.screenshot({ path: "scripts/__screenshots__/infection-2-existing-findings-review.png", fullPage: false });

  await apiSaveInfection(page, { ...DOCUMENTED_INFECTION, infectionOverview: "New or Worsening Infection Findings" });
  await loadInfectionAccordion(page);
  await page.screenshot({ path: "scripts/__screenshots__/infection-3-new-or-worsening.png", fullPage: false });

  await apiSaveInfection(page, { ...DOCUMENTED_INFECTION, infectionOverview: "Unable to Assess", infectionUnableToAssessReason: "Patient unresponsive" });
  await loadInfectionAccordion(page);
  await page.screenshot({ path: "scripts/__screenshots__/infection-4-unable-to-assess.png", fullPage: false });

  await apiSaveInfection(page, BASELINE_INFECTION);
  await browser.close();
  console.log("Screenshots captured.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
