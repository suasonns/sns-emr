const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const raw = fs.readFileSync('../backend/.env', 'utf8');
  const env = {};
  raw.split(/\r?\n/).forEach((l) => {
    const t = l.trim();
    if (!t || t.startsWith('#')) return;
    const i = t.indexOf('=');
    if (i === -1) return;
    env[t.slice(0, i).trim()] = t.slice(i + 1).trim();
  });
  const patientId = process.env.E2E_TEST_PATIENT_ID;
  if (!patientId) {
    console.error('Missing required env var: E2E_TEST_PATIENT_ID');
    process.exit(1);
  }
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();
  await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle' });
  const inputs = page.locator('input');
  await inputs.nth(0).fill(env.DEV_RN_EMAIL);
  await inputs.nth(1).fill(env.DEV_RN_PASSWORD);
  await page.getByRole('button', { name: /sign in/i }).click();
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);
  await page.goto(`http://localhost:5173/chart/${patientId}`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  await page.getByText('Nursing Assessment', { exact: true }).first().click();
  await page.waitForTimeout(1200);
  await page.evaluate(() => {
    const spans = Array.from(document.querySelectorAll('span, button, a'));
    const match = spans.find((el) => el.textContent.trim() === 'Body Systems');
    match.closest('button, a').click();
  });
  await page.waitForTimeout(1200);
  const info = await page.evaluate(() => {
    const col = document.querySelector('[data-testid="respiratory-oxygen-column"]');
    const freq = document.querySelector('[data-testid="respiratory-field-respiratory_oxygen_frequency"]');
    const hrs = document.querySelector('[data-testid="respiratory-field-respiratory_oxygen_hours_per_day"]');
    const spo2cond = document.querySelector('[data-testid="respiratory-field-respiratory_spo2_measurement_condition"]');
    const spo2val = document.querySelector('[data-testid="respiratory-field-respiratory_spo2_value"]');
    return {
      colWidth: col ? col.getBoundingClientRect().width : null,
      freqWidth: freq ? freq.getBoundingClientRect().width : null,
      hrsWidth: hrs ? hrs.getBoundingClientRect().width : null,
      spo2condWidth: spo2cond ? spo2cond.getBoundingClientRect().width : null,
      spo2valWidth: spo2val ? spo2val.getBoundingClientRect().width : null,
    };
  });
  console.log(JSON.stringify(info, null, 2));
  await browser.close();
})();
