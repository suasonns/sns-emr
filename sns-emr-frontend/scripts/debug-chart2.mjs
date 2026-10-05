import { chromium } from "@playwright/test";

const BASE_URL = "http://localhost:5173";
const LOGIN_EMAIL = "rsuason@loveandfaithhospice.com";
const LOGIN_PASSWORD = "LoveFaithHospice2026!";
const PATIENT_ID = "53fe69e1-fcd5-4b49-8203-9b890b18b7d6";

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await page.getByLabel(/email/i).fill(LOGIN_EMAIL);
  await page.getByLabel(/^password/i).fill(LOGIN_PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForTimeout(2000);
  console.log("URL after login:", page.url());

  await page.evaluate((patientId) => {
    window.sessionStorage.setItem("sns-hospice-solutions-active-patient", patientId);
  }, PATIENT_ID);

  await page.goto(`${BASE_URL}/nursing-assessment`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  console.log("URL:", page.url());
  const text1 = await page.evaluate(() => document.body.innerText.slice(0, 1500));
  console.log("BODY TEXT:\n", text1);

  // Try to find the Body Systems stage tab.
  const tabTexts = await page.evaluate(() => {
    const out = [];
    document.querySelectorAll("*").forEach((el) => {
      if (el.children.length === 0 && /Body Systems/i.test(el.textContent || "")) {
        out.push({ tag: el.tagName, cls: el.className, text: el.textContent.trim().slice(0, 40) });
      }
    });
    return out;
  });
  console.log("BODY SYSTEMS CANDIDATES:", JSON.stringify(tabTexts, null, 2));

  // Click the Body Systems stage rail tab, then the Cardiovascular accordion.
  await page.locator(".rnica-rail__label", { hasText: "Body Systems" }).first().click();
  await page.waitForTimeout(600);
  const cvCandidates = await page.evaluate(() => {
    const out = [];
    document.querySelectorAll("button, [role='button']").forEach((el) => {
      if (/Cardiovascular/i.test(el.textContent || "")) {
        out.push({ cls: el.className, text: el.textContent.trim().slice(0, 60) });
      }
    });
    return out;
  });
  console.log("CARDIOVASCULAR CANDIDATES:", JSON.stringify(cvCandidates, null, 2));
  await page.screenshot({ path: "scripts/cardio-audit-output/debug-bodysystems.png", fullPage: true });
  await browser.close();
}
main().catch((e) => { console.error(e); process.exitCode = 1; });
