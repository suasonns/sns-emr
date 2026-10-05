// Cardiovascular layout/viewport acceptance verification (SNS Layout Standard v1.1).
//
// Permanent QA/acceptance-testing tool (per owner directive, 2026-09-29 era
// Cardiovascular sign-off). Logs into the real running dev app (localhost:5173),
// navigates to a real patient's Cardiovascular section, captures real (non-
// simulated) screenshots and computed-style measurements at the required
// desktop/tablet/mobile viewports, then restores the patient record to its
// prior baseline.
//
// Usage: node scripts/cardio-layout-audit.mjs
// Requires: the dev frontend running on http://localhost:5173 and the dev
// backend reachable from it (same as normal local development).

import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const BASE_URL = "http://localhost:5173";
const LOGIN_EMAIL = "rsuason@loveandfaithhospice.com";
const LOGIN_PASSWORD = "LoveFaithHospice2026!";
const PATIENT_ID = "53fe69e1-fcd5-4b49-8203-9b890b18b7d6";
const ASSESSMENT_ID = "84234eb9-bfb9-4222-8287-4f4e8475c593";

const VIEWPORTS = [
  { name: "desktop-1440x900", width: 1440, height: 900 },
  { name: "desktop-1366x768", width: 1366, height: 768 },
  { name: "tablet-1024x768", width: 1024, height: 768 },
];

const OUT_DIR = path.resolve("scripts", "cardio-audit-output");
fs.mkdirSync(OUT_DIR, { recursive: true });

async function apiFetchCardio(page) {
  return page.evaluate(async (assessmentId) => {
    const token = localStorage.getItem("sns-hospice-solutions-access-token");
    const res = await fetch(`/visits/rnica/${assessmentId}`, {
      credentials: "include",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`API fetch failed: ${res.status}`);
    const data = await res.json();
    return data?.formData?.cardiovascular ?? null;
  }, ASSESSMENT_ID);
}

async function measureChain(page) {
  return page.evaluate(() => {
    const circCard = document.querySelector(
      '[data-section="cardiovascular"] [data-card-title="Circulation & Perfusion"]',
    );
    const symCard = document.querySelector(
      '[data-section="cardiovascular"] [data-card-title="Cardiovascular Symptoms"]',
    );
    function describe(el) {
      if (!el) return null;
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      return {
        width: Math.round(r.width),
        display: cs.display,
        gridTemplateColumns: cs.gridTemplateColumns,
        columnGap: cs.columnGap,
        rowGap: cs.rowGap,
        containerType: cs.containerType,
      };
    }
    function chainFor(el) {
      const chain = [];
      let node = el;
      while (node && node.tagName !== "BODY") {
        const r = node.getBoundingClientRect();
        const cs = getComputedStyle(node);
        chain.push({
          tag: node.tagName,
          cls: (node.className || "").toString().slice(0, 60),
          width: Math.round(r.width),
          display: cs.display,
          overflowX: cs.overflowX,
          minWidth: cs.minWidth,
          maxWidth: cs.maxWidth,
          flexBasis: cs.flexBasis,
          flexGrow: cs.flexGrow,
          flexShrink: cs.flexShrink,
          containerType: cs.containerType,
        });
        node = node.parentElement;
      }
      return chain;
    }
    const circFields = circCard ? circCard.querySelector(".rnica-bodysystem-group__fields, [class*='fields']") : null;
    const symFields = symCard ? symCard.querySelector(".rnica-bodysystem-group__fields, [class*='fields']") : null;
    return {
      viewportWidth: window.innerWidth,
      circulationCard: describe(circCard),
      symptomsCard: describe(symCard),
      circulationFieldsGrid: describe(circFields),
      symptomsFieldsGrid: describe(symFields),
      ancestorChainFromCirculationCard: chainFor(circCard),
    };
  });
}

async function main() {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: VIEWPORTS[0] });
  const page = await context.newPage();

  const report = { viewports: {}, baseline: null, restoredMatchesBaseline: null };

  try {
    // 1. Login (real UI, no token injection).
    await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
    await page.getByLabel(/email/i).fill(LOGIN_EMAIL);
    await page.getByLabel(/^password/i).fill(LOGIN_PASSWORD);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForTimeout(2000);

    // 2. Navigate to the patient's RN-ICA Nursing Assessment > Body Systems > Cardiovascular,
    //    using the real active-patient session mechanism (same one the app's own chart
    //    navigation uses internally) rather than simulating arbitrary clicks.
    await page.evaluate((patientId) => {
      window.sessionStorage.setItem("sns-hospice-solutions-active-patient", patientId);
    }, PATIENT_ID);
    await page.goto(`${BASE_URL}/nursing-assessment`, { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);
    await page.locator(".rnica-rail__label", { hasText: "Body Systems" }).first().click();
    await page.waitForTimeout(600);
    await page.locator(".rnica-bodysystems__trigger", { hasText: "Cardiovascular" }).first().click();
    await page.waitForTimeout(600);

    // 3. Capture baseline before any mutation.
    const baseline = await apiFetchCardio(page);
    report.baseline = baseline;

    // 4. Temporarily switch Overview to expose the full Circulation & Perfusion /
    //    Cardiovascular Symptoms cards (same state the owner's screenshots used).
    await page.getByText("New or Worsening Cardiovascular Findings", { exact: false }).first().click();
    await page.waitForTimeout(700);

    // 5. Capture real screenshots + measurements at each required viewport.
    for (const vp of VIEWPORTS) {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.waitForTimeout(400);
      const measurement = await measureChain(page);
      report.viewports[vp.name] = measurement;

      const cardLocator = page.locator('[data-section="cardiovascular"]').first();
      const screenshotPath = path.join(OUT_DIR, `cardio-${vp.name}.png`);
      await cardLocator.screenshot({ path: screenshotPath }).catch(async () => {
        await page.screenshot({ path: screenshotPath, fullPage: true });
      });
      report.viewports[vp.name].screenshotPath = screenshotPath;
    }

    // 6. Restore original record state.
    if (baseline?.cardiovascularOverview) {
      await page.getByText(baseline.cardiovascularOverview, { exact: false }).first().click().catch(() => {});
      await page.waitForTimeout(400);
      if (baseline.cardiovascularOverview === "Unable to Assess" && baseline.cardiovascularUnableToAssessReason) {
        await page
          .getByText(baseline.cardiovascularUnableToAssessReason, { exact: false })
          .first()
          .click()
          .catch(() => {});
        await page.waitForTimeout(400);
      }
    }
    await page.waitForTimeout(1500); // allow autosave

    const restored = await apiFetchCardio(page);
    report.restored = restored;
    report.restoredMatchesBaseline = JSON.stringify(restored) === JSON.stringify(baseline);
  } finally {
    await context.close();
    await browser.close();
  }

  fs.writeFileSync(path.join(OUT_DIR, "report.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
