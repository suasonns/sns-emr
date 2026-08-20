# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: playwright-fetch-check.spec.js >> capture browser errors and failed fetches
- Location: playwright-fetch-check.spec.js:3:1

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('input[type="email"]')

```

# Page snapshot

```yaml
- generic [ref=e5]:
  - img "SNS Hospice Solutions" [ref=e6]
  - generic [ref=e7]:
    - generic [ref=e8]:
      - text: Secure clinical access
      - heading "Welcome back" [level=5] [ref=e9]
    - generic [ref=e10]:
      - generic [ref=e11]:
        - generic: Email
        - generic [ref=e12]:
          - textbox "Email" [ref=e13]
          - group:
            - generic: Email
      - generic [ref=e14]:
        - generic: Password
        - generic [ref=e15]:
          - textbox "Password" [ref=e16]
          - group:
            - generic: Password
      - button "Sign in" [disabled]
      - button "Forgot password?" [ref=e17] [cursor=pointer]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test('capture browser errors and failed fetches', async ({ page }) => {
  4  |   const consoleMessages = [];
  5  |   const pageErrors = [];
  6  |   const failedRequests = [];
  7  | 
  8  |   page.on('console', msg => consoleMessages.push({ type: msg.type(), text: msg.text() }));
  9  |   page.on('pageerror', err => pageErrors.push(err.message));
  10 |   page.on('requestfailed', req => failedRequests.push({ url: req.url(), failure: req.failure()?.errorText || 'unknown' }));
  11 | 
  12 |   await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded', timeout: 30000 });
  13 |   await page.waitForTimeout(5000);
  14 | 
  15 |   console.log('CONSOLE', JSON.stringify(consoleMessages.slice(-20), null, 2));
  16 |   console.log('PAGEERR', JSON.stringify(pageErrors.slice(-20), null, 2));
  17 |   console.log('FAILED_REQ', JSON.stringify(failedRequests.slice(-20), null, 2));
  18 | 
> 19 |   await page.locator('input[type="email"]').fill('rsuason@loveandfaithhospice.com');
     |                                             ^ Error: locator.fill: Test timeout of 30000ms exceeded.
  20 |   await page.locator('input[type="password"]').fill('LoveFaithHospice2026!');
  21 |   await page.getByRole('button', { name: /sign in|login/i }).click();
  22 |   await page.waitForTimeout(5000);
  23 | 
  24 |   console.log('AFTER_LOGIN_PAGEERR', JSON.stringify(pageErrors.slice(-20), null, 2));
  25 |   console.log('AFTER_LOGIN_FAILED_REQ', JSON.stringify(failedRequests.slice(-20), null, 2));
  26 | 
  27 |   await expect(page).toHaveURL(/localhost:5173/);
  28 | });
  29 | 
```