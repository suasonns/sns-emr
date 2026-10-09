import { chromium } from "@playwright/test";

const BASE_URL = "http://localhost:5173";
const LOGIN_EMAIL = "rsuason@loveandfaithhospice.com";
const LOGIN_PASSWORD = "LoveFaithHospice2026!";
const PATIENT_ID = "53fe69e1-fcd5-4b49-8203-9b890b18b7d6";
const ASSESSMENT_ID = "84234eb9-bfb9-4222-8287-4f4e8475c593";

async function apiFetchFull(page) {
  return page.evaluate(async (assessmentId) => {
    const token = localStorage.getItem("sns-hospice-solutions-access-token");
    const res = await fetch(`/visits/rnica/${assessmentId}`, {
      credentials: "include",
      headers: { Authorization: `Bearer ${token}` },
    });
    return res.json();
  }, ASSESSMENT_ID);
}

async function apiSave(page, cardiovascular) {
  return page.evaluate(async ({ assessmentId, cardiovascular, full }) => {
    const token = localStorage.getItem("sns-hospice-solutions-access-token");
    const newFormData = { ...full.formData, cardiovascular };
    const res = await fetch(`/visits/rnica/${assessmentId}`, {
      method: "PATCH",
      credentials: "include",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ formData: newFormData }),
    });
    return res.status;
  }, { assessmentId: ASSESSMENT_ID, cardiovascular, full: await apiFetchFull(page) });
}

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await page.getByLabel(/email/i).fill(LOGIN_EMAIL);
  await page.getByLabel(/^password/i).fill(LOGIN_PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForTimeout(2000);

  const full = await apiFetchFull(page);
  console.log("CURRENT cardiovascular:", JSON.stringify(full.formData.cardiovascular, null, 2));

  await browser.close();
}
main().catch((e) => { console.error(e); process.exitCode = 1; });
