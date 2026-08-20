import { test, expect } from '@playwright/test';

test('capture browser errors and failed fetches', async ({ page }) => {
  const consoleMessages = [];
  const pageErrors = [];
  const failedRequests = [];

  page.on('console', msg => consoleMessages.push({ type: msg.type(), text: msg.text() }));
  page.on('pageerror', err => pageErrors.push(err.message));
  page.on('requestfailed', req => failedRequests.push({ url: req.url(), failure: req.failure()?.errorText || 'unknown' }));

  await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(5000);

  console.log('CONSOLE', JSON.stringify(consoleMessages.slice(-20), null, 2));
  console.log('PAGEERR', JSON.stringify(pageErrors.slice(-20), null, 2));
  console.log('FAILED_REQ', JSON.stringify(failedRequests.slice(-20), null, 2));

  await page.locator('input[type="email"]').fill('rsuason@loveandfaithhospice.com');
  await page.locator('input[type="password"]').fill('LoveFaithHospice2026!');
  await page.getByRole('button', { name: /sign in|login/i }).click();
  await page.waitForTimeout(5000);

  console.log('AFTER_LOGIN_PAGEERR', JSON.stringify(pageErrors.slice(-20), null, 2));
  console.log('AFTER_LOGIN_FAILED_REQ', JSON.stringify(failedRequests.slice(-20), null, 2));

  await expect(page).toHaveURL(/localhost:5173/);
});
