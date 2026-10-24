const { chromium } = require('playwright');
const path = require('path');

// Writes only to a gitignored local temp directory -- never a hardcoded
// machine/session path. Patient and credentials come from the
// environment; never hardcode either in a committed script.
const OUT_DIR = path.join('scripts', 'tmp-output', 'body-system-compare');
const PATIENT_ID = process.env.E2E_TEST_PATIENT_ID;
const EMAIL = process.env.DEV_LOGIN_EMAIL;
const PASSWORD = process.env.DEV_LOGIN_PASSWORD;
if (!PATIENT_ID || !EMAIL || !PASSWORD) {
  console.error('Missing required env vars: E2E_TEST_PATIENT_ID, DEV_LOGIN_EMAIL, DEV_LOGIN_PASSWORD');
  process.exit(1);
}

(async () => {
  const fs = require('fs');
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 3440, height: 1440 } });
  const page = await context.newPage();
  const consoleMsgs = [];
  page.on('console', (msg) => consoleMsgs.push(`[${msg.type()}] ${msg.text()}`));
  page.on('pageerror', (err) => consoleMsgs.push(`[pageerror] ${err.message}`));

  await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(EMAIL);
  await inputs.nth(1).fill(PASSWORD);
  await page.getByRole('button', { name: /sign in/i }).click();
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);

  await page.goto(`http://localhost:5173/chart/${PATIENT_ID}`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);

  // Open Nursing Assessment in left nav
  const navLink = page.getByText('Nursing Assessment', { exact: true }).first();
  await navLink.click();
  await page.waitForTimeout(1500);

  // Within the RNICA workflow steps list, click "Body Systems"
  const bodySystemsStep = page.getByText('Body Systems', { exact: true }).first();
  await bodySystemsStep.click();
  await page.waitForTimeout(1500);

  // Collapse all first for a known baseline state
  const collapseAllBtn = page.getByText('Collapse all', { exact: true }).first();
  await collapseAllBtn.click().catch(() => {});
  await page.waitForTimeout(800);

  // Click accordion trigger-label elements by text suffix match (label text is "<icon> <SystemName>")
  const systems = ['Neurological', 'Respiratory', 'Cardiovascular', 'Infection'];
  for (const system of systems) {
    const target = await page.evaluate((name) => {
      const els = Array.from(document.querySelectorAll('.rnica-bodysystems__trigger-label'));
      const match = els.find(el => el.textContent.trim().toLowerCase().endsWith(name.toLowerCase()));
      if (!match) return null;
      const r = match.getBoundingClientRect();
      return { x: r.x, y: r.y, w: r.width, h: r.height };
    }, system);
    if (!target) {
      console.log(`No trigger found for ${system}`);
      continue;
    }
    await page.mouse.click(target.x + target.w / 2, target.y + target.h / 2);
    await page.waitForTimeout(1000);
    const shotPath = path.join(OUT_DIR, `${system.toLowerCase()}.png`);
    await page.screenshot({ path: shotPath, fullPage: true });
    console.log(`Saved ${shotPath}`);
    // Collapse it again before moving to next system
    await page.mouse.click(target.x + target.w / 2, target.y + target.h / 2);
    await page.waitForTimeout(500);
  }

  await browser.close();
  console.log('--- Console messages ---');
  console.log(consoleMsgs.filter(m => /error|warn/i.test(m)).join('\n'));
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
