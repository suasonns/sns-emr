// HOPE-E2E-AUTH-001: real-login Playwright "setup" project. Runs once
// before the dependent test projects, drives the actual LoginPage UI
// (not a localStorage injection shortcut) through the real
// POST /auth/login endpoint, then persists the resulting session as a
// Playwright storageState file that other specs reuse via
// `use: { storageState: RN_STORAGE_STATE_PATH }` in playwright.config.ts.
//
// Exercising the real login form here is deliberate: it is also the
// first, cheapest regression check that login itself still works, and
// it proves the token this suite exercises other screens with came from
// the real backend-issued auth flow, not a shortcut.
import { test as setup, expect } from "@playwright/test";
import { loadRnTestCredentials } from "./support/testEnv";
import { RN_STORAGE_STATE_PATH } from "./support/storageStatePath";

setup("authenticate as the dev RN user", async ({ page }) => {
  const { email, password } = loadRnTestCredentials();

  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: /sign in/i }).click();

  // A tenant-scoped RN account lands on /portal (see
  // src/utils/authorization.ts getDefaultRoute). Waiting for this
  // navigation is also the assertion that login succeeded -- a failed
  // login leaves the user on /login with an error Alert instead.
  await expect(page).toHaveURL(/\/portal$/, { timeout: 15_000 });

  await page.context().storageState({ path: RN_STORAGE_STATE_PATH });
});
