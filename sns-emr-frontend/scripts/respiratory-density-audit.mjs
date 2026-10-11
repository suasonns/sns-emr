// Respiratory layout/viewport density audit (SNS Layout Standard v1.1).
//
// Analysis-only QA tool. Follows the exact same methodology as
// scripts/gi-density-audit.mjs (measurement only, no code change): logs
// into the real running dev app, navigates to a real patient's Respiratory
// section via the actual production route (/chart/:patientId -> Nursing
// Assessment -> Body Systems accordion -> Respiratory), and measures the
// real rendered geometry of every nested layout region (outer command
// rail, Body Systems aggregate findings rail, and RespiratoryPanel's own
// sidebar) to determine where unused/wasted horizontal space actually
// originates.
//
// Usage: node scripts/respiratory-density-audit.mjs
// Requires: the dev frontend running on http://localhost:5173 and the dev
// backend reachable from it (same as normal local development).

import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const BASE_URL = "http://localhost:5173";
const LOGIN_EMAIL = "rsuason@loveandfaithhospice.com";
const LOGIN_PASSWORD = "LoveFaithHospice2026!";
const PATIENT_ID = "53fe69e1-fcd5-4b49-8203-9b890b18b7d6";

const VIEWPORTS = [
  { name: "desktop-1920x1080", width: 1920, height: 1080 },
  { name: "desktop-1440x900", width: 1440, height: 900 },
  { name: "desktop-1366x768", width: 1366, height: 768 },
];

const OUT_DIR = path.resolve("scripts", "respiratory-audit-output");
fs.mkdirSync(OUT_DIR, { recursive: true });

function rect(el) {
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return { x: Math.round(r.x), width: Math.round(r.width), height: Math.round(r.height) };
}

async function measure(page) {
  return page.evaluate(() => {
    function rectOf(sel) {
      const el = document.querySelector(sel);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { x: Math.round(r.x), right: Math.round(r.right), width: Math.round(r.width), height: Math.round(r.height) };
    }
    const viewportWidth = window.innerWidth;
    const layout = rectOf(".rnica-command-layout");
    const detail = rectOf(".rnica-command-detail");
    const commandRail = rectOf(".rnica-command-rail");
    const bodysystems = rectOf(".rnica-bodysystems");
    const bsMain = rectOf(".rnica-bodysystems__main");
    const bsRail = rectOf(".rnica-bodysystems__rail");
    const respPanel = rectOf('[data-testid="respiratory-panel"]');
    const respMain = rectOf('[data-testid="respiratory-main-column"]');
    const respSidebar = rectOf('[data-testid="respiratory-sidebar-column"]');
    const pageScrollHeight = document.scrollingElement ? document.scrollingElement.scrollHeight : null;

    // Unused = viewport width minus the rightmost edge of the last
    // meaningful content region, plus anything unused between regions.
    const rightmostContentEdge = Math.max(
      commandRail?.right || 0,
      bodysystems?.right || 0,
      respPanel?.right || 0,
      detail?.right || 0,
    );

    return {
      viewportWidth,
      layout,
      detail,
      commandRail,
      bodysystems,
      bsMain,
      bsRail,
      respPanel,
      respMain,
      respSidebar,
      pageScrollHeight,
      rightmostContentEdge,
      unusedRightOfContentPx: Math.max(0, viewportWidth - rightmostContentEdge),
    };
  });
}

async function main() {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: VIEWPORTS[1] });
  const page = await context.newPage();

  const report = { route: null, domTreeConfirmed: null, viewports: {} };

  try {
    await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
    await page.getByLabel(/email/i).fill(LOGIN_EMAIL);
    await page.getByLabel(/^password/i).fill(LOGIN_PASSWORD);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/chart/${PATIENT_ID}`, { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);

    // Open chart navigation and click Nursing Assessment.
    const navBtn = page.getByRole("button", { name: "Patient chart navigation" });
    if (await navBtn.isVisible().catch(() => false)) {
      await navBtn.click();
      await page.waitForTimeout(300);
    }
    await page.getByText("Nursing Assessment", { exact: true }).first().click();
    await page.waitForTimeout(1200);
    report.route = page.url();

    // Click into the Body Systems screen/rail, then open Respiratory.
    const bodySystemsLabel = page.getByRole("button", { name: "Body Systems" }).first();
    await bodySystemsLabel.click({ timeout: 10000 });
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(OUT_DIR, "debug-after-bodysystems-click.png") });

    const respTrigger = page.getByRole("button", { name: /Respiratory/ }).first();
    const expandedAttr = await respTrigger.getAttribute("aria-expanded").catch(() => null);
    if (expandedAttr !== "true") {
      await respTrigger.click({ timeout: 10000 });
      await page.waitForTimeout(1200);
    }
    await page.waitForSelector('[data-testid="respiratory-panel"]', { timeout: 10000 }).catch(() => {});
    await page.screenshot({ path: path.join(OUT_DIR, "debug-after-respiratory-click.png") });

    report.domTreeConfirmed = await page.evaluate(() => ({
      hasRespiratoryPanelTestId: !!document.querySelector('[data-testid="respiratory-panel"]'),
      hasBodysystemsAggregateRail: !!document.querySelector(".rnica-bodysystems__rail"),
      hasOuterCommandRail: !!document.querySelector(".rnica-command-rail"),
    }));

    for (const vp of VIEWPORTS) {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.waitForTimeout(400);
      report.viewports[vp.name] = await measure(page);
      await page.screenshot({ path: path.join(OUT_DIR, `respiratory-${vp.name}.png`), fullPage: false });
    }
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
