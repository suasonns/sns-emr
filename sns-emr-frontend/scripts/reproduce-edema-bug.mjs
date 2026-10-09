import { chromium } from "@playwright/test";
import fs from "node:fs";

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

async function openCardio(page) {
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

async function save(page) {
  await page.getByRole("button", { name: /Save assessment/i }).click();
  await page.waitForTimeout(2000);
}

async function main() {
  fs.mkdirSync("scripts/cardio-audit-output/edema", { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await page.getByLabel(/email/i).fill(LOGIN_EMAIL);
  await page.getByLabel(/^password/i).fill(LOGIN_PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForTimeout(2000);

  await openCardio(page);

  // Step 1: "New or Worsening" path -- populate edema data.
  await page.getByText("New or Worsening Cardiovascular Findings", { exact: false }).first().click();
  await page.waitForTimeout(900);
  await page.screenshot({ path: "scripts/cardio-audit-output/edema/01-new-or-worsening-before-edema.png", fullPage: true });

  // Edema Present = Yes -- scope strictly to the field group containing
  // the "Edema Present" label so we never hit JVD's or Chest Pain's own
  // Yes/No/Not Assessed triple (DOM order != visual column order here).
  const edemaPresentGroup = page.locator('[data-card-title="Circulation & Perfusion"] :text-is("Edema Present")').locator("xpath=ancestor::*[contains(@class,'rnica-bodysystem-workspace__fields') or self::fieldset][1]");
  const edemaPresentField = page.locator('[data-card-title="Circulation & Perfusion"]').locator("div", { has: page.getByText("Edema Present", { exact: true }) }).first();
  await page.getByText("Edema Present", { exact: true }).first().scrollIntoViewIfNeeded();
  // Click the "Yes" button that is a sibling within the same field block
  // as the "Edema Present" label (walk up to a reasonably-scoped
  // container, then query within it).
  const edemaBlock = page.locator('[data-card-title="Circulation & Perfusion"]').locator("xpath=.//*[normalize-space(text())='Edema Present']/ancestor::div[position()<=4][1]");
  await edemaBlock.getByText("Yes", { exact: true }).first().click();
  await page.waitForTimeout(700);
  await page.screenshot({ path: "scripts/cardio-audit-output/edema/02-new-or-worsening-edema-yes.png", fullPage: true });

  const locationBlock = page.locator('[data-card-title="Circulation & Perfusion"]').locator("xpath=.//*[normalize-space(text())='Edema Location']/ancestor::div[position()<=4][1]");
  await locationBlock.getByText("Bilateral lower extremities", { exact: true }).first().click();
  await page.waitForTimeout(400);
  const severityBlock = page.locator('[data-card-title="Circulation & Perfusion"]').locator("xpath=.//*[normalize-space(text())='Edema Severity']/ancestor::div[position()<=4][1]");
  await severityBlock.getByText("3+", { exact: true }).first().click();
  await page.waitForTimeout(400);
  const typeBlock = page.locator('[data-card-title="Circulation & Perfusion"]').locator("xpath=.//*[normalize-space(text())='Edema Type']/ancestor::div[position()<=4][1]");
  await typeBlock.getByText("Pitting", { exact: true }).first().click();
  await page.waitForTimeout(400);
  await page.screenshot({ path: "scripts/cardio-audit-output/edema/03-new-or-worsening-edema-full.png", fullPage: true });

  await save(page);
  let state = await apiFetchCardio(page);
  console.log("AFTER SAVE (New or Worsening):", JSON.stringify(state.edema), state.cardiovascularOverview);

  // Step 2: switch to "Existing Cardiovascular Findings Review"
  await page.getByText("Existing Cardiovascular Findings Review", { exact: false }).first().click();
  await page.waitForTimeout(900);
  await page.screenshot({ path: "scripts/cardio-audit-output/edema/04-existing-findings-review.png", fullPage: true });
  await save(page);
  state = await apiFetchCardio(page);
  console.log("AFTER SAVE (Existing Review):", JSON.stringify(state.edema), state.cardiovascularOverview);

  const edemaCardText = await page.locator('[data-card-title="Circulation & Perfusion"]').innerText().catch(() => "CARD NOT FOUND / HIDDEN");
  console.log("CIRCULATION & PERFUSION CARD TEXT (Existing Review):\n", edemaCardText);

  // Step 3: "No Current Cardiovascular Concern"
  await page.getByText("No Current Cardiovascular Concern", { exact: false }).first().click();
  await page.waitForTimeout(900);
  await page.screenshot({ path: "scripts/cardio-audit-output/edema/05-no-current-concern.png", fullPage: true });

  // Step 4: "Unable to Assess"
  await page.getByText("Unable to Assess", { exact: true }).first().click();
  await page.waitForTimeout(900);
  await page.getByText("Patient unresponsive", { exact: true }).first().click();
  await page.waitForTimeout(900);
  await page.screenshot({ path: "scripts/cardio-audit-output/edema/06-unable-to-assess.png", fullPage: true });
  await save(page);

  state = await apiFetchCardio(page);
  console.log("FINAL STATE (should be baseline target before manual restore):", JSON.stringify(state, null, 2));

  await browser.close();
}
main().catch((e) => { console.error(e); process.exitCode = 1; });
