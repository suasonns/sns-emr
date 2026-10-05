import { chromium } from "@playwright/test";
import fs from "node:fs";

const BASE_URL = "http://localhost:5173";
const LOGIN_EMAIL = "rsuason@loveandfaithhospice.com";
const LOGIN_PASSWORD = "LoveFaithHospice2026!";
const PATIENT_ID = "53fe69e1-fcd5-4b49-8203-9b890b18b7d6";
const ASSESSMENT_ID = "84234eb9-bfb9-4222-8287-4f4e8475c593";

const BASELINE_CARDIOVASCULAR = {
  cardiovascularOverview: "Unable to Assess",
  cardiovascularUnableToAssessReason: "Patient unresponsive",
  cardiovascularUnableToAssessOther: "",
  cardiovascularFindingsConfirmedThisVisit: false,
  pulseRhythm: "", pulseRate: "", pulseStrength: "", pulseSites: [], pulseQuality: "",
  skinColor: "", skinColorOther: "", heartSounds: "", heartSoundsOther: "",
  coolExtremities: false, varicoseVeins: false, stasisUlcer: false,
  jvd: "", peripheralCirculation: "", peripheralCirculationOther: "",
  edema: { present: "No", location: [], severity: "", pitting: "" },
  chestPain: { present: "", type: "", frequency: "" },
  bpStatus: "", bpSymptoms: [], orthostaticFinding: "", dizziness: "", fatigue: "", syncope: "",
  cardiacDyspnea: false, heartFailurePresent: false, heartFailureType: [],
  pacemaker: false, internalDefibrillator: false, centralVenousLine: false,
  clinicalStatusChange: "Initial Assessment", notes: "",
};

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

async function apiSaveCardio(page, cardiovascular) {
  return page.evaluate(async ({ assessmentId, cardiovascular }) => {
    const token = localStorage.getItem("sns-hospice-solutions-access-token");
    const getRes = await fetch(`/visits/rnica/${assessmentId}`, {
      credentials: "include",
      headers: { Authorization: `Bearer ${token}` },
    });
    const full = await getRes.json();
    const newFormData = { ...full.formData, cardiovascular };
    const putRes = await fetch(`/visits/rnica/${assessmentId}`, {
      method: "PUT",
      credentials: "include",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ formData: newFormData, fieldProvenance: full.fieldProvenance || [] }),
    });
    return { status: putRes.status, body: await putRes.json().catch(() => null) };
  }, { assessmentId: ASSESSMENT_ID, cardiovascular });
}

