// One-off visual confirmation for Density Pass 2: Assessment Context /
// Comparison to Prior shared-row + subtle-border fix. Analysis-only.
import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const BASE_URL = "http://localhost:5173";
const LOGIN_EMAIL = "rsuason@loveandfaithhospice.com";
const LOGIN_PASSWORD = "LoveFaithHospice2026!";
const PATIENT_ID = "53fe69e1-fcd5-4b49-8203-9b890b18b7d6";
const OUT_DIR = path.resolve("scripts", "respiratory-audit-output");
fs.mkdirSync(OUT_DIR, { recursive: true });

async function main() {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await page.getByLabel(/email/i).fill(LOGIN_EMAIL);
  await page.getByLabel(/^password/i).fill(LOGIN_PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForTimeout(2000);

  await page.goto(`${BASE_URL}/chart/${PATIENT_ID}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);

  const navBtn = page.getByRole("button", { name: "Patient chart navigation" });
  if (await navBtn.isVisible().catch(() => false)) {
    await navBtn.click();
    await page.waitForTimeout(300);
  }
  await page.getByText("Nursing Assessment", { exact: true }).first().click();
  await page.waitForTimeout(1200);

  await page.getByRole("button", { name: "Body Systems" }).first().click({ timeout: 10000 });
  await page.waitForTimeout(1000);

  // Retry the Respiratory trigger up to 3 times in case of the known
  // flaky-accordion timing issue noted during Pass 1 verification.
  let found = false;
  for (let i = 0; i < 3 && !found; i++) {
    const respTrigger = page.getByRole("button", { name: /Respiratory/ }).first();
    const expandedAttr = await respTrigger.getAttribute("aria-expanded").catch(() => null);
    if (expandedAttr !== "true") {
      await respTrigger.click({ timeout: 10000 }).catch(() => {});
      await page.waitForTimeout(1000);
    }
    found = await page
      .waitForSelector('[data-testid="respiratory-assessment-context-section"]', { timeout: 4000 })
      .then(() => true)
      .catch(() => false);
  }

  if (!found) {
    console.error("Could not locate respiratory-assessment-context-section after retries.");
    await page.screenshot({ path: path.join(OUT_DIR, "pass2-visual-check-FAILED.png"), fullPage: true });
    await browser.close();
    process.exitCode = 1;
    return;
  }

  const section = page.locator('[data-testid="respiratory-assessment-context-section"]');
  await section.scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  await section.screenshot({ path: path.join(OUT_DIR, "pass2-assessment-context-section.png") });

  const lungSounds = page.locator('[data-testid="respiratory-field-respiratory_lung_sounds"]');
  if (await lungSounds.count()) {
    await lungSounds.scrollIntoViewIfNeeded();
    await page.waitForTimeout(200);
    await lungSounds.screenshot({ path: path.join(OUT_DIR, "pass2-lung-sounds.png") });
  }
  const pattern = page.locator('[data-testid="respiratory-field-respiratory_respiration_pattern"]');
  if (await pattern.count()) {
    await pattern.scrollIntoViewIfNeeded();
    await page.waitForTimeout(200);
    await pattern.screenshot({ path: path.join(OUT_DIR, "pass2-respiratory-pattern.png") });
  }

  console.log("Saved pass2 field screenshots.");
  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
