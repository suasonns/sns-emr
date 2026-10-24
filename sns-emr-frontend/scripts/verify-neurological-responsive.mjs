// Verification script for the "NEUROLOGICAL REDESIGN -- Infection Is The
// Layout Reference Standard" product-owner directive: opens the real app
// via Playwright at ultrawide/desktop/laptop/tablet(iPad)/mobile
// viewports, screenshots the Neurological panel, and measures the live
// `.rnica-bodysystem-grid-columns` column count at each width so the
// "compatible with all types of screen" requirement can be checked
// against real rendered DOM, not just source/CSS inspection. Mirrors
// scripts/verify-respiratory-layout-compaction.mjs exactly (same
// viewport matrix, same container-based column-count assertion).
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:5173";
// Never hardcode a chart/patient identifier in a committed script --
// pass the seeded fixture patient's chart ID via the environment.
const PATIENT_ID = process.env.E2E_TEST_PATIENT_ID;
if (!PATIENT_ID) {
  throw new Error("E2E_TEST_PATIENT_ID is not set. Set it to the seeded fixture patient chart ID before running.");
}

function loadCredentials() {
  const envPath = path.resolve(process.cwd(), "../backend/.env");
  const raw = fs.readFileSync(envPath, "utf8");
  const values = {};
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    values[trimmed.slice(0, eq).trim()] = trimmed.slice(eq + 1).trim();
  }
  if (!values.DEV_RN_EMAIL || !values.DEV_RN_PASSWORD) {
    throw new Error("backend/.env missing DEV_RN_EMAIL/DEV_RN_PASSWORD");
  }
  return { email: values.DEV_RN_EMAIL, password: values.DEV_RN_PASSWORD };
}
const { email: EMAIL, password: PASSWORD } = loadCredentials();

const VIEWPORTS = [
  { name: "ultrawide", width: 3440, height: 1440 },
  { name: "desktop", width: 1920, height: 1080 },
  { name: "laptop", width: 1366, height: 768 },
  { name: "ipad", width: 820, height: 1180 },
  { name: "mobile", width: 390, height: 844 },
];

const outDir = "scripts/neurological-audit-output";
fs.mkdirSync(outDir, { recursive: true });

