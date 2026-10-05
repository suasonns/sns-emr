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
    return data?.formData?.cardiovascular ?? data;
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

  const current = await apiFetchCardio(page);
  console.log("CURRENT SERVER STATE BEFORE RESTORE:\n", JSON.stringify(current, null, 2));

  // Force back to the documented true baseline: Unable to Assess / Patient unresponsive.
  await page.getByText("Unable to Assess", { exact: true }).first().click();
  await page.waitForTimeout(600);
  await page.getByText("Patient unresponsive", { exact: true }).first().click();
  await page.waitForTimeout(600);

  // Force an explicit save (do not rely solely on debounced autosave before closing).
  await page.getByRole("button", { name: /Save assessment/i }).click();
  await page.waitForTimeout(2500);

  const afterRestore = await apiFetchCardio(page);
  console.log("SERVER STATE AFTER RESTORE ATTEMPT (same page, post explicit save):\n", JSON.stringify(afterRestore, null, 2));

  await page.screenshot({ path: "scripts/cardio-audit-output/debug-restore.png", fullPage: true });
  await browser.close();
}
main().catch((e) => { console.error(e); process.exitCode = 1; });
