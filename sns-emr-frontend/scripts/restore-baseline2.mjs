import { chromium } from "@playwright/test";

const BASE_URL = "http://localhost:5173";
const LOGIN_EMAIL = "rsuason@loveandfaithhospice.com";
const LOGIN_PASSWORD = "LoveFaithHospice2026!";
const PATIENT_ID = "53fe69e1-fcd5-4b49-8203-9b890b18b7d6";
const ASSESSMENT_ID = "84234eb9-bfb9-4222-8287-4f4e8475c593";

async function apiFetchCardio(page) {
  return page.evaluate(async (assessmentId) => {
    const token = localStorage.getItem("sns-hospice-solutions-access-token");
    const res = await fetch(`/visits/rnica/${assessmentId}`, {
      credentials: "include",
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    return data?.formData?.cardiovascular;
  }, ASSESSMENT_ID);
}

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await page.getByLabel(/email/i).fill(LOGIN_EMAIL);
  await page.getByLabel(/^password/i).fill(LOGIN_PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForTimeout(2000);

  await page.evaluate((patientId) => {
    window.sessionStorage.setItem("sns-hospice-solutions-active-patient", patientId);
  }, PATIENT_ID);
  await page.goto(`${BASE_URL}/nursing-assessment`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.locator(".rnica-rail__label", { hasText: "Body Systems" }).first().click();
  await page.waitForTimeout(600);
  await page.locator(".rnica-bodysystems__trigger", { hasText: "Cardiovascular" }).first().click();
  await page.waitForTimeout(600);

  let state = await apiFetchCardio(page);
  console.log("STATE AT START:", state.cardiovascularOverview, "|", state.cardiovascularUnableToAssessReason);

  for (let attempt = 1; attempt <= 4; attempt++) {
    if (state.cardiovascularOverview === "Unable to Assess" && state.cardiovascularUnableToAssessReason === "Patient unresponsive") {
      console.log("Baseline reached.");
      break;
    }
    console.log(`Attempt ${attempt}: clicking Unable to Assess + Patient unresponsive...`);
    if (state.cardiovascularOverview !== "Unable to Assess") {
      await page.getByText("Unable to Assess", { exact: true }).first().click();
      await page.waitForTimeout(900);
    }
    await page.getByText("Patient unresponsive", { exact: true }).first().click();
    await page.waitForTimeout(900);
    await page.getByRole("button", { name: /Save assessment/i }).click();
    await page.waitForTimeout(2500);
    state = await apiFetchCardio(page);
    console.log(`After attempt ${attempt}:`, state.cardiovascularOverview, "|", state.cardiovascularUnableToAssessReason);
  }

  await page.locator(".rnica-bodysystems__trigger", { hasText: "Cardiovascular" }).first().click();
  await page.waitForTimeout(600);
  await page.getByText("New or Worsening Cardiovascular Findings", { exact: false }).first().click();
  await page.waitForTimeout(900);
  const probe = await page.evaluate(() => {
    const cardTitles = Array.from(document.querySelectorAll("[data-card-title]")).map((e) => e.getAttribute("data-card-title"));
    const sections = Array.from(document.querySelectorAll("[data-section]")).map((e) => e.getAttribute("data-section"));
    return { cardTitles, sections };
  });
  console.log("PROBE:", JSON.stringify(probe, null, 2));
  await page.screenshot({ path: "scripts/cardio-audit-output/debug-probe.png", fullPage: true });
  await browser.close();
}
main().catch((e) => { console.error(e); process.exitCode = 1; });