async function login(page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  const inputs = page.locator("input");
  await inputs.nth(0).fill(EMAIL);
  await inputs.nth(1).fill(PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(1000);
}

async function openNeurological(page) {
  await page.goto(`${BASE_URL}/chart/${PATIENT_ID}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);

  const navDrawerBtn = page.getByRole("button", { name: /Patient chart navigation/i });
  if (await navDrawerBtn.isVisible().catch(() => false)) {
    await navDrawerBtn.click();
    await page.waitForTimeout(500);
  }

  await page.getByText("Nursing Assessment", { exact: true }).first().click();
  await page.waitForTimeout(1200);

  if (await navDrawerBtn.isVisible().catch(() => false)) {
    await page.keyboard.press("Escape").catch(() => {});
    await page.waitForTimeout(400);
  }
  const clicked = await page.evaluate(() => {
    const spans = Array.from(document.querySelectorAll("span, button, a"));
    const match = spans.find((el) => el.textContent.trim() === "Body Systems");
    if (!match) return false;
    const clickable = match.closest("button, a") || match;
    clickable.click();
    return true;
  });
  if (!clicked) throw new Error("Body Systems nav element not found in DOM");
  await page.waitForTimeout(1200);

  const target = await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll(".rnica-bodysystems__trigger-label"));
    const match = els.find((el) => el.textContent.trim().toLowerCase().endsWith("neurological"));
    if (!match) return null;
    const r = match.getBoundingClientRect();
    return { x: r.x, y: r.y, w: r.width, h: r.height };
  });
  if (!target) throw new Error("Neurological accordion trigger not found");
  // Some already-persisted draft states leave this section pre-expanded
  // (matches the Nutrition/GI audit scripts' same safeguard) -- a blind
  // click would then toggle it CLOSED instead of opening it, which is
  // exactly why ultrawide/desktop/ipad runs intermittently timed out
  // waiting for the now-collapsed panel. Only click if it is not already
  // visible.
  const alreadyOpen = await page.locator('[data-testid="neurological-panel"]').isVisible().catch(() => false);
  if (!alreadyOpen) {
    await page.mouse.click(target.x + target.w / 2, target.y + target.h / 2);
  }
  await page.locator('[data-testid="neurological-panel"]').waitFor({ state: "visible", timeout: 20_000 });
}

async function measure(page) {
  return page.evaluate(() => {
    const panel = document.querySelector('[data-testid="neurological-panel"]');
    if (!panel) return null;
    const grid = panel.querySelector('[data-testid="neurological-panel-assessment-grid"]');
    // `data-card-title` is the real card-title hook (RNICA.jsx ~line
    // 15596) -- NOT a heading element, and its host div's textContent
    // includes every nested field/pill label too, so match on the
    // attribute value itself rather than textContent equality.
    const behavioralCard = panel.querySelector('[data-card-title="Behavioral Symptoms"]');
    const columns = grid ? grid.querySelectorAll(".rnica-bodysystem-grid-column") : [];
    // PRODUCT OWNER REVIEW (2026-10-24) "Organize, Don't Hide" -- neither
    // Psychiatric History nor Sleep Assessment/Responsiveness/
    // Neurological Status Change are collapsed by default anymore; all
    // render fully expanded without any toggle click required.
    const psychCard = panel.querySelector('[data-card-title="Psychiatric History"]');
    const psychFields = psychCard ? psychCard.querySelector(".rnica-bodysystem-workspace__fields") : null;
    // PRODUCT OWNER REVIEW (2026-10-24) "Sleep Assessment Is Not
    // Clinically Aligned With Responsiveness / Status Change" -- the
    // former single "Sleep / Responsiveness" card is split into three
    // standalone, always-visible, full-width sections rendered outside
    // the Assessment Grid: Sleep Assessment (own 3-column sub-grid),
    // Responsiveness, and Neurological Status Change.
    const sleepRow = panel.querySelector('[data-testid="neurological-panel-sleep-assessment-fullwidth"]');
    const sleepCard = sleepRow ? sleepRow.querySelector('[data-card-title="Sleep Assessment"]') : null;
    const sleepFields = sleepCard ? sleepCard.querySelector(".rnica-bodysystem-workspace__fields") : null;
    const sleepInGrid = grid ? !!grid.querySelector('[data-card-title="Sleep Assessment"]') : false;
    const responsivenessRow = panel.querySelector('[data-testid="neurological-panel-responsiveness-fullwidth"]');
    const responsivenessCard = responsivenessRow ? responsivenessRow.querySelector('[data-card-title="Responsiveness"]') : null;
    const statusChangeRow = panel.querySelector('[data-testid="neurological-panel-status-change-fullwidth"]');
    const statusChangeCard = statusChangeRow ? statusChangeRow.querySelector('[data-card-title="Neurological Status Change"]') : null;
    const overallChangeControl = statusChangeRow ? statusChangeRow.querySelector(".rnica-bodysystem-shell__change-since-prior") : null;
    return {
      panelWidth: panel.getBoundingClientRect().width,
      gridFound: !!grid,
      gridTemplateColumns: grid ? getComputedStyle(grid).gridTemplateColumns : null,
      gridColumnCount: grid ? getComputedStyle(grid).gridTemplateColumns.split(" ").filter(Boolean).length : null,
      // PRODUCT OWNER CORRECTION (2026-10-21) Section 9 -- the pooled
      // full-width collapsible row is retired; secondary cards are now
      // balanced directly inside columns 2/3, so column heights (not a
      // separate row) are the relevant "no wasted space" signal.
      columnHeights: Array.from(columns).map((c) => Math.round(c.getBoundingClientRect().height)),
      behavioralSymptomsVisible: !!behavioralCard,
      panelOverflowsViewport: panel.getBoundingClientRect().right > window.innerWidth + 1,
      psychiatricHistoryInColumn3: grid ? !!grid.querySelector('[data-card-title="Psychiatric History"]') : false,
      psychiatricHistoryExpanded: !!psychFields,
      sleepAssessmentStandalone: !!sleepRow && !sleepInGrid,
      sleepFieldsGridTemplateColumns: sleepFields ? getComputedStyle(sleepFields).gridTemplateColumns : null,
      sleepFieldsGridColumnCount: sleepFields
        ? getComputedStyle(sleepFields).gridTemplateColumns.split(" ").filter(Boolean).length
        : null,
      sleepCardOverflowsViewport: sleepCard ? sleepCard.getBoundingClientRect().right > window.innerWidth + 1 : null,
      responsivenessStandalone: !!responsivenessCard,
      statusChangeCardPresent: !!statusChangeCard,
      overallChangeControlGroupedWithStatusChange: !!overallChangeControl,
    };
  });
}

(async () => {
  const browser = await chromium.launch();
  const results = [];
  for (const vp of VIEWPORTS) {
    let lastErr = null;
    let recorded = false;
    // Two attempts per viewport: the first-attempt "Body Systems"/accordion
    // click is occasionally lost to a UI race (drawer still animating,
    // or the click landing before React finishes a re-render) -- a
    // fresh context + retry resolves it without masking a real failure
    // (the error is still recorded if both attempts fail).
    for (let attempt = 1; attempt <= 2 && !recorded; attempt += 1) {
      const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
      const page = await context.newPage();
      try {
        await login(page);
        await openNeurological(page);
        await page.waitForTimeout(500);
        const metrics = await measure(page);
        await page
          .locator('[data-testid="neurological-panel"]')
          .screenshot({ path: `${outDir}/neurological-${vp.name}.png` });
        results.push({ viewport: vp.name, width: vp.width, height: vp.height, attempt, ...metrics });
        recorded = true;
      } catch (err) {
        lastErr = err;
        await page.screenshot({ path: `${outDir}/debug-${vp.name}-attempt${attempt}.png`, fullPage: true }).catch(() => {});
      } finally {
        await context.close();
      }
    }
    if (!recorded) {
      results.push({
        viewport: vp.name,
        width: vp.width,
        height: vp.height,
        error: String(lastErr?.message || lastErr),
      });
    }
  }
  await browser.close();
  fs.writeFileSync(`${outDir}/metrics.json`, JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results, null, 2));
})();