async function openCardio(page) {
  await page.evaluate((patientId) => {
    window.sessionStorage.setItem("sns-hospice-solutions-active-patient", patientId);
  }, PATIENT_ID);
  await page.goto(`${BASE_URL}/nursing-assessment`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  await page.locator(".rnica-rail__label", { hasText: "Body Systems" }).first().click();
  await page.waitForTimeout(700);
  await page.locator(".rnica-bodysystems__trigger", { hasText: "Cardiovascular" }).first().click();
  await page.waitForTimeout(700);
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

  const results = {};

  // ---- Path: New or Worsening Findings, Edema Present = Yes w/ full detail ----
  let r = await apiSaveCardio(page, {
    ...BASELINE_CARDIOVASCULAR,
    cardiovascularOverview: "New or Worsening Cardiovascular Findings",
    cardiovascularUnableToAssessReason: "",
    edema: { present: "Yes", location: ["Bilateral lower extremities"], severity: "3+", pitting: "Pitting" },
  });
  console.log("SAVE new-or-worsening:", r.status);
  await openCardio(page);
  await page.waitForTimeout(500);
  await page.screenshot({ path: "scripts/cardio-audit-output/edema/01-new-or-worsening.png", fullPage: true });
  let cardText = await page.locator('[data-card-title="Circulation & Perfusion"]').innerText().catch(() => "NOT FOUND");
  results.newOrWorsening = {
    locationVisible: /Bilateral lower extremities/.test(cardText),
    severityVisible: /\b3\+\b/.test(cardText),
    typeVisible: /\bPitting\b/.test(cardText),
  };
  console.log("New or Worsening visibility:", results.newOrWorsening);

  // ---- Path: Existing Cardiovascular Findings Review, same edema data already stored ----
  r = await apiSaveCardio(page, {
    ...BASELINE_CARDIOVASCULAR,
    cardiovascularOverview: "Existing Cardiovascular Findings Review",
    cardiovascularUnableToAssessReason: "",
    edema: { present: "Yes", location: ["Bilateral lower extremities"], severity: "3+", pitting: "Pitting" },
  });
  console.log("SAVE existing-review:", r.status);
  await openCardio(page);
  await page.waitForTimeout(500);
  await page.screenshot({ path: "scripts/cardio-audit-output/edema/02-existing-findings-review.png", fullPage: true });
  cardText = await page.locator('[data-card-title="Circulation & Perfusion"]').innerText().catch(() => "NOT FOUND / HIDDEN");
  console.log("CIRCULATION & PERFUSION CARD TEXT (Existing Review):\n", cardText);
  results.existingReview = {
    cardVisible: cardText !== "NOT FOUND / HIDDEN",
    edemaPresentVisible: /Edema Present/i.test(cardText) && /\bYes\b/.test(cardText),
    locationVisible: /Bilateral lower extremities/.test(cardText),
    severityVisible: /\b3\+\b/.test(cardText),
    typeVisible: /\bPitting\b/.test(cardText),
  };
  console.log("Existing Review visibility:", results.existingReview);

  // ---- Path: No Current Cardiovascular Concern (should hide, not delete) ----
  r = await apiSaveCardio(page, {
    ...BASELINE_CARDIOVASCULAR,
    cardiovascularOverview: "No Current Cardiovascular Concern",
    cardiovascularUnableToAssessReason: "",
    edema: { present: "Yes", location: ["Bilateral lower extremities"], severity: "3+", pitting: "Pitting" },
  });
  console.log("SAVE no-current-concern:", r.status);
  await openCardio(page);
  await page.waitForTimeout(500);
  await page.screenshot({ path: "scripts/cardio-audit-output/edema/03-no-current-concern.png", fullPage: true });
  cardText = await page.locator('[data-card-title="Circulation & Perfusion"]').innerText().catch(() => "NOT FOUND / HIDDEN");
  results.noCurrentConcern = { cardText };
  console.log("No Current Concern card text:", cardText);

  // ---- Path: Unable to Assess (should hide everything but Overview) ----
  r = await apiSaveCardio(page, {
    ...BASELINE_CARDIOVASCULAR,
    cardiovascularOverview: "Unable to Assess",
    cardiovascularUnableToAssessReason: "Patient unresponsive",
    edema: { present: "Yes", location: ["Bilateral lower extremities"], severity: "3+", pitting: "Pitting" },
  });
  console.log("SAVE unable-to-assess:", r.status);
  await openCardio(page);
  await page.waitForTimeout(500);
  await page.screenshot({ path: "scripts/cardio-audit-output/edema/04-unable-to-assess.png", fullPage: true });
  cardText = await page.locator('[data-card-title="Circulation & Perfusion"]').innerText().catch(() => "NOT FOUND / HIDDEN");
  results.unableToAssess = { cardText };
  console.log("Unable to Assess card text:", cardText);

  // ---- Restore true baseline ----
  r = await apiSaveCardio(page, BASELINE_CARDIOVASCULAR);
  console.log("RESTORE baseline:", r.status);
  const finalCheck = await apiFetchFull(page);
  console.log("FINAL cardiovascular state:", JSON.stringify(finalCheck.formData.cardiovascular.edema), finalCheck.formData.cardiovascular.cardiovascularOverview, finalCheck.formData.cardiovascular.cardiovascularUnableToAssessReason);

  fs.writeFileSync("scripts/cardio-audit-output/edema/results.json", JSON.stringify(results, null, 2));
  await browser.close();
}
main().catch((e) => { console.error(e); process.exitCode = 1; });
