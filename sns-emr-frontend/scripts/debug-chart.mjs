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
  const errText = await page.evaluate(() => document.body.innerText.slice(0, 1000));
  console.log("POST-LOGIN BODY:\n", errText);
  await page.goto(`${BASE_URL}/chart/${PATIENT_ID}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  console.log("URL after chart nav:", page.url());
  await page.screenshot({ path: "scripts/cardio-audit-output/debug-chart.png", fullPage: true });
  const navCandidates = await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll("button, a, [role='tab'], [role='button']"));
    return els
      .map((e) => (e.innerText || "").trim())
      .filter((t) => t.length > 0 && t.length < 60)
      .slice(0, 80);
  });
  console.log("NAV CANDIDATES:\n", JSON.stringify(navCandidates, null, 2));
  const fullText = await page.evaluate(() => document.body.innerText);
  console.log("CONTAINS 'Nursing Assessment':", fullText.includes("Nursing Assessment"));
  console.log("CONTAINS 'RNICA':", fullText.toUpperCase().includes("RNICA"));
  console.log("CONTAINS 'Patient chart navigation':", fullText.includes("Patient chart navigation"));
  const ariaLabels = await page.evaluate(() => Array.from(document.querySelectorAll('[aria-label]')).map(e => e.getAttribute('aria-label')).filter(Boolean).slice(0,60));
  console.log("ARIA LABELS:", JSON.stringify(ariaLabels, null, 2));
  const naInfo = await page.evaluate(() => {
    const matches = [];
    document.querySelectorAll("*").forEach((el) => {
      if (el.children.length === 0 && el.textContent && /^7\s*Body Systems$/i.test(el.textContent.trim())) {
        matches.push({ tag: el.tagName, cls: el.className, text: el.textContent.trim() });
      }
    });
    return matches;
  });
  console.log("BODY SYSTEMS TAB MATCHES:", JSON.stringify(naInfo, null, 2));
  await page.getByText("Nursing Assessment", { exact: true }).first().click();
  await page.waitForTimeout(800);
  const afterNursingClick = await page.evaluate(() => document.body.innerText.slice(0, 2000));
  console.log("AFTER NURSING ASSESSMENT CLICK:\n", afterNursingClick);
  await page.getByText("Open", { exact: true }).first().click();
  await page.waitForTimeout(1200);
  console.log("URL after Open:", page.url());
  const afterOpenClick = await page.evaluate(() => document.body.innerText.slice(0, 2000));
  console.log("AFTER OPEN CLICK:\n", afterOpenClick);
  await browser.close();
}
main().catch((e) => { console.error(e); process.exitCode = 1; });
