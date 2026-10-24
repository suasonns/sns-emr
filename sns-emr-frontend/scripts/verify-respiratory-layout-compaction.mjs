// Verification script for the "RESPIRATORY LAYOUT COMPACTION REVIEW"
// product-owner directive: opens the real app via Playwright at
// ultrawide/desktop/laptop/tablet(iPad)/mobile viewports, screenshots
// the Respiratory panel, and measures a whitespace ratio (empty vertical
// gap between top-level panel sections divided by total panel height)
// so the "reduce total height 20-30%, whitespace <= 14.1%" target can be
// checked against real rendered DOM, not just source inspection.
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

// Reuses the same gitignored backend/.env dev credentials as
// e2e/support/testEnv.ts (DEV_RN_EMAIL / DEV_RN_PASSWORD) -- no literal
// credential is hardcoded here.
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

const outDir = "scripts/respiratory-audit-output";
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

async function openRespiratory(page) {
  await page.goto(`${BASE_URL}/chart/${PATIENT_ID}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);

  // Narrow viewports (iPad/mobile) collapse the left nav behind a
  // "Patient chart navigation" drawer button instead of showing the
  // nav items inline.
  const navDrawerBtn = page.getByRole("button", { name: /Patient chart navigation/i });
  if (await navDrawerBtn.isVisible().catch(() => false)) {
    await navDrawerBtn.click();
    await page.waitForTimeout(500);
  }

  await page.getByText("Nursing Assessment", { exact: true }).first().click();
  await page.waitForTimeout(1200);

  // The drawer can remain open as an overlay after navigating on narrow
  // viewports -- close it explicitly (press Escape, a common drawer
  // dismissal) so it doesn't paint over the panel in screenshots/measurements.
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
    const match = els.find((el) => el.textContent.trim().toLowerCase().endsWith("respiratory"));
    if (!match) return null;
    const r = match.getBoundingClientRect();
    return { x: r.x, y: r.y, w: r.width, h: r.height };
  });
  if (!target) throw new Error("Respiratory accordion trigger not found");
  await page.mouse.click(target.x + target.w / 2, target.y + target.h / 2);
  await page.locator('[data-testid="respiratory-panel"]').waitFor({ state: "visible", timeout: 10_000 });
}

async function measure(page) {
  return page.evaluate(() => {
    const panel = document.querySelector('[data-testid="respiratory-panel"]');
    if (!panel) return null;
    const content = panel.closest(".rnica-bodysystem-workspace__content");
    const grid = panel.querySelector(".rnica-bodysystem-grid-columns");
    const drawerOverlay = Array.from(document.querySelectorAll("*")).find((el) =>
      el.textContent.trim() === "Patient chart navigation" && el.getBoundingClientRect().width > 0 &&
      el.closest("[role='dialog'], aside, nav, .drawer, [class*='drawer'], [class*='overlay']"),
    );
    const containerDebug = {
      contentWidth: content ? content.getBoundingClientRect().width : null,
      gridTemplateColumns: grid ? getComputedStyle(grid).gridTemplateColumns : null,
      gridColumnCount: grid ? getComputedStyle(grid).gridTemplateColumns.split(" ").length : null,
      drawerOpen: !!drawerOverlay,
    };
    const panelRect = panel.getBoundingClientRect();
    const sections = Array.from(panel.children).filter(
      (el) => el.getBoundingClientRect().height > 0,
    );
    let gapSum = 0;
    for (let i = 1; i < sections.length; i++) {
      const prev = sections[i - 1].getBoundingClientRect();
      const cur = sections[i].getBoundingClientRect();
      const gap = cur.top - prev.bottom;
      if (gap > 0) gapSum += gap;
    }
    const totalHeight = panelRect.height;
    return {
      totalHeight,
      sectionCount: sections.length,
      gapSum,
      whitespaceRatioPercent: totalHeight > 0 ? (gapSum / totalHeight) * 100 : 0,
      ...containerDebug,
    };
  });
}

(async () => {
  const browser = await chromium.launch();
  const results = [];
  for (const vp of VIEWPORTS) {
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
    const page = await context.newPage();
    try {
      await login(page);
      await openRespiratory(page);
      await page.waitForTimeout(500);
      const metrics = await measure(page);
      await page.locator('[data-testid="respiratory-panel"]').screenshot({ path: `${outDir}/respiratory-${vp.name}.png` });
      results.push({ viewport: vp.name, width: vp.width, height: vp.height, ...metrics });
    } catch (err) {
      await page.screenshot({ path: `${outDir}/debug-${vp.name}.png`, fullPage: true }).catch(() => {});
      results.push({ viewport: vp.name, width: vp.width, height: vp.height, error: String(err.message || err) });
    }
    await context.close();
  }
  await browser.close();
  fs.writeFileSync(`${outDir}/metrics.json`, JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results, null, 2));
})();
