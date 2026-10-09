import { chromium } from "@playwright/test";

const BASE_URL = "http://localhost:5173";
const LOGIN_EMAIL = "rsuason@loveandfaithhospice.com";
const LOGIN_PASSWORD = "LoveFaithHospice2026!";
const ASSESSMENT_ID = "84234eb9-bfb9-4222-8287-4f4e8475c593";

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await page.getByLabel(/email/i).fill(LOGIN_EMAIL);
  await page.getByLabel(/^password/i).fill(LOGIN_PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForTimeout(2000);

  const cardio = await page.evaluate(async (assessmentId) => {
    const token = localStorage.getItem("sns-hospice-solutions-access-token");
    const res = await fetch(`/visits/rnica/${assessmentId}`, {
      credentials: "include",
      headers: { Authorization: `Bearer ${token}` },
    });
    const full = await res.json();
    return full.formData.cardiovascular;
  }, ASSESSMENT_ID);

  console.log(JSON.stringify(cardio, null, 2));
  await browser.close();
}
main().catch((e) => { console.error(e); process.exitCode = 1; });
