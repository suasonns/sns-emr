import { chromium } from "@playwright/test";
import fs from "node:fs";

const BASE_URL = "http://localhost:5173";
const LOGIN_EMAIL = "rsuason@loveandfaithhospice.com";
const LOGIN_PASSWORD = "LoveFaithHospice2026!";
const PATIENT_ID = "53fe69e1-fcd5-4b49-8203-9b890b18b7d6";
const ASSESSMENT_ID = "84234eb9-bfb9-4222-8287-4f4e8475c593";
const VIEWPORTS = [
  { name: "1440x900", width: 1440, height: 900 },
  { name: "1366x768", width: 1366, height: 768 },
  { name: "1024x768", width: 1024, height: 768 },
];

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

async function loginAndOpenCardio(page) {
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
}

async function main() {
  fs.mkdirSync("scripts/cardio-audit-output/final", { recursive: true });
  const browser = await chromium.launch();
  const results = [];

  for (const vp of VIEWPORTS) {
    const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
    await loginAndOpenCardio(page);

    // Expose the full field set for this real viewport.
    await page.getByText("New or Worsening Cardiovascular Findings", { exact: false }).first().click();
    await page.waitForTimeout(900);

    const measurement = await page.evaluate(() => {
      function describe(el) {
        if (!el) return null;
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        return { width: Math.round(r.width), gridColumn: cs.gridColumn };
      }
      const circCard = document.querySelector('[data-section="cardiovascular"] [data-card-title="Circulation & Perfusion"]');
      const symCard = document.querySelector('[data-section="cardiovascular"] [data-card-title="Cardiovascular Symptoms"]');
      const fieldsGrid = circCard ? circCard.querySelector(".rnica-bodysystem-workspace__fields") : null;
      const fieldsCs = fieldsGrid ? getComputedStyle(fieldsGrid) : null;
      return {
        circCard: describe(circCard),
        symCard: describe(symCard),
        circFieldsGridTemplateColumns: fieldsCs ? fieldsCs.gridTemplateColumns : null,
      };
    });

    await page.screenshot({ path: `scripts/cardio-audit-output/final/cardio-${vp.name}.png`, fullPage: true });

    // Restore baseline immediately, in-page, before moving to next viewport.
    let state = await apiFetchCardio(page);
    for (let attempt = 1; attempt <= 4; attempt++) {
      if (state.cardiovascularOverview === "Unable to Assess" && state.cardiovascularUnableToAssessReason === "Patient unresponsive") break;
      if (state.cardiovascularOverview !== "Unable to Assess") {
        await page.getByText("Unable to Assess", { exact: true }).first().click();
        await page.waitForTimeout(900);
      }
      await page.getByText("Patient unresponsive", { exact: true }).first().click();
      await page.waitForTimeout(900);
      await page.getByRole("button", { name: /Save assessment/i }).click();
      await page.waitForTimeout(2500);
      state = await apiFetchCardio(page);
    }

    results.push({ viewport: vp.name, measurement, restoredState: { overview: state.cardiovascularOverview, reason: state.cardiovascularUnableToAssessReason } });
    await page.close();
  }

  await browser.close();
  console.log(JSON.stringify(results, null, 2));
}
main().catch((e) => { console.error(e); process.exitCode = 1; });
